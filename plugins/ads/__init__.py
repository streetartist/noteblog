"""
广告插件
支持侧边栏广告位和Google AdSense验证
"""
import os
from flask import current_app, render_template, Blueprint, request, jsonify
from app.services.plugin_manager import PluginBase
from .models import AdSlot


class AdsPlugin(PluginBase):
    """广告插件类"""

    def __init__(self):
        super().__init__()
        self.name = 'ads'
        self.version = '1.0.0'
        self.description = '广告管理插件，支持Google AdSense'
        self.author = 'Noteblog'

    def get_info(self):
        return {
            'name': self.name,
            'version': self.version,
            'description': self.description,
            'author': self.author,
            'hooks': self.get_registered_hooks(),
            'filters': self.get_registered_filters()
        }

    def install(self):
        current_app.logger.info(f"Installing {self.name} plugin")
        try:
            from app import db
            db.create_all()
            current_app.logger.info("Ad slots table created successfully")
        except Exception as e:
            current_app.logger.error(f"Failed to create ad slots table: {e}")
            return False
        return True

    def uninstall(self):
        current_app.logger.info(f"Uninstalling {self.name} plugin")
        return True

    def render_sidebar_widget(self):
        """渲染侧边栏广告"""
        config = self.get_config()
        if not config.get('enabled', True) or not config.get('show_in_sidebar', True):
            return ""

        slots = AdSlot.get_active_by_type('sidebar')
        if not slots:
            return ""

        template_path = os.path.join(os.path.dirname(__file__), 'templates', 'sidebar.html')
        with open(template_path, 'r', encoding='utf-8') as f:
            template_content = f.read()

        context = {
            'ads': {
                'slots': slots
            }
        }

        html_content = current_app.plugin_manager.render_plugin_template(
            self.name, template_content, context
        )
        self._register_assets()
        return html_content

    def render_adsense_script(self):
        """渲染AdSense验证脚本到head"""
        config = self.get_config()
        if not config.get('enabled', True):
            return ""
        client_id = config.get('adsense_client_id', '').strip()
        if not client_id:
            return ""
        return (
            f'<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js'
            f'?client={client_id}" crossorigin="anonymous"></script>'
        )

    def _register_assets(self):
        if hasattr(current_app, 'plugin_manager'):
            current_app.plugin_manager.register_template_hook(
                'head_assets',
                lambda: '<link rel="stylesheet" href="/static/plugins/ads/css/ads.css">',
                priority=10,
                plugin_name=self.name
            )

    def register_hooks(self):
        if hasattr(current_app, 'plugin_manager'):
            current_app.plugin_manager.register_template_hook(
                'sidebar_bottom',
                self.render_sidebar_widget,
                priority=20,
                plugin_name=self.name
            )
            current_app.plugin_manager.register_template_hook(
                'head_assets',
                self.render_adsense_script,
                priority=5,
                plugin_name=self.name
            )


def create_plugin():
    return AdsPlugin()


ads_bp = Blueprint('ads', __name__,
                   template_folder='templates',
                   static_folder='static')


@ads_bp.route('/plugins/ads/admin')
def admin_page():
    try:
        plugin = current_app.plugin_manager.get_plugin('ads')
        if plugin:
            config = plugin.get_config()
            slots = [s.to_dict() for s in AdSlot.get_all()]
            return render_template('ads_admin.html', config=config, slots=slots)
        return "插件未找到", 404
    except Exception as e:
        current_app.logger.error(f"获取广告插件失败: {e}")
        return f"插件加载失败: {str(e)}", 500


@ads_bp.route('/plugins/ads/api/config', methods=['POST'])
def api_config():
    try:
        plugin = current_app.plugin_manager.get_plugin('ads')
        if not plugin:
            return jsonify({'success': False, 'message': '插件未找到'})
        config_data = request.get_json()
        plugin.set_config(config_data)
        return jsonify({'success': True, 'message': '配置保存成功'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


@ads_bp.route('/plugins/ads/api/slots', methods=['GET', 'POST'])
def api_slots():
    try:
        plugin = current_app.plugin_manager.get_plugin('ads')
        if not plugin:
            return jsonify({'success': False, 'message': '插件未找到'})

        if request.method == 'GET':
            slots = [s.to_dict() for s in AdSlot.get_all()]
            return jsonify({'success': True, 'data': slots})

        data = request.get_json()
        slot = AdSlot(
            name=data.get('name'),
            ad_code=data.get('ad_code'),
            slot_type=data.get('slot_type', 'sidebar'),
            sort_order=data.get('sort_order', 0),
            is_active=data.get('is_active', True)
        )
        if slot.save():
            return jsonify({'success': True, 'message': '广告位添加成功'})
        return jsonify({'success': False, 'message': '广告位添加失败'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


@ads_bp.route('/plugins/ads/api/slots/<int:slot_id>', methods=['PUT', 'DELETE'])
def api_slot_detail(slot_id):
    try:
        plugin = current_app.plugin_manager.get_plugin('ads')
        if not plugin:
            return jsonify({'success': False, 'message': '插件未找到'})

        slot = AdSlot.get_by_id(slot_id)
        if not slot:
            return jsonify({'success': False, 'message': '广告位不存在'})

        if request.method == 'PUT':
            data = request.get_json()
            slot.name = data.get('name', slot.name)
            slot.ad_code = data.get('ad_code', slot.ad_code)
            slot.slot_type = data.get('slot_type', slot.slot_type)
            slot.sort_order = data.get('sort_order', slot.sort_order)
            slot.is_active = data.get('is_active', slot.is_active)
            if slot.save():
                return jsonify({'success': True, 'message': '广告位更新成功'})
            return jsonify({'success': False, 'message': '广告位更新失败'})

        if slot.delete():
            return jsonify({'success': True, 'message': '广告位删除成功'})
        return jsonify({'success': False, 'message': '广告位删除失败'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})
