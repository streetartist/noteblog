# Noteblog

一个基于Flask的现代化博客框架，具有极强的可扩展性和可自定义性。

## ✨ 特性

- 🚀 **现代化架构**: 基于Flask + SQLAlchemy + Vue.js构建
- 🔌 **插件系统**: 支持钩子函数、过滤器、模板插入点
- 🎨 **主题系统**: 支持多主题切换和自定义主题
- 👥 **用户管理**: 完整的用户认证和权限管理系统
- 📝 **博客功能**: 文章、分类、标签、评论等完整功能
- 🔍 **搜索功能**: 全文搜索和高级搜索
- 📱 **响应式设计**: 支持移动端和桌面端
- 🐳 **Docker支持**: 完整的Docker部署方案
- 🔒 **安全性**: 内置安全防护机制
- 📊 **统计分析**: 访问统计和数据分析

## 🏗️ 技术栈

### 后端
- **Flask**: Web框架
- **SQLAlchemy**: ORM数据库操作
- **Flask-Migrate**: 数据库迁移
- **Flask-Login**: 用户认证
- **Flask-WTF**: 表单处理
- **Alembic**: 数据库版本控制
- **Redis**: 缓存和会话存储

### 前端
- **Vue.js 3**: 前端框架
- **Element Plus**: UI组件库
- **Axios**: HTTP客户端
- **Webpack**: 构建工具

### 数据库
- **MySQL**: 主数据库（生产环境）
- **SQLite**: 开发数据库

### 部署
- **Docker**: 容器化部署
- **Nginx**: 反向代理和静态文件服务
- **Gunicorn**: WSGI服务器

## 🚀 快速开始

### 使用Docker Compose（推荐）

1. **克隆项目**
```bash
git clone https://github.com/your-username/noteblog.git
cd noteblog
```

2. **启动服务**
```bash
# 启动基础服务
docker-compose up -d

# 启动包含搜索功能的服务
docker-compose --profile search up -d
```

3. **初始化数据库**
```bash
# 进入应用容器
docker-compose exec noteblog bash

# 运行数据库迁移
flask db upgrade

# 创建管理员用户
python scripts/create_admin.py
```

4. **访问应用**
- 前端: http://localhost
- 管理后台: http://localhost/admin
- API文档: http://localhost/api/docs

### 本地开发环境

1. **安装依赖**
```bash
# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装Python依赖
pip install -r requirements.txt
```

2. **配置环境变量**
```bash
cp .env.example .env
# 编辑.env文件，配置数据库等信息
```

### 首次初始化注意事项

在首次在本地运行项目并创建数据库表时，可能会遇到插件或主题加载阶段访问数据库表尚未创建导致的错误。

- 现在你可以直接运行下面命令来初始化项目，`run.py init` 会在内部自动处理跳过插件/主题的加载以避免该问题：

```powershell
python run.py init
```

- 如果你在特殊环境下仍遇到相关错误，可以手动在 PowerShell 中临时设置环境变量再运行：

```powershell
#$env:SKIP_PLUGIN_INIT='1'; python run.py init
```

完成初始化后，再运行常规启动命令即可：

```powershell
python run.py run --host=127.0.0.1 --port=5000
```

上面步骤会创建 SQLite 数据库（默认 `noteblog.db`），并初始化默认设置与管理员账号（默认 admin/admin123）。

3. **初始化数据库**
```bash
flask db init
flask db migrate -m "Initial migration"
flask db upgrade
```

4. **启动开发服务器**
```bash
python app.py
```

## 📁 项目结构

```
noteblog/
├── app/                    # 应用核心代码
│   ├── __init__.py        # 应用工厂
│   ├── models/            # 数据模型
│   │   ├── user.py        # 用户模型
│   │   ├── post.py        # 文章模型
│   │   ├── comment.py     # 评论模型
│   │   ├── plugin.py      # 插件模型
│   │   ├── theme.py       # 主题模型
│   │   └── setting.py     # 设置模型
│   ├── views/             # 视图控制器
│   │   ├── main.py        # 主要视图
│   │   ├── auth.py        # 认证视图
│   │   ├── admin.py       # 管理后台
│   │   └── api.py         # API接口
│   └── services/          # 服务层
│       ├── plugin_manager.py    # 插件管理器
│       └── theme_manager.py     # 主题管理器
├── plugins/               # 插件目录
│   └── hello_world/      # 示例插件
├── themes/                # 主题目录
│   └── default/          # 默认主题
├── docker/               # Docker配置
│   ├── nginx/           # Nginx配置
│   └── mysql/           # MySQL配置
├── migrations/           # 数据库迁移文件
├── uploads/             # 上传文件目录
├── logs/                # 日志文件
├── requirements.txt     # Python依赖
├── docker-compose.yml   # Docker Compose配置
├── Dockerfile          # Docker镜像配置
└── README.md           # 项目文档
```

## 🔌 插件开发

### 创建插件

1. **创建插件目录**
```bash
mkdir plugins/my_plugin
cd plugins/my_plugin
```

2. **创建插件主文件**
```python
# __init__.py
from app.services.plugin_manager import PluginBase, hook, filter

class MyPlugin(PluginBase):
    def __init__(self):
        super().__init__()
        self.name = "my_plugin"
        self.version = "1.0.0"
    
    @hook('template_context')
    def add_context(self, context):
        context['my_variable'] = 'Hello from plugin!'
        return context
    
    @filter('post_content')
    def filter_content(self, content, post):
        return content.replace('Hello', 'Hi')

def create_plugin():
    return MyPlugin()
```

3. **创建插件配置文件**
```json
// plugin.json
{
    "name": "my_plugin",
    "version": "1.0.0",
    "description": "My custom plugin",
    "author": "Your Name",
    "entry_point": "create_plugin",
    "hooks": ["template_context"],
    "filters": ["post_content"]
}
```

### 插件钩子

可用的钩子包括：

- `before_request`: 请求前处理
- `after_request`: 请求后处理
- `template_context`: 模板上下文处理
- `admin_navigation`: 管理后台导航
- `user_registered`: 用户注册后
- `post_published`: 文章发布后

### 插件过滤器

可用的过滤器包括：

- `post_content`: 文章内容过滤
- `page_title`: 页面标题过滤
- `comment_content`: 评论内容过滤

## 🎨 主题开发

### 创建主题

1. **创建主题目录**
```bash
mkdir themes/my_theme
cd themes/my_theme
```

2. **创建主题配置**
```json
// theme.json
{
    "name": "my_theme",
    "version": "1.0.0",
    "description": "My custom theme",
    "author": "Your Name",
    "config_schema": {
        "color_scheme": {
            "type": "string",
            "default": "light",
            "options": ["light", "dark"]
        }
    }
}
```

3. **创建模板文件**
```html
<!-- templates/base.html -->
<!DOCTYPE html>
<html>
<head>
    <title>{{ page_title or site_title }}</title>
    <link rel="stylesheet" href="{{ url_for('static', filename='css/style.css') }}">
</head>
<body>
    <header>
        <h1>{{ site_title }}</h1>
    </header>
    
    <main>
        {% block content %}{% endblock %}
    </main>
    
    <footer>
        <p>&copy; 2024 {{ site_title }}</p>
    </footer>
</body>
</html>
```

## 📚 API文档

### 认证接口

```
POST /api/auth/login          # 用户登录
POST /api/auth/logout         # 用户登出
POST /api/auth/register       # 用户注册
GET  /api/auth/profile        # 获取用户信息
PUT  /api/auth/profile        # 更新用户信息
```

### 文章接口

```
GET    /api/posts             # 获取文章列表
GET    /api/posts/{id}        # 获取文章详情
POST   /api/posts             # 创建文章
PUT    /api/posts/{id}        # 更新文章
DELETE /api/posts/{id}        # 删除文章
```

### 评论接口

```
GET    /api/comments          # 获取评论列表
POST   /api/comments          # 创建评论
PUT    /api/comments/{id}     # 更新评论
DELETE /api/comments/{id}     # 删除评论
```

## 🔧 配置说明

### 环境变量

```bash
# 基本配置
FLASK_APP=app.py
FLASK_ENV=development
SECRET_KEY=your-secret-key

# 数据库配置
DATABASE_URL=mysql+pymysql://user:pass@localhost/noteblog

# Redis配置
REDIS_URL=redis://localhost:6379/0

# 邮件配置
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-password
```

### 系统设置

系统设置可以通过管理后台或直接修改数据库：

```sql
-- 更新网站标题
UPDATE setting SET value = 'My Blog' WHERE key_name = 'site_title';

-- 更新每页文章数量
UPDATE setting SET value = '15' WHERE key_name = 'posts_per_page';
```

## 🚀 部署指南

### 生产环境部署

1. **使用Docker Compose**
```bash
# 配置生产环境变量
cp .env.example .env.production
# 编辑.env.production文件

# 启动生产环境
docker-compose -f docker-compose.yml --env-file .env.production up -d
```

2. **配置SSL证书**
```bash
# 生成自签名证书（开发环境）
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout docker/ssl/key.pem \
    -out docker/ssl/cert.pem

# 使用Let's Encrypt（生产环境）
certbot certonly --webroot -w /var/www/html -d yourdomain.com
```

3. **配置Nginx**
编辑 `docker/nginx/conf.d/default.conf` 文件，配置域名和SSL。

### 性能优化

1. **数据库优化**
```sql
-- 添加索引
CREATE INDEX idx_post_published ON post(status, published_at);
CREATE INDEX idx_comment_post ON comment(post_id, status);
```

2. **缓存配置**
```python
# Redis缓存
CACHE_TYPE = 'redis'
CACHE_REDIS_URL = 'redis://localhost:6379/1'
```

3. **静态文件优化**
```nginx
# 启用Gzip压缩
gzip on;
gzip_types text/css application/javascript;

# 设置缓存头
location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
    expires 1y;
    add_header Cache-Control "public, immutable";
}
```

## 🤝 贡献指南

1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 🆘 支持

如果您遇到问题或有建议，请：

1. 查看 [FAQ](docs/FAQ.md)
2. 搜索 [Issues](https://github.com/your-username/noteblog/issues)
3. 创建新的 Issue
4. 联系维护者

## 🙏 致谢

感谢所有为这个项目做出贡献的开发者！

- [Flask](https://flask.palletsprojects.com/) - Web框架
- [Vue.js](https://vuejs.org/) - 前端框架
- [Element Plus](https://element-plus.org/) - UI组件库
- [SQLAlchemy](https://www.sqlalchemy.org/) - ORM框架

---

**Noteblog** - 让博客更简单，让开发更愉快！ 🚀
