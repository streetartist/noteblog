**Noteblog 主题与插件开发指南**

本指南面向希望为 Noteblog 扩展 UI/功能的开发者，汇总了主题与插件体系的结构、规范与调试要点。阅读前建议先浏览 `README.md` 了解项目结构，再结合 `themes/THEME_GUIDE.md`、`app/services/plugin_manager.py` 获取实现细节。

## 1. 架构概览
- 主题通过 `app/services/theme_manager.py` 挂载，负责模板、静态资源与前端扩展；插件通过 `app/services/plugin_manager.py` 管理，负责业务钩子、过滤器与后台扩展。
- 两套体系互相解耦：主题提供模板插槽(`plugin_hooks.*`)，插件在运行时向这些插槽注入 HTML/CSS/JS；插件还可监听控制器中的 `do_action` / `apply_filters` 来拦截或补充业务逻辑。
- 所有扩展均运行在 Flask Application Context 内，日志输出可在 `logs/` 或终端中查看。

## 2. 主题开发
### 2.1 推荐目录结构
```
themes/
  your-theme/
    theme.json             # 元数据 + 配置 schema
    extensions.py          # 可选：Blueprint/自定义路由
    templates/
      base.html            # 必须，包含核心 blocks
      index.html           # 列表页
      post.html            # 详情页（含评论）
      ...
    static/
      css/style.css        # 主样式，覆盖规范类
      css/markdown.css     # Markdown 渲染
      js/app.js            # 可选交互逻辑
    screenshot.png
```

### 2.2 `theme.json` 关键字段
- `display_name`, `description`, `version`, `author`, `license`, `min_version`：用于后台展示与兼容性检查。
- `config_schema`：遵循 JSON Schema 的简化结构，字段名尽量沿用 `themes/default`，以便后台自动生成设置表单（如 `logo`, `primary_color`, `show_sidebar`）。
- `custom_pages`：`[{"route": "/timeline", "template": "pages/timeline.html", "methods": ["GET"], "context": {"title": "时间线"}}]`，用于声明无需写 Python 的静态路由。
- `assets.version` 或自定义字段可帮助做静态资源 cache busting。

### 2.3 模板规范
- `templates/base.html` 必须声明以下 Jinja block：`title`, `description`, `keywords`, `head`, `content`, `sidebar`, `scripts`。若主题提供顶部/底部插槽，可通过 block `content_top`, `content_bottom` 再嵌套。
- 详情页 `post.html` 需包含评论表单与列表，并保留 `.comments-section`, `.comments-list`, `.comment-item` 等类，便于插件追加功能（如验证码、第三方评论）。
- 模板中通过 `plugin_hooks` 注入插件内容，常见插槽：`head_assets`, `scripts_assets`, `nav`, `content_top`, `content_bottom`, `sidebar_bottom`, `post_meta`, `post_footer`, `comment_form_top`, `comment_form_bottom`, `footer`。遍历时务必加 `|safe` 输出。
- 必需 CSS 类最小集（用于核心 DOM 与插件定位）：`.container`, `.site-header`, `.site-main`, `.content-wrapper`, `.main-content`, `.with-sidebar`, `.sidebar`, `.posts-list`, `.post-item`, `.post-title`, `.post-meta`, `.post-excerpt`, `.post-detail`, `.post-footer`, `.comments-section`, `.comment-item`, `.site-footer`, `.back-to-top`。

### 2.4 模板上下文
- 基础变量：`site_title`, `site_description`, `current_user`, `recent_posts`, `categories`, `tags`, `get_theme_config()`, `plugin_hooks`。
- 若主题自带 Blueprint（`extensions.py`），请使用 `theme_manager.render_template()` 渲染，以确保自定义页面仍可拿到当前主题上下文与 Hooks。

### 2.5 可选扩展
- **自定义路由**：在 `extensions.py` 中定义 Flask Blueprint 并返回，Theme Manager 会在主题激活时自动注册。视图内部可继续使用 `plugin_manager`、`theme_manager` 提供的工具。
- **多语言/文案**：避免写死中文/英文，尽量通过配置或后端传参控制。日期格式化可调用 `moment`/`datetime` helpers，或在模板中用 `post.created_at.strftime()`。
- **静态资源**：推荐用构建工具输出到 `static/`，并在 `theme.json` 中声明版本；CDN 资源应提供本地 fallback，以便离线部署。

### 2.6 调试与发布检查表
- `scripts/test_template_render.py`, `scripts/test_admin_page.py` 等脚本可快速检验模板是否能被渲染；`THEME_FALLBACK_FEATURE.md` 解释了回退策略。
- 发布前自查：
  - [ ] `theme.json` 填写元数据与 `config_schema`
  - [ ] `base.html` 具备所有核心 block
  - [ ] `plugin_hooks.*` 插槽全部保留并渲染 `|safe`
  - [ ] `.comments-*` 等约定类存在
  - [ ] 移动端宽度 < 768px 下布局正常，菜单可聚焦
  - [ ] Markdown 样式、代码块与图片不溢出容器
  - [ ] 若声明 `custom_pages` 或 Blueprint，均已测试 404/500 行为

## 3. 插件开发
### 3.1 体系速览
- 插件记录使用 `app/models/plugin.py` 中的 `Plugin`、`PluginHook` 模型，支持启用/停用、版本约束与配置存储。
- `plugin_manager` 负责：发现插件、动态导入 `plugins/<name>/__init__.py`、调用 `PluginBase` 生命周期、注册钩子/过滤器/模板插槽、自动挂载 Blueprint。
- 插件可以向三类钩子注册：动作(`register_hook` → `do_action`)、过滤器(`register_filter` → `apply_filters`) 和模板插槽(`register_template_hook` → `plugin_hooks.*`)。

### 3.2 目录示例
```
plugins/
  reading_time/
    plugin.json
    __init__.py
    models.py              # 可选：SQLAlchemy 模型
    templates/
      admin.html
      partials/badge.html
    static/
      css/plugin.css
      js/plugin.js
```

### 3.3 `plugin.json` 字段
- **必填**：`name`, `display_name`, `version`, `description`, `author`, `entry_point` (入口函数名, 如 `create_plugin`), `min_version` (建议), `install_path` 由系统推断。
- **可选**：
  - `blueprints`: `[{"name": "reading_time_bp", "url_prefix": "/reading-time"}]`，供后台展示路由信息。
  - `config_schema`: 与主题类似，用于后台渲染配置项。
  - `hooks` / `filters`: 仅用于文档化；真正的注册在代码里完成。
  - `requirements`: 列出额外 Python 依赖，便于部署时安装。
  - `permissions`: 需额外授予的后台权限。
  - `templates`, `assets`, `database`: 用于说明所需模板或数据表（详见 `plugins/ai_summary/plugin.json`）。

### 3.4 插件主类与入口
```python
# plugins/reading_time/__init__.py
from flask import render_template
from app.services.plugin_manager import PluginBase, plugin_manager

class ReadingTimePlugin(PluginBase):
    def __init__(self):
        super().__init__()
        self.name = "reading_time"
        self.version = "1.0.0"
        self.description = "在文章尾部显示预计阅读时长"

    def register_hooks(self):
        plugin_manager.register_filter(
            'post_context', self.add_reading_time_to_context,
            accepted_args=2, priority=10, plugin_name=self.name
        )
        plugin_manager.register_template_hook(
            'post_footer', self.render_reading_time_badge,
            priority=20, plugin_name=self.name
        )

    def add_reading_time_to_context(self, context, post):
        words = len(post.content.split())
        context['reading_time'] = max(1, words // 250)
        return context

    def render_reading_time_badge(self):
        return render_template('reading_time/partials/badge.html')

def create_plugin():
    return ReadingTimePlugin()
```
- `PluginManager._load_plugin` 会寻找 `create_plugin()` 或同名工厂，实例化后调用 `register_hooks()`；确保该方法里完成全部钩子注册。
- 若需要安装时初始化数据，可实现 `install()`；停用/卸载时可扩展 `deactivate()` / `uninstall()`，处理清理逻辑。

### 3.5 常用钩子清单（源自 `app/views/*.py`）
**动作钩子**（`do_action()`）
| 域 | 钩子 | 触发点 |
| --- | --- | --- |
| 站点 | `before_index_render` | 首页渲染前，可修改 `posts` 列表 |
| 文章 | `before_post_render` / `before_post_save` / `after_post_save` / `before_post_update` / `after_post_update` / `before_post_delete` / `after_post_delete` | `main.py`, `admin.py`, `api.py` 中文章读取/保存流程 |
| 评论 | `before_comment_save` / `after_comment_save` / `before_comment_update` / `after_comment_update` | 评论创建/编辑 API |
| 用户 | `before_user_login`, `after_user_login`, `before_user_register`, `after_user_register`, `before_user_logout`, `before_profile_update`, `after_profile_update`, `before_password_change`, `after_password_change`, `before_password_reset`, `after_password_reset` | `app/views/auth.py` 对应动作 |

**过滤器**（`apply_filters()`）
| 名称 | 默认上下文 |
| --- | --- |
| `index_context` | 首页模板上下文，在 `app/views/main.py` 中创建后调用，可追加统计数据 |
| `post_context` | 文章详情上下文；第二个参数是 `post` 模型 |
| `admin_post_editor_hooks` | 后台文章编辑器扩展点，参数包含 `mode` 与 `post` |

**模板钩子**（`plugin_hooks.*`）
- `head_assets`, `scripts_assets`: 向 `<head>` / `<body>` 尾部插入 CSS/JS。
- `nav`, `content_top`, `content_bottom`, `sidebar_bottom`, `footer`: 扩展布局。
- `post_meta`, `post_footer`: 在文章详情元信息、底部操作区域注入 HTML。
- `comment_form_top`, `comment_form_bottom`: 评论表单上下插槽（验证码、第三方登录等）。

使用钩子时可通过 `priority` 控制顺序（数字越小优先级越高），`accepted_args` 控制回调将收到的参数个数。模板钩子回调不接收参数，应返回 HTML 字符串，可配合 `plugin_manager.render_plugin_template()`。

### 3.6 Blueprint、模板与静态资源
- 在插件模块中定义 `Blueprint` 对象（如 `hello_world_bp = Blueprint('hello_world', __name__, template_folder='templates', static_folder='static', url_prefix='/hello-world')`），Plugin Manager 会自动扫描并 `register_blueprint`。
- 插件模板默认位于 `plugins/<name>/templates/`。如果需要从钩子中渲染 HTML，可直接使用 `render_template()`，Flask 会正确解析插件模板目录。
- 静态文件可通过 `/static/plugins/<plugin_name>/<path>` 访问，或在模板中使用 `url_for('static', filename='plugins/<plugin_name>/css/plugin.css')`。

### 3.7 配置、数据与依赖
- `PluginBase.get_config()` / `set_config(dict)` 用于持久化 JSON。通常模式：`config = self.get_config(); config['message'] = '...'; self.set_config(config)`。
- 需要数据库表时，可将 SQLAlchemy 模型放在 `plugins/<name>/models.py`，并在 `plugin.json` 的 `database.models` 中声明，便于迁移脚本识别。复杂场景可直接编写 Alembic 脚本并在 `install()` 中调用。
- 若插件依赖第三方包，请在 `plugin.json` 的 `requirements` 列出，并在仓库 `requirements.txt` 或私有安装脚本中同步。

- 初次开发可利用 `scripts/test_plugin_discovery.py`, `scripts/test_admin_plugins.py`, `scripts/test_admin_page.py` 检验插件注册、后台 UI 可用性。
- 后台 -> 插件管理 中的日志输出是排错首选；若钩子未执行，确认插件处于已启用状态且 `register_hooks()` 已被调用。
- 发布前自查：
  - [ ] `plugin.json` 填写版本、入口、依赖与钩子声明
  - [ ] `create_plugin()` 返回的实例继承 `PluginBase` 且实现 `register_hooks`
  - [ ] 所有 Blueprint `url_prefix` 不与核心路由冲突
  - [ ] 模板钩子输出使用 `|safe`，避免双重转义
  - [ ] 如涉及外网 API（如 `plugins/ai_summary`），提供可配置的 `endpoint` 与超时处理

## 4. 常见排错思路
- **钩子未触发**：确认钩子名称拼写与源码一致；可在 `register_hooks` 中通过 `current_app.logger.info` 记录；必要时在 `plugin_manager.hooks` 内检查是否存在。
- **模板找不到静态资源**：检查 `url_for('static', filename='plugins/<name>/...')` 中路径；确保插件打包时包含 `static/` 目录。
- **配置未保存**：`set_config` 需要一次性写入完整字典，避免只传单个键值；保存后检查数据库 `plugins.config_data`。
- **蓝图注册报错**：通常来自路由函数在模块导入阶段访问 `current_app`。将此类逻辑放到请求内或使用惰性加载，避免在蓝图定义时执行。

通过遵循以上规范，主题与插件即可在 Noteblog 中安全、可维护地运行。如需进一步的 lint/脚手架支持，可基于本文档添加 CI 脚本或扩展管理后台。
