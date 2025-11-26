**Noteblog 主题开发指南（简体中文）**

简介
-
此文档面向为 Noteblog 开发主题的前端开发者。目标是定义一套最小化的规范，保证主题与 Noteblog 核心、插件、以及后台自定义功能兼容。

一、目录结构（推荐）
- themes/<your-theme>/
  - theme.json              # 主题元信息与配置 schema
  - templates/
    - base.html             # 全局骨架（必须）
    - index.html            # 首页/文章列表（推荐）
    - post.html             # 文章详情（必须支持评论）
    - archives.html
    - categories.html
    - tags.html
    - search.html
  - static/
    - css/
      - style.css           # 主要样式（必须包含规范类）
      - markdown.css        # Markdown 渲染样式（建议）
    - js/
      - app.js
  - screenshot.png          # 主题预览图

二、`theme.json` 要点
- 基本字段：`display_name`, `description`, `version`, `author`, `min_noteblog_version`。
- `config_schema`：用于主题设置（logo, favicon, primary_color, show_sidebar 等），请使用与默认主题一致的字段名以便管理后台自动生成配置界面。

三、必须实现的 CSS 类（最小集）
- `.container`、`.site-header`、`.site-main`、`.content-wrapper`、`.main-content`、`.with-sidebar`、`.sidebar`、`.posts-list`、`.post-item`、`.post-content`、`.post-title`、`.post-meta`、`.post-excerpt`、`.post-tags`、`.post-detail`、`.post-footer`、`.comments-section`、`.comments-list`、`.comment-item`、`.comment-reply`、`.site-footer`、`.back-to-top`

说明：这些类用于核心模板（默认主题已实现）。插件或内置功能会期待这些类存在以便插入 DOM、绑定行为或应用样式。

四、模板钩子与 Jinja2 blocks（建议/必须）
- Jinja block（必须在 `base.html` 中支持）：
  - `title`：页面标题
  - `description`：meta description
  - `keywords`：meta keywords
  - `head`：允许子模板或插件在 <head> 注入额外标签
  - `content`：主内容区
  - `sidebar`：侧边栏默认内容块（可被子模板覆盖）
  - `scripts`：页面尾部脚本插入点
- 插件钩子（在模板上下文中以 `plugin_hooks` 暴露，类型为字典）：
  - `head_assets`：在 <head> 中插入 CSS/Meta 等
  - `scripts_assets`：在 body 结束前插入 JS
  - `sidebar_bottom`：侧边栏底部
  - `post_meta`：单篇文章元信息位置（推荐在 `.post-meta` 之后）
  - `post_footer`：文章操作区之后
  - `comment_form_top` / `comment_form_bottom`：用于在评论表单上下插入额外内容（验证码、第三方评论、插件UI）

五、可访问的全局模板变量（示例）
- `site_title`, `site_description`, `current_user`, `get_theme_config()`, `recent_posts`, `categories`, `tags`, `plugin_hooks`。

六、无障碍与响应式
- 确保导航可聚焦、按钮可通过键盘操作、图像 `alt` 属性可用。
- 在小屏幕（<=768px）下，主内容应垂直堆叠，侧边栏在底部。

七、国际化与日期格式
- 模板不要硬编码语言字符串，尽量使用后端传入的文本或可配置项以便翻译。

八、性能建议
- 静态资源尽量版本化与压缩（尤其样式与脚本）。
- 若使用外部库（如 Element Plus、KaTeX），建议通过 CDN 或按需加载。

九、检查表（发布前）
- [ ] `theme.json` 包含必要字段
- [ ] `base.html` 声明了 `title/head/content/scripts/sidebar` 等 block
- [ ] 页面在移动端可正常展示（菜单/侧边栏/分页）
- [ ] Markdown 内容样式（`markdown.css`）覆盖良好，代码块/表格/图片不溢出
- [ ] 评论表单/列表的类存在并样式可用
- [ ] 插件钩子（`plugin_hooks.*`）已在合适位置调用或提供占位

十、示例：在模板中渲染插件钩子
```
{% raw %}{% if plugin_hooks and plugin_hooks.post_meta %}
  {% for content in plugin_hooks.post_meta %}
    {{ content|safe }}
  {% endfor %}
{% endif %}{% endraw %}
```

结语
- 本指南覆盖了主题开发的大部分常见需求。根据站点特性你可以在此基础上扩展更多可选的钩子与配置项。如需我将此规范生成一个可验证的 lint 检查脚本，也可以继续协助实现。
