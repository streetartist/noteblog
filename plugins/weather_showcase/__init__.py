"""
Weather Showcase plugin
在页面上显示多种天气特效，并提供后台管理。
"""
import json
from datetime import datetime
from typing import Any, Dict

from flask import Blueprint, current_app, jsonify, render_template, request

from app.services.plugin_manager import PluginBase


DEFAULT_CONFIG: Dict[str, Any] = {
    'enabled': True,
    'default_type': 'rain',
    'intensity': 3,
    'auto_rotate': False,
    'rotate_seconds': 18,
    'show_toggle': True,
    'allow_on': 'all',  # all | home | post
    'accent_color': '#7dd3fc'
}


class WeatherShowcasePlugin(PluginBase):
    def __init__(self):
        super().__init__()
        self.name = 'weather_showcase'
        self.version = '1.0.0'
        self.description = '展示雨、雪、极光等天气特效，支持后台配置'
        self.author = 'Noteblog'

    # -------- lifecycle --------
    def install(self):
        cfg = self._safe_config()
        self.set_config(cfg)
        current_app.logger.info('weather_showcase installed with defaults')
        return True

    def register_hooks(self):
        if not hasattr(current_app, 'plugin_manager'):
            return
        pm = current_app.plugin_manager
        pm.register_template_hook('head_assets', self._render_head_assets, priority=12, plugin_name=self.name)
        pm.register_template_hook('content_top', self._render_stage, priority=12, plugin_name=self.name)
        pm.register_template_hook('scripts_assets', self._render_scripts, priority=12, plugin_name=self.name)

    # -------- rendering helpers --------
    def _safe_config(self) -> Dict[str, Any]:
        cfg = DEFAULT_CONFIG.copy()
        try:
            stored = self.get_config() or {}
            cfg.update(stored)
        except Exception:
            pass
        cfg['enabled'] = bool(cfg.get('enabled', True))
        cfg['auto_rotate'] = bool(cfg.get('auto_rotate', False))
        cfg['show_toggle'] = bool(cfg.get('show_toggle', True))
        cfg['allow_on'] = (cfg.get('allow_on') or 'all').lower()
        try:
            cfg['intensity'] = max(1, min(5, int(cfg.get('intensity', 3))))
        except Exception:
            cfg['intensity'] = 3
        try:
            cfg['rotate_seconds'] = max(5, min(120, int(cfg.get('rotate_seconds', 18))))
        except Exception:
            cfg['rotate_seconds'] = 18
        cfg['default_type'] = (cfg.get('default_type') or 'rain').lower()
        cfg['accent_color'] = (cfg.get('accent_color') or '#7dd3fc').strip()
        return cfg

    def _render_head_assets(self) -> str:
        cfg = self._safe_config()
        if not cfg['enabled']:
            return ''
        return '<link rel="stylesheet" href="/static/plugins/weather_showcase/css/weather_showcase.css">'

    def _should_render_on_request(self, cfg: Dict[str, Any]) -> bool:
        try:
            path = request.path or ''
        except Exception:
            return True
        scope = cfg.get('allow_on', 'all')
        if scope == 'home':
            return path in ('/', '/index') or path.startswith('/page')
        if scope == 'post':
            return '/post/' in path
        return True

    def _render_stage(self) -> str:
        cfg = self._safe_config()
        if not cfg['enabled'] or not self._should_render_on_request(cfg):
            return ''
        data_attrs = [
            f'data-weather-enabled="{str(cfg["enabled"]).lower()}"',
            f'data-weather-type="{cfg["default_type"]}"',
            f'data-weather-intensity="{cfg["intensity"]}"',
            f'data-weather-rotate="{str(cfg["auto_rotate"]).lower()}"',
            f'data-weather-rotate-seconds="{cfg["rotate_seconds"]}"',
            f'data-weather-toggle="{str(cfg["show_toggle"]).lower()}"',
            f'data-weather-accent="{cfg["accent_color"]}"'
        ]
        attrs = ' '.join(data_attrs)
        timestamp = datetime.utcnow().isoformat()
        return f'''
<div class="weather-showcase" data-weather-stage {attrs}>
    <div class="weather-stage" aria-hidden="true"></div>
    <button class="weather-toggle" type="button" data-weather-toggle aria-label="切换天气显示">天气特效</button>
    <div class="weather-legend" data-weather-legend>
        <span class="legend-dot"></span>
        <span class="legend-text">{cfg['default_type'].title()} · {timestamp[:16]}Z</span>
    </div>
</div>
'''

    def _render_scripts(self) -> str:
        cfg = self._safe_config()
        if not cfg['enabled']:
            return ''
        cfg_json = json.dumps(cfg, ensure_ascii=False)
        return f'''
<script>window.__WEATHER_SHOWCASE_CONFIG = {cfg_json};</script>
<script src="/static/plugins/weather_showcase/js/weather_showcase.js"></script>
'''


# -------- factory --------
def create_plugin():
    return WeatherShowcasePlugin()


# -------- blueprint --------
weather_showcase_bp = Blueprint(
    'weather_showcase', __name__, template_folder='templates', static_folder='static'
)


@weather_showcase_bp.route('/plugins/weather_showcase/admin')
def admin_page():
    plugin = current_app.plugin_manager.get_plugin('weather_showcase') if hasattr(current_app, 'plugin_manager') else None
    if not plugin:
        return '插件未加载', 404
    cfg = plugin._safe_config()
    return render_template('weather_showcase_admin.html', config=cfg)


@weather_showcase_bp.route('/plugins/weather_showcase/api/config', methods=['POST'])
def save_config():
    try:
        plugin = current_app.plugin_manager.get_plugin('weather_showcase') if hasattr(current_app, 'plugin_manager') else None
        if not plugin:
            return jsonify({'success': False, 'message': '插件未加载'})
        data = request.get_json() or {}
        cfg = plugin._safe_config()

        cfg['enabled'] = bool(data.get('enabled', cfg['enabled']))
        cfg['auto_rotate'] = bool(data.get('auto_rotate', cfg['auto_rotate']))
        cfg['show_toggle'] = bool(data.get('show_toggle', cfg['show_toggle']))
        allow_on = (data.get('allow_on') or cfg['allow_on']).lower()
        cfg['allow_on'] = allow_on if allow_on in ('all', 'home', 'post') else 'all'
        default_type = (data.get('default_type') or cfg['default_type']).lower()
        cfg['default_type'] = default_type if default_type in ('rain', 'snow', 'stars', 'meteors', 'aurora') else 'rain'
        try:
            cfg['intensity'] = max(1, min(5, int(data.get('intensity', cfg['intensity']))))
        except Exception:
            pass
        try:
            cfg['rotate_seconds'] = max(5, min(120, int(data.get('rotate_seconds', cfg['rotate_seconds']))))
        except Exception:
            pass
        color = (data.get('accent_color') or cfg['accent_color']).strip()
        if color:
            cfg['accent_color'] = color

        plugin.set_config(cfg)
        return jsonify({'success': True, 'message': '配置已保存', 'config': cfg})
    except Exception as exc:
        current_app.logger.error(f'保存 weather_showcase 配置失败: {exc}')
        return jsonify({'success': False, 'message': str(exc)})
