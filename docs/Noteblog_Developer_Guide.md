# Noteblog 开发指南

> 本书面向希望参与 Noteblog 本体开发、主题制作或插件编写的开发者。

---

## 第一部分：本体开发

### 1.1 项目结构

```
noteblog/
├── app/
│   ├── __init__.py          # 应用工厂 create_app()
│   ├── models/              # SQLAlchemy 模型
│   │   ├── post.py          # Post, Category, Tag
│   │   ├── comment.py       # Comment
│   │   ├── user.py          # User
│   │   ├── setting.py       # Setting, SettingManager
│   │   ├── plugin.py        # Plugin, PluginHook
│   │   └── theme.py         # Theme
│   ├── views/               # 蓝图（路由）
│   │   ├── main.py          # 前台页面
│   │   ├── admin.py         # 后台管理
│   │   ├── auth.py          # 认证
│   │   └── api.py           # RESTful API
│   ├── services/            # 业务服务
│   │   ├── plugin_manager.py
│   │   ├── theme_manager.py
│   │   ├── markdown_service.py
│   │   └── backup_service.py
│   └── utils/               # 工具函数
├── themes/                  # 主题目录
├── plugins/                 # 插件目录
├── migrations/              # 数据库迁移
├── scripts/                 # 管理脚本
├── run.py                   # 启动入口 + CLI 命令
└── docs/                    # 文档
```

### 1.2 技术栈

- Python 3.9+ / Flask 2.x
- SQLAlchemy + Flask-Migrate（数据库）
- Flask-Login（认证）
- Jinja2（模板）
- Markdown + Bleach（内容渲染与安全过滤）
- EasyMDE（Markdown 编辑器）

### 1.3 应用工厂

`app/__init__.py` 中的 `create_app()` 负责：
1. 初始化 Flask 实例与配置
2. 应用 `ProxyFix` 中间件（反向代理支持）
3. 初始化数据库、登录管理器、CORS
4. 注册蓝图（main, auth, admin, api）
5. 初始化插件系统和主题系统
6. 注册全局模板上下文、过滤器、错误处理器

### 1.4 数据模型

#### Post
- `title`, `slug`, `content`, `excerpt`
- `status`: draft / published
- `created_at`: 记录创建时间
- `published_at`: 首次发布时间（用于排序）
- `is_top`: 置顶标记
- 关联：`author` (User), `category` (Category), `tags` (多对多)

#### Category
- `name`, `slug`, `description`
- `is_active`, `sort_order`, `parent_id`

#### Comment
- `content`, `author_name`, `author_email`, `author_ip`
- `is_approved`, `is_spam`
- 关联：`post`, `parent`（支持嵌套回复）

### 1.5 路由架构

| 蓝图 | 前缀 | 职责 |
|------|------|------|
| main | / | 首页、文章详情、归档、分类、标签、搜索 |
| auth | /auth | 登录、注册、个人资料 |
| admin | /admin | 后台管理所有功能 |
| api | /api | JSON API（文章 CRUD、分类、评论等） |

### 1.6 CLI 命令

```bash
python run.py init          # 初始化数据库
python run.py full-init     # 完全重建（删除所有数据）
python run.py run           # 启动开发服务器
python run.py create-admin  # 创建管理员
python run.py status        # 查看统计
```

---

## 第二部分：主题开发

### 2.1 目录结构

```
themes/your-theme/
├── theme.json              # 元数据 + 配置 schema
├── extensions.py           # 可选：自定义路由
├── templates/
│   ├── base.html           # 基础布局（必须）
│   ├── index.html          # 首页
│   ├── post.html           # 文章详情
│   ├── archives.html       # 归档
│   ├── category.html       # 分类页
│   ├── tag.html            # 标签页
│   ├── search.html         # 搜索
│   ├── 404.html / 500.html # 错误页
│   └── admin/              # 可选：自定义后台模板
├── static/
│   ├── css/
│   ├── js/
│   └── images/
└── screenshot.png
```

### 2.2 theme.json

```json
{
  "name": "your-theme",
  "display_name": "Your Theme",
  "version": "1.0.0",
  "author": "Your Name",
  "description": "主题描述",
  "min_version": "1.0.0",
  "config_schema": {
    "primary_color": { "type": "color", "default": "#4d6cfa", "label": "主色调" },
    "show_sidebar": { "type": "boolean", "default": true, "label": "显示侧边栏" }
  }
}
```

### 2.3 必须实现的 Jinja Blocks

`base.html` 必须声明：

```jinja2
{% block title %}{% endblock %}
{% block description %}{% endblock %}
{% block keywords %}{% endblock %}
{% block head %}{% endblock %}
{% block content %}{% endblock %}
{% block sidebar %}{% endblock %}
{% block scripts %}{% endblock %}
```

### 2.4 模板上下文变量

所有模板可用：
- `site_title`, `site_description`
- `current_user`
- `recent_posts`, `categories`, `tags`
- `get_theme_config()` — 获取主题配置
- `get_setting(key, default)` — 获取系统设置
- `plugin_hooks` — 插件注入内容

### 2.5 插件插槽（必须保留）

```jinja2
{# head 区域 #}
{% if plugin_hooks and plugin_hooks.head_assets %}
    {% for content in plugin_hooks.head_assets %}{{ content|safe }}{% endfor %}
{% endif %}

{# 内容区域 #}
{% if plugin_hooks and plugin_hooks.content_top %}...{% endif %}
{% if plugin_hooks and plugin_hooks.sidebar_bottom %}...{% endif %}
{% if plugin_hooks and plugin_hooks.post_meta %}...{% endif %}
{% if plugin_hooks and plugin_hooks.post_footer %}...{% endif %}
{% if plugin_hooks and plugin_hooks.comment_form_top %}...{% endif %}
{% if plugin_hooks and plugin_hooks.comment_form_bottom %}...{% endif %}

{# 脚本区域 #}
{% if plugin_hooks and plugin_hooks.scripts_assets %}
    {% for content in plugin_hooks.scripts_assets %}{{ content|safe }}{% endfor %}
{% endif %}
```

<!-- PLACEHOLDER_PART2_CONTINUED -->

### 2.6 暗黑模式规范

主题如果支持暗黑模式，**必须**使用 `[data-theme="dark"]` 属性选择器（设置在 `<html>` 元素上）。

**必须提供的插件标准 CSS 变量（8 个）：**

```css
:root {
    --plugin-bg: #ffffff;          /* 卡片/面板背景 */
    --plugin-bg-soft: #f8fafc;     /* 次级背景/hover */
    --plugin-text: #1f2937;        /* 主文字 */
    --plugin-text-muted: #6b7280;  /* 次要文字 */
    --plugin-border: #e5e7eb;      /* 边框 */
    --plugin-primary: #4d6cfa;     /* 主色/链接 */
    --plugin-radius: 10px;         /* 圆角 */
    --plugin-shadow: 0 2px 8px rgba(0, 0, 0, 0.08); /* 阴影 */
}

[data-theme="dark"] {
    --plugin-bg: #1a2236;
    --plugin-bg-soft: #111a2f;
    --plugin-text: #f4f5fb;
    --plugin-text-muted: #96a0c1;
    --plugin-border: rgba(148, 160, 193, 0.25);
    --plugin-primary: #a8bbff;
    --plugin-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
}
```

主题可以将 `--plugin-*` 映射到自己的变量体系：

```css
:root {
    --plugin-bg: var(--my-theme-surface);
    --plugin-text: var(--my-theme-text);
    /* ... */
}
```

主题切换暗黑模式时，**必须**派发事件：

```javascript
window.dispatchEvent(new CustomEvent('noteblog:theme-change', { detail: { theme: 'dark' } }));
```

### 2.7 必需 CSS 类

主题必须实现以下类（用于核心功能和插件定位）：

`.container`, `.site-header`, `.site-main`, `.content-wrapper`, `.main-content`, `.sidebar`, `.posts-list`, `.post-item`, `.post-title`, `.post-meta`, `.post-excerpt`, `.post-detail`, `.post-footer`, `.comments-section`, `.comment-item`, `.site-footer`, `.back-to-top`

### 2.8 响应式要求

- 768px 以下：导航可折叠，内容单列
- 图片不溢出容器：`img { max-width: 100%; height: auto; }`
- 表格横向可滚动

### 2.9 调试检查表

- [ ] `theme.json` 元数据完整
- [ ] `base.html` 包含所有必需 block
- [ ] 所有 `plugin_hooks.*` 插槽已渲染
- [ ] 提供 `--plugin-*` CSS 变量（含暗黑模式）
- [ ] 移动端 375px 宽度下布局正常
- [ ] 图片和代码块不溢出容器

---

## 第三部分：插件开发

### 3.1 目录结构

```
plugins/your-plugin/
├── plugin.json             # 元数据
├── __init__.py             # 入口：create_plugin()
├── models.py               # 可选：数据模型
├── templates/
│   ├── admin.html          # 后台配置页
│   └── widget.html         # 前台组件
└── static/
    ├── css/plugin.css
    └── js/plugin.js
```

### 3.2 plugin.json

```json
{
  "name": "your_plugin",
  "display_name": "Your Plugin",
  "version": "1.0.0",
  "description": "插件描述",
  "author": "Your Name",
  "entry_point": "create_plugin",
  "min_version": "1.0.0",
  "config_schema": {
    "api_key": { "type": "string", "label": "API Key", "required": true }
  }
}
```

### 3.3 插件主类

```python
from app.services.plugin_manager import PluginBase, plugin_manager

class YourPlugin(PluginBase):
    def __init__(self):
        super().__init__()
        self.name = "your_plugin"
        self.version = "1.0.0"

    def register_hooks(self):
        # 注册模板插槽
        plugin_manager.register_template_hook(
            'sidebar_bottom', self.render_widget,
            priority=10, plugin_name=self.name
        )
        # 注册动作钩子
        plugin_manager.register_hook(
            'after_post_save', self.on_post_save,
            priority=10, plugin_name=self.name
        )

    def render_widget(self):
        return plugin_manager.render_plugin_template(
            'your_plugin/widget.html',
            data=self.get_data()
        )

    def on_post_save(self, **kwargs):
        post = kwargs.get('post')
        # 处理逻辑

def create_plugin():
    return YourPlugin()
```

### 3.4 钩子类型

#### 动作钩子（do_action）
触发时执行，无返回值。

| 钩子 | 触发点 |
|------|--------|
| `before_index_render` | 首页渲染前 |
| `before_post_save` / `after_post_save` | 文章保存前后 |
| `before_comment_save` / `after_comment_save` | 评论保存前后 |
| `after_user_login` / `after_user_register` | 用户登录/注册后 |

#### 过滤器（apply_filters）
可修改并返回数据。

| 过滤器 | 用途 |
|--------|------|
| `index_context` | 修改首页模板上下文 |
| `post_context` | 修改文章详情上下文 |
| `admin_post_editor_hooks` | 扩展编辑器 |

#### 模板插槽（register_template_hook）
返回 HTML 字符串，注入到页面指定位置。

可用插槽：`head_assets`, `scripts_assets`, `nav`, `content_top`, `content_bottom`, `sidebar_bottom`, `footer`, `post_meta`, `post_footer`, `comment_form_top`, `comment_form_bottom`

### 3.5 暗黑模式适配（必须遵守）

插件的 CSS **必须使用 `--plugin-*` 变量**，不得硬编码颜色值。

```css
/* 正确 */
.my-widget {
    background: var(--plugin-bg, #fff);
    color: var(--plugin-text, #333);
    border: 1px solid var(--plugin-border, #e5e7eb);
    border-radius: var(--plugin-radius, 8px);
    box-shadow: var(--plugin-shadow);
}

.my-widget-title {
    color: var(--plugin-primary, #4d6cfa);
}

.my-widget-desc {
    color: var(--plugin-text-muted, #6b7280);
}

/* 错误 — 不要这样做 */
.my-widget {
    background: #ffffff;
    color: #333333;
}
```

**规则：**
1. 所有背景色使用 `var(--plugin-bg)` 或 `var(--plugin-bg-soft)`
2. 所有文字色使用 `var(--plugin-text)` 或 `var(--plugin-text-muted)`
3. 边框使用 `var(--plugin-border)`
4. 强调色/链接使用 `var(--plugin-primary)`
5. 始终提供 fallback 值：`var(--plugin-bg, #fff)`
6. 按钮文字等固定白色可以硬编码 `#fff`

这样插件会自动跟随任何主题的暗黑模式切换，无需额外适配。

如果插件需要在 JS 中主动判断或监听暗黑模式，有三种标准方式：

**1. 读取 HTML 属性（推荐）**
```javascript
var isDark = document.documentElement.getAttribute('data-theme') === 'dark';
```

**2. CSS 选择器**
```css
[data-theme="dark"] .my-widget { /* 暗黑模式专属样式 */ }
```

**3. 监听切换事件**
```javascript
window.addEventListener('noteblog:theme-change', function(e) {
    var theme = e.detail.theme; // 'light' 或 'dark'
    // 更新插件状态
});
```

所有支持暗黑模式的主题在切换时都会派发 `noteblog:theme-change` 事件。

### 3.6 静态资源

- CSS/JS 放在 `plugins/your_plugin/static/` 下
- 访问路径：`/static/plugins/your_plugin/css/plugin.css`
- 在模板中引用：`url_for('plugin_static', plugin_name='your_plugin', filename='css/plugin.css')`

### 3.7 配置管理

```python
# 读取配置
config = self.get_config()
api_key = config.get('api_key', '')

# 保存配置
config['api_key'] = new_key
self.set_config(config)
```

### 3.8 数据库模型

插件可定义自己的 SQLAlchemy 模型：

```python
# plugins/your_plugin/models.py
from app import db

class YourModel(db.Model):
    __tablename__ = 'your_plugin_data'
    id = db.Column(db.Integer, primary_key=True)
    # ...
```

表会在插件首次加载时自动创建。

### 3.9 后台管理页面

通过 Blueprint 注册后台路由：

```python
from flask import Blueprint
bp = Blueprint('your_plugin', __name__,
               template_folder='templates',
               url_prefix='/admin/plugins/your_plugin')

@bp.route('/configure', methods=['GET', 'POST'])
def configure():
    # 配置逻辑
    pass
```

### 3.10 开发检查表

- [ ] `plugin.json` 元数据完整
- [ ] `create_plugin()` 入口函数存在
- [ ] 所有 CSS 使用 `--plugin-*` 变量
- [ ] 提供 fallback 值
- [ ] 在 serenity 主题暗黑模式下测试通过
- [ ] 移动端显示正常
- [ ] 无 JavaScript 错误

---

## 第四部分：部署

### 4.1 生产环境配置

```bash
# .env
SECRET_KEY=your-secret-key
DATABASE_URL=sqlite:///noteblog.db
UPLOAD_FOLDER=uploads
MAX_CONTENT_LENGTH=16777216
```

### 4.2 Gunicorn 启动

```bash
gunicorn -w 4 -b 127.0.0.1:5000 "app:create_app()"
```

### 4.3 Nginx 反向代理

```nginx
location / {
    proxy_pass http://127.0.0.1:5000;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_set_header X-Forwarded-Host $host;
}
```

### 4.4 数据库迁移

```bash
python run.py init          # 首次初始化
python run.py migrate       # 运行迁移
```

---

## 附录

### A. --plugin-* 变量速查表

| 变量 | 用途 | 浅色 | 暗色 |
|------|------|------|------|
| `--plugin-bg` | 面板背景 | `#ffffff` | `#1a2236` |
| `--plugin-bg-soft` | 次级背景 | `#f8fafc` | `#111a2f` |
| `--plugin-text` | 主文字 | `#1f2937` | `#f4f5fb` |
| `--plugin-text-muted` | 次要文字 | `#6b7280` | `#96a0c1` |
| `--plugin-border` | 边框 | `#e5e7eb` | `rgba(148,160,193,0.25)` |
| `--plugin-primary` | 主色 | `#4d6cfa` | `#a8bbff` |
| `--plugin-radius` | 圆角 | `10px` | `10px` |
| `--plugin-shadow` | 阴影 | `0 2px 8px rgba(0,0,0,0.08)` | `0 2px 8px rgba(0,0,0,0.3)` |

### B. 模板插槽一览

| 插槽名 | 位置 | 典型用途 |
|--------|------|----------|
| `head_assets` | `<head>` 内 | CSS、meta 标签 |
| `scripts_assets` | `</body>` 前 | JavaScript |
| `nav` | 导航栏 | 额外导航链接 |
| `content_top` | 主内容顶部 | 公告横幅 |
| `content_bottom` | 主内容底部 | 推荐内容 |
| `sidebar_bottom` | 侧边栏底部 | 小组件 |
| `post_meta` | 文章元信息 | 阅读时间、字数 |
| `post_footer` | 文章底部 | 点赞、分享 |
| `comment_form_top` | 评论表单上方 | 验证码 |
| `comment_form_bottom` | 评论表单下方 | 第三方登录 |
| `footer` | 页脚 | 备案信息 |

### C. 已有主题的暗黑模式支持

| 主题 | 暗黑模式 | 触发方式 | --plugin-* |
|------|----------|----------|------------|
| default | 无 | — | 仅浅色 |
| serenity | 有 | `[data-theme="dark"]` | 完整支持 |
| aurora | 有 | `[data-theme="dark"]` | 完整支持 |
| hoshizora | 有 | `[data-theme="dark"]` | 完整支持 |
| cyber_glitch | 无（本身暗色） | — | 仅暗色值 |
