"""Backup and restore utilities for the admin panel."""
from __future__ import annotations

import base64
import io
import json
import os
import shutil
import sqlite3
import tempfile
import zipfile
from datetime import date, datetime, time, timezone
from decimal import Decimal
from typing import Any, BinaryIO, Dict, List, Optional, Tuple

from flask import current_app
from werkzeug.utils import secure_filename

from app import db
from app.utils import path_utils

BACKUP_FORMAT_NAME = 'noteblog-backup'
BACKUP_FORMAT_VERSION = 2
DATA_FOLDER_NAME = 'data'
TABLE_FILE_SUFFIX = '.jsonl'
EXPORT_CHUNK_SIZE = 500
IMPORT_BATCH_SIZE = 500


class BackupError(RuntimeError):
    """Raised when backup or restore fails."""


def create_backup_archive(include_extensions: bool = False) -> Tuple[str, BinaryIO]:
    """Create a backup archive containing uploads, metadata, and database dumps."""
    upload_folder = current_app.config.get('UPLOAD_FOLDER')
    if not upload_folder:
        raise BackupError('UPLOAD_FOLDER 未配置，无法生成备份。')

    timestamp = datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')
    tmp_dir = tempfile.mkdtemp(prefix='noteblog-backup-')
    data_dir = os.path.join(tmp_dir, DATA_FOLDER_NAME)
    os.makedirs(data_dir, exist_ok=True)

    current_app.logger.info('开始生成备份，include_extensions=%s', include_extensions)

    try:
        manifest = _build_backup_manifest(upload_folder, include_extensions)
        table_summaries: List[Dict[str, Any]] = []
        for table in db.metadata.sorted_tables:
            summary = _dump_table_to_jsonl(table, data_dir)
            table_summaries.append(summary)
        manifest['database']['tables'] = table_summaries

        metadata_path = os.path.join(tmp_dir, 'metadata.json')
        with open(metadata_path, 'w', encoding='utf-8') as meta_fp:
            json.dump(manifest, meta_fp, ensure_ascii=False, indent=2)

        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', compression=zipfile.ZIP_DEFLATED, allowZip64=True) as zipf:
            zipf.write(metadata_path, arcname='metadata.json')
            _add_directory_to_zip(zipf, data_dir, DATA_FOLDER_NAME)
            _add_uploads_to_zip(zipf, upload_folder)

            if include_extensions:
                _add_extensions_to_zip(zipf)

        zip_buffer.seek(0)
        filename = f'noteblog-backup-{timestamp}.zip'
        current_app.logger.info('备份生成完成: %s', filename)
        return filename, zip_buffer
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


def restore_backup_from_zip(file_storage, restore_extensions: bool = False, overwrite_extensions: bool = False) -> None:
    """Restore uploads, database content, and optional extensions from a backup zip."""
    if not file_storage or not getattr(file_storage, 'filename', None):
        raise BackupError('请提供有效的备份文件。')

    upload_folder = current_app.config.get('UPLOAD_FOLDER')
    if not upload_folder:
        raise BackupError('UPLOAD_FOLDER 未配置，无法导入备份。')

    tmp_dir = tempfile.mkdtemp(prefix='noteblog-restore-')
    backup_filename = secure_filename(file_storage.filename)
    backup_path = os.path.join(tmp_dir, backup_filename or 'backup.zip')

    try:
        file_storage.save(backup_path)
        with zipfile.ZipFile(backup_path, 'r') as zipf:
            zipf.extractall(tmp_dir)

        manifest = _load_manifest(tmp_dir)
        data_dir = os.path.join(tmp_dir, DATA_FOLDER_NAME)
        sqlite_path = os.path.join(tmp_dir, 'database.sqlite')

        current_app.logger.info(
            '开始恢复备份，restore_extensions=%s, overwrite_extensions=%s',
            restore_extensions,
            overwrite_extensions,
        )

        # 1. 恢复插件和主题文件，保证数据库中的路径可以指向真实文件
        if restore_extensions:
            current_app.logger.info('正在恢复插件和主题文件...')
            _restore_extensions_from_zip(tmp_dir, overwrite_extensions)

        # 2. 恢复上传目录
        uploads_src = os.path.join(tmp_dir, 'uploads')
        if os.path.isdir(uploads_src):
            current_app.logger.info('正在恢复 uploads 目录...')
            _copy_upload_tree(uploads_src, upload_folder)

        # 3. 恢复数据库内容，优先使用新的 JSONL 格式，若不存在则回退到 legacy SQLite
        if manifest and os.path.isdir(data_dir):
            current_app.logger.info('检测到 JSONL 备份格式，正在恢复数据库...')
            _restore_database_from_jsonl(data_dir, manifest)
        elif os.path.exists(sqlite_path):
            current_app.logger.warning('检测到旧 SQLite 备份格式，正在使用兼容路径恢复...')
            _import_database_from_sqlite(sqlite_path)
        else:
            raise BackupError('备份文件缺少 data/ 或 database.sqlite，无法恢复数据库。')

        # 4. 修复路径
        current_app.logger.info('正在修复插件和主题路径...')
        _fix_restored_paths()

        # 5. 刷新运行时状态并应用
        current_app.logger.info('正在刷新运行时状态...')
        _refresh_runtime_state()
        _apply_restored_extensions()

        current_app.logger.info('备份恢复完成')
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


# ---------------------------------------------------------------------------
# Export helpers
# ---------------------------------------------------------------------------

def _build_backup_manifest(upload_folder: str, include_extensions: bool) -> Dict[str, Any]:
    """Return the base metadata structure for a backup archive."""
    return {
        'format': BACKUP_FORMAT_NAME,
        'version': BACKUP_FORMAT_VERSION,
        'generated_at': datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
        'app_version': current_app.config.get('APP_VERSION', 'unknown'),
        'upload_folder': upload_folder,
        'include_extensions': include_extensions,
        'database': {
            'dialect': db.engine.dialect.name,
            'tables': [],
        },
    }


def _dump_table_to_jsonl(table, data_dir: str) -> Dict[str, Any]:
    """Stream the given table into a JSONL file under the provided directory."""
    column_names = [col.name for col in table.columns]
    if not column_names:
        return {'name': table.name, 'columns': [], 'row_count': 0, 'filename': f'{table.name}{TABLE_FILE_SUFFIX}'}

    file_path = os.path.join(data_dir, f'{table.name}{TABLE_FILE_SUFFIX}')
    row_count = 0
    stmt = table.select().execution_options(stream_results=True)

    with db.engine.connect() as conn, open(file_path, 'w', encoding='utf-8') as dump_fp:
        result = conn.execute(stmt)
        while True:
            rows = result.fetchmany(EXPORT_CHUNK_SIZE)
            if not rows:
                break
            for row in rows:
                mapping = _row_to_mapping(row, column_names)
                record = {col: _serialize_value(mapping.get(col)) for col in column_names}
                dump_fp.write(json.dumps(record, ensure_ascii=False))
                dump_fp.write('\n')
                row_count += 1

    current_app.logger.debug('表 %s 导出 %s 行', table.name, row_count)
    return {
        'name': table.name,
        'columns': column_names,
        'row_count': row_count,
        'filename': f'{table.name}{TABLE_FILE_SUFFIX}',
    }


def _row_to_mapping(row: Any, column_names: List[str]) -> Dict[str, Any]:
    """Return a mapping keyed by column names for the given row."""
    mapping = getattr(row, '_mapping', None)
    if mapping is not None:
        return {col: mapping.get(col) for col in column_names}

    if isinstance(row, (list, tuple)):
        return {column_names[index]: value for index, value in enumerate(row)}

    return {col: getattr(row, col, None) for col in column_names}


def _serialize_value(value: Any) -> Any:
    """Convert Python values to JSON-serializable payloads."""
    if value is None:
        return None
    if isinstance(value, (bool, int, float, str)):
        return value
    if isinstance(value, (datetime, date, time)):
        return value.isoformat()
    if isinstance(value, bytes):
        return {
            '__type__': 'bytes',
            'data': base64.b64encode(value).decode('ascii'),
        }
    if isinstance(value, memoryview):
        return {
            '__type__': 'bytes',
            'data': base64.b64encode(value.tobytes()).decode('ascii'),
        }
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, (list, dict)):
        return value
    # Fallback to string representation
    return str(value)


def _add_directory_to_zip(zipf: zipfile.ZipFile, src_root: str, arc_root: str) -> None:
    """Add the contents of src_root to the archive under arc_root."""
    if not os.path.isdir(src_root):
        return

    for root, _, files in os.walk(src_root):
        for filename in files:
            abs_path = os.path.join(root, filename)
            rel_path = os.path.relpath(abs_path, src_root)
            arcname = os.path.join(arc_root, rel_path).replace('\\', '/')
            zipf.write(abs_path, arcname=arcname)


# ---------------------------------------------------------------------------
# Import helpers
# ---------------------------------------------------------------------------

def _load_manifest(tmp_dir: str) -> Optional[Dict[str, Any]]:
    """Load and validate metadata.json if it exists."""
    metadata_path = os.path.join(tmp_dir, 'metadata.json')
    if not os.path.exists(metadata_path):
        return None

    try:
        with open(metadata_path, 'r', encoding='utf-8') as meta_fp:
            manifest = json.load(meta_fp)
    except json.JSONDecodeError as exc:
        raise BackupError(f'metadata.json 解析失败: {exc}') from exc

    if manifest.get('format') != BACKUP_FORMAT_NAME:
        raise BackupError('备份文件格式不受支持。')

    version = manifest.get('version', 1)
    try:
        version_num = int(version)
    except (TypeError, ValueError):
        version_num = 1

    if version_num > BACKUP_FORMAT_VERSION:
        raise BackupError('备份文件版本过新，请升级应用后再尝试恢复。')

    return manifest


def _restore_database_from_jsonl(data_dir: str, manifest: Dict[str, Any]) -> None:
    """Restore the entire database from JSONL dumps."""
    db.create_all()

    dialect = db.engine.dialect.name
    disable_fk: Optional[str] = None
    enable_fk: Optional[str] = None
    if dialect == 'mysql':
        disable_fk = 'SET FOREIGN_KEY_CHECKS=0'
        enable_fk = 'SET FOREIGN_KEY_CHECKS=1'
    elif dialect == 'sqlite':
        disable_fk = 'PRAGMA foreign_keys = OFF'
        enable_fk = 'PRAGMA foreign_keys = ON'
    elif dialect == 'postgresql':
        pass

    row_meta = {
        item.get('name'): item.get('row_count')
        for item in manifest.get('database', {}).get('tables', [])
    }

    with db.engine.begin() as conn:
        if disable_fk:
            conn.exec_driver_sql(disable_fk)

        for table in reversed(db.metadata.sorted_tables):
            if dialect == 'postgresql':
                conn.exec_driver_sql(f'TRUNCATE TABLE "{table.name}" CASCADE')
            else:
                try:
                    conn.execute(table.delete())
                except Exception:
                    pass

        for table in db.metadata.sorted_tables:
            dump_path = os.path.join(data_dir, f'{table.name}{TABLE_FILE_SUFFIX}')
            if not os.path.exists(dump_path):
                continue

            inserted = 0
            batch: List[Dict[str, Any]] = []
            for payload in _iter_jsonl_rows(dump_path):
                row: Dict[str, Any] = {}
                for column in table.columns:
                    row[column.name] = _deserialize_value(payload.get(column.name), column)
                batch.append(row)
                if len(batch) >= IMPORT_BATCH_SIZE:
                    conn.execute(table.insert(), batch)
                    inserted += len(batch)
                    batch.clear()
            if batch:
                conn.execute(table.insert(), batch)
                inserted += len(batch)

            current_app.logger.info(
                '表 %s 已恢复 %s 行 (备份记录: %s)',
                table.name,
                inserted,
                row_meta.get(table.name, '未知'),
            )

        if enable_fk:
            conn.exec_driver_sql(enable_fk)

    db.session.remove()


def _iter_jsonl_rows(file_path: str):
    """Yield dictionaries from a JSONL file, raising BackupError on parse issues."""
    with open(file_path, 'r', encoding='utf-8') as dump_fp:
        for line_no, line in enumerate(dump_fp, start=1):
            stripped = line.strip()
            if not stripped:
                continue
            try:
                yield json.loads(stripped)
            except json.JSONDecodeError as exc:
                raise BackupError(f'无法解析 {file_path} 第 {line_no} 行: {exc}') from exc

def _import_database_from_sqlite(sqlite_path: str) -> None:
    """Load data from the SQLite backup into the current database."""
    conn = sqlite3.connect(sqlite_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    dialect = db.engine.dialect.name

    try:
        # Ensure schema exists
        db.create_all()

        # Build FK disable/enable statements
        disable_fk: Optional[str] = None
        enable_fk: Optional[str] = None
        if dialect == 'mysql':
            disable_fk = 'SET FOREIGN_KEY_CHECKS=0'
            enable_fk = 'SET FOREIGN_KEY_CHECKS=1'
        elif dialect == 'sqlite':
            disable_fk = 'PRAGMA foreign_keys = OFF'
            enable_fk = 'PRAGMA foreign_keys = ON'
        elif dialect == 'postgresql':
            # PostgreSQL handles this per-session via constraints; we'll use TRUNCATE CASCADE
            pass

        with db.engine.begin() as target_conn:
            if disable_fk:
                target_conn.exec_driver_sql(disable_fk)

            # Clear existing data
            for table in reversed(db.metadata.sorted_tables):
                if dialect == 'postgresql':
                    target_conn.exec_driver_sql(f'TRUNCATE TABLE "{table.name}" CASCADE')
                else:
                    try:
                        target_conn.execute(table.delete())
                    except Exception:
                        # Table might not exist; skip
                        pass

            # Insert data from backup
            for table in db.metadata.sorted_tables:
                cursor.execute(f'SELECT name FROM sqlite_master WHERE type="table" AND name="{table.name}"')
                if not cursor.fetchone():
                    continue

                cursor.execute(f'SELECT * FROM "{table.name}"')
                source_rows = cursor.fetchall()
                if not source_rows:
                    continue

                column_names = [col.name for col in table.columns]
                for src_row in source_rows:
                    row_dict: Dict[str, Any] = {}
                    for col_name in column_names:
                        try:
                            raw = src_row[col_name]
                        except (IndexError, KeyError):
                            raw = None
                        row_dict[col_name] = _deserialize_value(raw, table.columns[col_name])

                    target_conn.execute(table.insert().values(**row_dict))

            if enable_fk:
                target_conn.exec_driver_sql(enable_fk)

        db.session.remove()
    finally:
        conn.close()


def _deserialize_value(raw: Any, column) -> Any:
    """Convert serialized values back to column-friendly Python types."""
    python_type = None
    try:
        python_type = column.type.python_type
    except (AttributeError, NotImplementedError):
        python_type = None

    if isinstance(raw, dict) and raw.get('__type__') == 'bytes':
        data = raw.get('data')
        if data:
            try:
                raw = base64.b64decode(data)
            except Exception:
                raw = b''
        else:
            raw = b''

    if raw is None or (isinstance(raw, str) and raw.strip() == ''):
        if column.nullable or python_type in (int, float, bool, Decimal):
            return None

    if python_type == bool:
        if isinstance(raw, str):
            return raw.lower() in ('1', 'true', 'yes', 'on')
        return bool(raw)

    if python_type == int:
        if raw is None or raw == '':
            return None
        try:
            return int(raw)
        except (TypeError, ValueError):
            return None

    if python_type == float:
        if raw is None or raw == '':
            return None
        try:
            return float(raw)
        except (TypeError, ValueError):
            return None

    if python_type == Decimal:
        if raw is None or raw == '':
            return None
        try:
            return Decimal(str(raw))
        except Exception:
            return None

    if python_type == datetime:
        if isinstance(raw, str) and raw:
            try:
                return datetime.fromisoformat(raw.replace('Z', '+00:00'))
            except ValueError:
                return None
        return raw

    if python_type == date:
        if isinstance(raw, str) and raw:
            try:
                return date.fromisoformat(raw[:10])
            except ValueError:
                return None
        return raw

    if python_type == time:
        if isinstance(raw, str) and raw:
            try:
                return time.fromisoformat(raw)
            except ValueError:
                return None
        return raw

    return raw


# ---------------------------------------------------------------------------
# File helpers
# ---------------------------------------------------------------------------

def _add_uploads_to_zip(zipf: zipfile.ZipFile, upload_folder: str) -> None:
    """Add the uploads directory to the zip archive."""
    _add_directory_to_zip(zipf, upload_folder, 'uploads')


def _copy_upload_tree(src: str, dest: str) -> None:
    """Copy uploaded files from backup to destination folder."""
    os.makedirs(dest, exist_ok=True)

    for root, dirs, files in os.walk(src):
        rel_root = os.path.relpath(root, src)
        dest_root = dest if rel_root == '.' else os.path.join(dest, rel_root)
        os.makedirs(dest_root, exist_ok=True)

        for directory in dirs:
            os.makedirs(os.path.join(dest_root, directory), exist_ok=True)

        for filename in files:
            shutil.copy2(os.path.join(root, filename), os.path.join(dest_root, filename))



def _fix_restored_paths() -> None:
    """Fix install paths for plugins and themes after restore."""
    from app.models.plugin import Plugin
    from app.models.theme import Theme
    
    # Fix plugins
    try:
        plugins = Plugin.query.all()
        plugins_dir = path_utils.project_path('plugins')
        
        for plugin in plugins:
            # Check if current path exists
            if not os.path.exists(plugin.install_path):
                # Try to find in plugins dir
                expected_path = os.path.join(plugins_dir, plugin.name)
                if os.path.exists(expected_path):
                    # Update path using the setter which handles relative path conversion
                    plugin.install_path = expected_path
                    current_app.logger.info(f"Fixed path for plugin {plugin.name}: {expected_path}")
                else:
                    current_app.logger.warning(f"Plugin {plugin.name} not found in {expected_path}")

        # Fix themes
        themes = Theme.query.all()
        themes_dir = path_utils.project_path('themes')
        
        for theme in themes:
            if not os.path.exists(theme.install_path):
                expected_path = os.path.join(themes_dir, theme.name)
                if os.path.exists(expected_path):
                    theme.install_path = expected_path
                    current_app.logger.info(f"Fixed path for theme {theme.name}: {expected_path}")
                else:
                    current_app.logger.warning(f"Theme {theme.name} not found in {expected_path}")

        db.session.commit()
    except Exception as e:
        current_app.logger.error(f"Failed to fix restored paths: {e}")
        db.session.rollback()


# ---------------------------------------------------------------------------
# Runtime refresh
# ---------------------------------------------------------------------------

def _refresh_runtime_state() -> None:
    """Refresh plugin/theme runtime caches after data restoration."""
    plugin_mgr = getattr(current_app, 'plugin_manager', None)
    if plugin_mgr and hasattr(plugin_mgr, 'reload_runtime_state'):
        try:
            plugin_mgr.reload_runtime_state()
        except Exception as exc:
            current_app.logger.warning('插件状态刷新失败: %s', exc)

    theme_mgr = getattr(current_app, 'theme_manager', None)
    if theme_mgr and hasattr(theme_mgr, 'reload_from_database'):
        try:
            theme_mgr.reload_from_database()
        except Exception as exc:
            current_app.logger.warning('主题状态刷新失败: %s', exc)


def _add_extensions_to_zip(zipf: zipfile.ZipFile) -> None:
    """Add plugins and themes to the zip archive."""
    plugins_dir = path_utils.project_path('plugins')
    themes_dir = path_utils.project_path('themes')

    if os.path.isdir(plugins_dir):
        for root, _, files in os.walk(plugins_dir):
            if '__pycache__' in root:
                continue
            for filename in files:
                if filename.endswith('.pyc'):
                    continue
                abs_path = os.path.join(root, filename)
                rel_path = os.path.relpath(abs_path, plugins_dir)
                arcname = os.path.join('plugins', rel_path).replace('\\', '/')
                zipf.write(abs_path, arcname=arcname)

    if os.path.isdir(themes_dir):
        for root, _, files in os.walk(themes_dir):
            if '__pycache__' in root:
                continue
            for filename in files:
                if filename.endswith('.pyc'):
                    continue
                abs_path = os.path.join(root, filename)
                rel_path = os.path.relpath(abs_path, themes_dir)
                arcname = os.path.join('themes', rel_path).replace('\\', '/')
                zipf.write(abs_path, arcname=arcname)


def _restore_extensions_from_zip(tmp_dir: str, overwrite: bool) -> None:
    """Restore plugins and themes from the backup."""
    plugins_src = os.path.join(tmp_dir, 'plugins')
    themes_src = os.path.join(tmp_dir, 'themes')
    
    plugins_dest = path_utils.project_path('plugins')
    themes_dest = path_utils.project_path('themes')

    if os.path.isdir(plugins_src):
        _copy_extension_dirs(plugins_src, plugins_dest, overwrite)
    
    if os.path.isdir(themes_src):
        _copy_extension_dirs(themes_src, themes_dest, overwrite)


def _copy_extension_dirs(src_dir: str, dest_dir: str, overwrite: bool) -> None:
    """Copy extension directories from source to destination."""
    if not os.path.exists(dest_dir):
        os.makedirs(dest_dir)

    for item in os.listdir(src_dir):
        src_path = os.path.join(src_dir, item)
        dest_path = os.path.join(dest_dir, item)
        
        if os.path.isdir(src_path):
            if os.path.exists(dest_path):
                if overwrite:
                    # Try to remove existing directory
                    try:
                        shutil.rmtree(dest_path)
                    except OSError as e:
                        # If removal fails (e.g. file in use), try to rename it first
                        current_app.logger.warning(f"Failed to remove {dest_path}: {e}. Trying to rename and replace.")
                        try:
                            tmp_backup = dest_path + f".bak.{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"
                            os.rename(dest_path, tmp_backup)
                            # Schedule deletion of backup? For now just leave it or try to delete
                            try:
                                shutil.rmtree(tmp_backup)
                            except OSError:
                                pass # Ignore if we can't delete the backup immediately
                        except OSError as e2:
                            current_app.logger.error(f"Failed to replace extension {item}: {e2}")
                            # If we can't rename, we might try to copy over it (merge)
                            # But copytree requires dest not to exist.
                            # So we skip this item if we can't clear the path.
                            continue
                    
                    shutil.copytree(src_path, dest_path)
            else:
                shutil.copytree(src_path, dest_path)


def _apply_restored_extensions() -> None:
    """Apply restored themes and plugins immediately.
    
    注意：由于 Flask 的限制，蓝图(Blueprint)不能在应用处理第一个请求后注册。
    因此这里只做以下工作：
    1. 发现新的主题/插件并注册到数据库
    2. 更新数据库中的路径
    3. 刷新主题管理器的内存缓存（不涉及蓝图）
    
    插件的蓝图和扩展功能需要重启应用后才能完全生效。
    """
    from app.models.plugin import Plugin
    from app.models.theme import Theme
    from app.models.setting import SettingManager

    current_app.logger.info("开始应用恢复的扩展...")

    theme_mgr = getattr(current_app, 'theme_manager', None)
    
    # 1. 发现新主题并注册到数据库
    if theme_mgr:
        try:
            current_app.logger.info("重新扫描主题目录...")
            theme_mgr.discover_themes()
        except Exception as e:
            current_app.logger.error(f"扫描主题失败: {e}")

    # 2. 更新活跃主题（只更新数据库和内存缓存，不注册蓝图）
    active_theme_name = SettingManager.get('active_theme')
    current_app.logger.info(f"数据库中的活跃主题: {active_theme_name}")
    
    if active_theme_name and theme_mgr:
        theme = Theme.query.filter_by(name=active_theme_name).first()
        if theme:
            current_app.logger.info(f"找到主题记录: {theme.name}, 路径: {theme.install_path}")
            if os.path.exists(theme.install_path):
                try:
                    # 只更新数据库中的激活状态，不完全activate（避免蓝图注册）
                    Theme.query.update({Theme.is_active: False})
                    theme.is_active = True
                    db.session.commit()
                    
                    # 更新内存中的当前主题引用
                    theme_mgr.current_theme = theme
                    current_app.logger.info(f"主题状态已更新: {active_theme_name}")
                except Exception as e:
                    current_app.logger.error(f"更新主题状态 {active_theme_name} 失败: {e}")
                    db.session.rollback()
            else:
                current_app.logger.info(f"主题路径不存在: {theme.install_path}，将跳过主题激活。")
        else:
            current_app.logger.info(f"数据库中未找到主题: {active_theme_name}，该主题可能未包含在备份中，跳过。")

    # 3. 插件的蓝图加载需要重启应用，这里只记录日志
    active_plugins = Plugin.query.filter_by(is_active=True).all()
    if active_plugins:
        plugin_names = [p.name for p in active_plugins]
        current_app.logger.info(f"以下插件需要重启后才能完全生效: {plugin_names}")
    
    current_app.logger.info("扩展应用完成。注意：部分功能（如插件蓝图）需要重启应用后才能完全生效。")

