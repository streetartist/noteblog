"""
迁移脚本：为 plugins 表添加 is_installed 列，并将已激活的插件标记为已安装。

纯 SQL 操作，不依赖 Flask app（避免 ORM 与数据库列不一致的问题）。

用法：
    python scripts/migrate_plugin_is_installed.py
"""
import os
import sqlite3

db_path = os.environ.get('DATABASE_PATH')
if not db_path:
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    instance_dir = os.path.join(project_root, 'instance')
    db_path = os.path.join(instance_dir, 'noteblog.db')

if not os.path.exists(db_path):
    print(f"[ERROR] 数据库文件不存在: {db_path}")
    print("如果数据库路径不同，请设置环境变量 DATABASE_PATH 后重试")
    exit(1)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

try:
    # 1. 检查列是否已存在
    cursor.execute("PRAGMA table_info(plugins)")
    columns = [row[1] for row in cursor.fetchall()]

    if 'is_installed' not in columns:
        cursor.execute("ALTER TABLE plugins ADD COLUMN is_installed BOOLEAN DEFAULT 0")
        print("[OK] 已添加 is_installed 列")
    else:
        print("[SKIP] is_installed 列已存在")

    # 2. 已激活的插件标记为已安装（排除 ads，它之前没真正安装成功）
    cursor.execute("""
        UPDATE plugins SET is_installed = 1
        WHERE is_active = 1 AND (is_installed = 0 OR is_installed IS NULL)
        AND name != 'ads'
    """)
    print(f"[OK] 已将 {cursor.rowcount} 个已激活插件标记为已安装")

    # 3. ads 插件重置为未安装未激活，让用户重新走安装→激活流程
    cursor.execute("UPDATE plugins SET is_installed = 0, is_active = 0 WHERE name = 'ads'")
    print(f"[OK] 已重置 ads 插件状态")

    conn.commit()
finally:
    cursor.close()
    conn.close()
