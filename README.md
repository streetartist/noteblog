# Noteblog

一个基于Flask的现代化博客框架，具有极强的可扩展性和可自定义性。

## ✨ 特性

- 🚀 **现代化架构**: 基于Flask + SQLAlchemy构建
- 🔌 **插件系统**: 支持钩子函数、过滤器、模板插入点
- 🎨 **主题系统**: 支持多主题切换和自定义主题
- 👥 **用户管理**: 完整的用户认证和权限管理系统
- 📝 **博客功能**: 文章、分类、标签、评论等完整功能
- 🔍 **搜索功能**: 全文搜索和高级搜索（To do）
- 📱 **响应式设计**: 支持移动端和桌面端
- 🐳 **Docker支持**: 完整的Docker部署方案
- 📊 **统计分析**: 访问统计和数据分析（To do）

## 🚀 安装与部署

### 方法一：使用 Docker Compose (推荐)

此方法是启动 Noteblog 最简单快捷的方式，同时适用于开发和生产环境。

#### 1. 先决条件

- 已安装 [Docker](https://docs.docker.com/engine/install/)
- 已安装 [Docker Compose](https://docs.docker.com/compose/install/) (通常随 Docker Desktop 一起安装)
- `git` 用于克隆项目代码

#### 2. 获取代码

克隆 Noteblog 项目到你的服务器：

```bash
git clone https://github.com/streetartist/noteblog.git
cd noteblog
```

#### 3. 构建并启动服务

使用 Docker Compose 在后台构建并启动所有服务（Noteblog 应用, MySQL, Redis, Nginx）。

```bash
docker-compose up --build -d
```

- `--build`: 强制重新构建镜像，确保代码更改生效。
- `-d`: 在后台（detached mode）运行容器。

你可以使用 `docker-compose ps` 查看所有正在运行的服务状态。

#### 4. 初始化应用

首次启动时，你需要执行初始化命令来创建数据库表和默认的管理员账户。

```bash
docker-compose exec noteblog python run.py init
```

- `docker-compose exec noteblog`: 在名为 `noteblog` 的服务容器内执行命令。
- `python run.py init`: 运行初始化脚本。

脚本会提示你设置管理员的用户名、邮箱和密码。

#### 5. 访问你的博客

完成以上步骤后，你的 Noteblog 实例应该已经成功运行。

- **前台**: 访问 `http://<你的服务器IP或域名>`
- **后台**: 访问 `http://<你的服务器IP或域名>/admin`

#### 8. Nginx 与 HTTPS (生产环境推荐)

`docker-compose.yml` 中的 Nginx 服务已配置为监听 80 和 443 端口。为了在生产环境中启用 HTTPS，请执行以下操作：

1.  **获取 SSL 证书**: 使用 Certbot 或其他方式为你的域名获取 SSL 证书 (`cert.pem`) 和私钥 (`key.pem`)。

2.  **放置证书**: 将你的证书和私钥文件放入 `docker/ssl/` 目录。如果该目录不存在，请创建它。

> 注意：如果 `docker/ssl/` 目录中**没有** `cert.pem` 或 `key.pem`，Nginx 将不会启用 HTTPS（容器启动不会因缺少证书而失败）。如果你之后添加了证书，请重启 Nginx 容器使其生效：

```bash
docker-compose restart nginx
```

3.  **修改 Nginx 配置**:
    - 打开 `docker/nginx/conf.d/default.conf`。
    - 在 `server { listen 80; ... }` 块中，取消注释 `return 301 https://$server_name$request_uri;` 这一行，以强制将 HTTP 请求重定向到 HTTPS。
    - 将 `server_name` 从 `localhost` 修改为你的域名。
    - 在 `server { listen 443 ssl; ... }` 块中，同样将 `server_name` 修改为你的域名。

4.  **重启 Nginx 服务**:
    ```bash
    docker-compose restart nginx
    ```

#### 8. 日常运维

- **查看日志**:
  ```bash
  # 查看所有服务的日志
  docker-compose logs -f

  # 查看特定服务的日志 (例如 noteblog 应用)
  docker-compose logs -f noteblog
  ```

- **停止服务**:
  ```bash
  docker-compose down
  ```

- **更新应用**:
  ```bash
  # 1. 拉取最新代码
  git pull

  # 2. 重新构建并重启服务
  docker-compose up --build -d

  # 3. (如果需要) 执行数据库迁移
  docker-compose exec noteblog flask db upgrade
  ```

- **数据备份**:
  所有持久化数据都存储在 Docker 卷或绑定挂载中：
  - **数据库**: `mysql_data` Docker 卷。
  - **Redis**: `redis_data` Docker 卷。
  - **上传文件**: `./uploads` 目录。
  - **插件/主题**: `./plugins` 和 `./themes` 目录。
  请定期备份这些数据。

### 方法二：本地**开发**环境 (不使用 Docker)

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

3. **启动开发服务器**
```bash
python run.py run
```

### 方法三：Vercel 部署

Noteblog 支持 Vercel 无服务器部署，具有自动扩缩容和全球 CDN 加速的优势。

#### 1. 创建 Vercel Postgres 数据库

1. 登录 [Vercel Dashboard](https://vercel.com/dashboard)
2. 选择您的项目
3. 进入 **Storage** 选项卡
4. 点击 **Create Database**
5. 选择 **Postgres** 数据库
6. 选择区域（建议选择离用户最近的区域）
7. 点击 **Create**

#### 2. 获取数据库连接信息

创建完成后，Vercel 会自动为您的项目设置环境变量

#### 3. 安装 Vercel CLI 并部署

```bash
# 安装 Vercel CLI
npm i -g vercel

# 部署应用
vercel --prod
```

#### 4. 配置应用环境变量

在 Vercel 项目设置中，添加以下环境变量：

```
DATABASE_URL = ${POSTGRES_URL}
SECRET_KEY = your-secret-key-here
FLASK_ENV = production
SKIP_PLUGIN_INIT = 1
PYTHONPATH = /var/task
```

**重要**：将 `DATABASE_URL` 设置为 `${POSTGRES_URL}`，这样它会自动使用 Vercel Postgres 的连接字符串。

#### 5. 更新依赖

确保您的 `requirements.txt` 包含 PostgreSQL 驱动：

```
psycopg2-binary
```

#### 6. 验证部署

- **检查数据库连接**:
  部署完成后，访问您的应用，查看函数日志确认数据库连接：
  ```bash
  vercel logs
  ```
  您应该看到类似以下的日志：
  ```
  使用环境变量中的数据库配置: postgres://***
  数据库表创建完成
  默认设置初始化成功
  管理员用户创建成功
  ```

- **测试数据持久化**:
  1. 访问 `/admin` 并使用 `admin/admin123` 登录
  2. 创建一些测试数据（文章、分类等）
  3. 等待几分钟让函数进入休眠状态
  4. 重新访问应用，确认数据仍然存在

#### 7. 数据库管理

- **查看数据库**:
  在 Vercel Dashboard 中：
  1. 进入 **Storage** 选项卡
  2. 点击您的 Postgres 数据库
  3. 使用内置的查询工具查看和管理数据

- **备份和恢复**:
  Vercel Postgres 自动提供：
  - 每日自动备份
  - 点位时间恢复（PITR）
  - 手动备份功能

- **连接限制**:
  免费计划的限制：
  - 60 个连接
  - 512MB 存储
  - 10GB 月度传输

  对于大多数博客应用来说，这些限制是足够的。

### 方法四：普通服务器部署

本文档提供在常规 Linux 服务器（如 Ubuntu 22.04、Debian 12、CentOS Stream 9 等）上部署 Noteblog 的示例流程，可根据自身环境调整命令与路径。

#### 1. 环境准备

- 创建专用系统用户（示例 `noteblog`），限制其 sudo 权限。
- 安装基础组件：`git`、`python3.11+`、`python3-venv`、`build-essential`、`nginx`、`mysql-server`/`postgresql`（或使用 SQLite 作为测试）、可选 `redis`、`certbot`。
- 开放 80/443 端口并限制其余端口；开启 `ufw`/`firewalld`。

```bash
sudo apt update && sudo apt install -y git python3.11 python3.11-venv python3-pip build-essential nginx mysql-server redis-server certbot
sudo useradd -m -s /bin/bash noteblog
sudo passwd noteblog
```

> 如果使用 PostgreSQL，请安装 `postgresql postgresql-contrib` 并创建数据库与账号。

#### 2. 获取代码与安装依赖

```bash
sudo mkdir -p /var/www
sudo chown noteblog:noteblog /var/www
sudo -u noteblog bash <<'EOF'
cd /var/www
git clone https://github.com/streetartist/noteblog.git
cd noteblog
python3.11 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
EOF
```

如需启用额外插件或主题，请确认其依赖已写入 `requirements.txt`，再重新执行 `pip install -r requirements.txt`。

#### 3. 配置环境变量与服务依赖

1. 复制示例配置：`cp .env.example .env`（或 `.env.production`）。
2. 按需填写：
   - `SECRET_KEY`：随机字符串。
   - `FLASK_ENV=production`、`SKIP_PLUGIN_INIT=1`。
   - 数据库连接字符串 `DATABASE_URL=mysql+pymysql://user:pass@127.0.0.1/noteblog`（或 PostgreSQL/SQLite）。
   - Redis：`REDIS_URL=redis://127.0.0.1:6379/0`（可选）。
3. 数据库准备：

```sql
CREATE DATABASE noteblog CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'noteblog'@'localhost' IDENTIFIED BY 'strong-pass';
GRANT ALL PRIVILEGES ON noteblog.* TO 'noteblog'@'localhost';
FLUSH PRIVILEGES;
```

#### 4. 初始化数据库与基础数据

```bash
sudo -u noteblog bash <<'EOF'
cd /var/www/noteblog
source venv/bin/activate
python run.py init   # 自动建库、迁移、创建默认管理员
EOF
```

后续数据模型更新可通过：

```bash
flask db migrate -m "add something"
flask db upgrade
```

#### 5. 启动 Noteblog 应用

##### 5.1 临时启动

```bash
sudo -u noteblog bash <<'EOF'
cd /var/www/noteblog
source venv/bin/activate
gunicorn -w 4 -b 127.0.0.1:8000 run:app
EOF
```

##### 5.2 Systemd 守护示例

创建 `/etc/systemd/system/noteblog.service`：

```
[Unit]
Description=Noteblog Service
After=network.target

[Service]
User=noteblog
Group=noteblog
WorkingDirectory=/var/www/noteblog
Environment="PATH=/var/www/noteblog/venv/bin"
EnvironmentFile=/var/www/noteblog/.env
ExecStart=/var/www/noteblog/venv/bin/gunicorn -w 4 -b 127.0.0.1:8000 run:app
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

加载并启动：

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now noteblog
sudo systemctl status noteblog
```

#### 6. Nginx 反向代理与静态文件

创建 `/etc/nginx/sites-available/noteblog`：

```
server {
    listen 80;
    server_name blog.example.com;

    client_max_body_size 32m;

    location /static/ {
        alias /var/www/noteblog/app/static/;
        access_log off;
        expires 7d;
        add_header Cache-Control "public";
    }

    location /uploads/ {
        alias /var/www/noteblog/instance/uploads/;
    }

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

启用站点并测试：

```bash
sudo ln -s /etc/nginx/sites-available/noteblog /etc/nginx/sites-enabled/noteblog
sudo nginx -t
sudo systemctl reload nginx
```

##### HTTPS（推荐）

```bash
sudo certbot --nginx -d blog.example.com
```

Certbot 会自动写入 SSL 证书配置并设置定时续期。

#### 7. 持久化与安全加固

- 保证 `/var/www/noteblog/instance/uploads`、`logs`、`migrations` 对运行用户可写。
- 数据库按需添加索引，例如：

```sql
CREATE INDEX idx_post_published ON post(status, published_at);
CREATE INDEX idx_comment_post ON comment(post_id, status);
```

- 启用 Fail2ban 或 Cloudflare 等防护；限制 SSH 登录；定期备份数据库与 `instance/uploads`。
- 每次升级：`git pull`、`pip install -r requirements.txt`、`flask db upgrade`、`sudo systemctl restart noteblog`。

#### 8. 验证与运维

- 访问 `http(s)://blog.example.com/` 与 `/admin` 检查前台/后台。
- 查看日志：
  - 应用：`journalctl -u noteblog -f`
  - Nginx：`/var/log/nginx/access.log`、`error.log`
- 常见问题排查：
  - 数据库连不上：核对 `.env`、网络、权限。
  - 插件/主题导致启动失败：设置 `SKIP_PLUGIN_INIT=1`，启动后在后台逐个启用。
  - 静态资源 404：确认 Nginx `alias` 指向正确目录。

完成以上步骤，Noteblog 即可在普通服务器上稳定运行。若需要多实例或自动扩缩容，可进一步结合 Docker、Kubernetes 或 CI/CD 管道实现。

## 🔧 配置说明

### 环境变量

```bash
# 基本配置
FLASK_APP=app.py
FLASK_ENV=development
SECRET_KEY=your-secret-key

# 数据库配置
DATABASE_URL=mysql+pymysql://user:pass@localhost/noteblog

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

## 📚 API文档

### 认证接口（Web 路由 /auth）

注意：项目中用于用户登录/注册/个人资料的是 Web 路由（`auth` 蓝图），不是以 `/api/auth` 为前缀的 JSON API。常用路由如下：

```
# Web 页面 / 表单
POST  /auth/login             # 用户登录（表单提交）
GET   /auth/logout            # 用户登出（重定向）
POST  /auth/register          # 用户注册（表单提交）
GET   /auth/profile           # 查看个人资料（页面，仅登录用户）
POST  /auth/profile/edit      # 编辑个人资料（表单提交，仅登录用户）

# RESTful API（JSON）
GET   /api/users/current      # 获取当前登录用户的 JSON 信息
GET   /api/users              # 获取用户列表（需要管理员权限）
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
├── requirements.txt     # Python依赖
├── docker-compose.yml   # Docker Compose配置
├── Dockerfile          # Docker镜像配置
└── README.md           # 项目文档
```

## 🏗️ 技术栈

### 后端
- **Flask**: Web框架
- **SQLAlchemy**: ORM数据库操作
- **Flask-Migrate**: 数据库迁移
- **Flask-Login**: 用户认证
- **Flask-WTF**: 表单处理
- **Alembic**: 数据库版本控制

### 前端
- **Jinja2**: 模板引擎，用于服务器端渲染

### 数据库
- **MySQL**: 主数据库（生产环境）
- **PostgreSQL**: 支持的生产数据库
- **SQLite**: 开发数据库

### 部署
- **Docker**: 容器化部署
- **Nginx**: 反向代理和静态文件服务
- **Gunicorn**: WSGI服务器

## 🔌 插件开发

### 体系速览

- 插件记录使用 `app/models/plugin.py` 中的 `Plugin`、`PluginHook` 模型，支持启用/停用、版本约束与配置存储。
- `plugin_manager` 负责：发现插件、动态导入 `plugins/<name>/__init__.py`、调用 `PluginBase` 生命周期、注册钩子/过滤器/模板插槽、自动挂载 Blueprint。
- 插件可以向三类钩子注册：动作(`register_hook` → `do_action`)、过滤器(`register_filter` → `apply_filters`) 和模板插槽(`register_template_hook` → `plugin_hooks.*`)。

### 目录示例

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

### `plugin.json` 字段

- **必填**：`name`, `display_name`, `version`, `description`, `author`。`install_path` 由系统推断。

- **可选**：`entry_point` （如 `create_plugin`）可用于约定插件工厂函数，但并非必须 — 插件管理器会导入插件模块并尝试加载模块中定义的插件类（建议继承 `PluginBase`）。
- **可选**:
  - `blueprints`: `[{"name": "reading_time_bp", "url_prefix": "/reading-time"}]`，供后台展示路由信息。
  - `config_schema`: 与主题类似，用于后台渲染配置项。
  - `hooks` / `filters`: 仅用于文档化；真正的注册在代码里完成。
  - `requirements`: 列出额外 Python 依赖，便于部署时安装。
  - `permissions`: 需额外授予的后台权限。
  - `templates`, `assets`, `database`: 用于说明所需模板或数据表（详见 `plugins/ai_summary/plugin.json`）。

### 插件主类与入口

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
- `PluginManager._load_plugin` 的行为：插件管理器会导入 `plugins/<name>/__init__.py` 模块并在模块中查找插件类（通常继承 `PluginBase`）并实例化它；模块中定义的 Blueprint 也会被自动注册。

  说明：历史上很多插件生态约定 `create_plugin()` 作为工厂函数，仓库中示例插件也可能包含 `create_plugin()`，这并不会影响插件加载 —— 目前加载器会优先寻找可实例化的类并直接实例化它。为了兼容性，建议：

  - 模块导出一个明确的插件类（继承 `PluginBase`）并在模块顶部定义它；或在模块导入时以显式方式完成钩子/过滤器注册。
  - 使用 `PluginBase.get_config()` 获取插件配置（返回 dict），修改配置后使用 `PluginBase.set_config(dict)` 一次性保存完整 dict；不要调用 `get_config(key)` 或 `set_config(key, value)` 之类单键签名（当前 `PluginBase` 接口以 dict 为单位读写配置）。
- 若需要安装时初始化数据，可实现 `install()`；停用/卸载时可扩展 `deactivate()` / `uninstall()`，处理清理逻辑。

### 常用钩子清单（源自 `app/views/*.py`）

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

### Blueprint、模板与静态资源

- 在插件模块中定义 `Blueprint` 对象（如 `hello_world_bp = Blueprint('hello_world', __name__, template_folder='templates', static_folder='static', url_prefix='/hello-world')`），Plugin Manager 会自动扫描并 `register_blueprint`。
- 插件模板默认位于 `plugins/<name>/templates/`。如果需要从钩子中渲染 HTML，可直接使用 `render_template()`，Flask 会正确解析插件模板目录。
- 静态文件可通过 `/static/plugins/<plugin_name>/<path>` 访问，或在模板中使用 `url_for('static', filename='plugins/<plugin_name>/css/plugin.css')`。

### 配置、数据与依赖

- `PluginBase.get_config()` / `set_config(dict)` 用于持久化 JSON。通常模式：`config = self.get_config(); config['message'] = '...'; self.set_config(config)`。
- 需要数据库表时，可将 SQLAlchemy 模型放在 `plugins/<name>/models.py`，并在 `plugin.json` 的 `database.models` 中声明，便于迁移脚本识别。复杂场景可直接编写 Alembic 脚本并在 `install()` 中调用。
- 若插件依赖第三方包，请在 `plugin.json` 的 `requirements` 列出，并在仓库 `requirements.txt` 或私有安装脚本中同步。

### 调试与发布检查表

- 初次开发可利用 `scripts/test_plugin_discovery.py`, `scripts/test_admin_plugins.py`, `scripts/test_admin_page.py` 检验插件注册、后台 UI 可用性。
- 后台 -> 插件管理 中的日志输出是排错首选；若钩子未执行，确认插件处于已启用状态且 `register_hooks()` 已被调用。
- **发布前自查**:
  - [ ] `plugin.json` 填写版本、入口、依赖与钩子声明
  - [ ] 插件以 `create_plugin()` 或导出的插件类提供实例均可，但推荐导出继承自 `PluginBase` 的类并在 `register_hooks()` 中完成钩子注册。
  - [ ] 所有 Blueprint `url_prefix` 不与核心路由冲突
  - [ ] 模板钩子输出使用 `|safe`，避免双重转义
  - [ ] 如涉及外网 API（如 `plugins/ai_summary`），提供可配置的 `endpoint` 与超时处理

## 🎨 主题开发

### 目录结构（推荐）

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

### `theme.json` 要点

- **基本字段**: `display_name`, `description`, `version`, `author`, `min_version`。
- **`config_schema`**: 遵循 JSON Schema 的简化结构，字段名尽量沿用 `themes/default`，以便后台自动生成设置表单（如 `logo`, `primary_color`, `show_sidebar`）。
- **`custom_pages`**: `[{"route": "/timeline", "template": "pages/timeline.html", "methods": ["GET"], "context": {"title": "时间线"}}]`，用于声明无需写 Python 的静态路由。
- **`assets.version`** 或自定义字段可帮助做静态资源 cache busting。

### 模板规范

- **`templates/base.html` 必须声明以下 Jinja block**: `title`, `description`, `keywords`, `head`, `content`, `sidebar`, `scripts`。若主题提供顶部/底部插槽，可通过 block `content_top`, `content_bottom` 再嵌套。
- **详情页 `post.html` 需包含评论表单与列表**，并保留 `.comments-section`, `.comments-list`, `.comment-item` 等类，便于插件追加功能（如验证码、第三方评论）。
- **模板中通过 `plugin_hooks` 注入插件内容**，常见插槽：`head_assets`, `scripts_assets`, `nav`, `content_top`, `content_bottom`, `sidebar_bottom`, `post_meta`, `post_footer`, `comment_form_top`, `comment_form_bottom`, `footer`。遍历时务必加 `|safe` 输出。
- **必需 CSS 类最小集**（用于核心 DOM 与插件定位）：`.container`, `.site-header`, `.site-main`, `.content-wrapper`, `.main-content`, `.with-sidebar`, `.sidebar`, `.posts-list`, `.post-item`, `.post-title`, `.post-meta`, `.post-excerpt`, `.post-detail`, `.post-footer`, `.comments-section`, `.comment-item`, `.comment-reply-form`, `.site-footer`, `.back-to-top`。

### 模板上下文

- **基础变量**: `site_title`, `site_description`, `current_user`, `recent_posts`, `categories`, `tags`, `get_theme_config()`, `plugin_hooks`。
- **若主题自带 Blueprint（`extensions.py`）**，请使用 `theme_manager.render_template()` 渲染，以确保自定义页面仍可拿到当前主题上下文与 Hooks。

### 主题回退机制

Noteblog 现在支持主题回退机制。当当前激活的主题缺少某个页面模板时，系统会自动回退到 `default` 主题使用对应的模板。

#### 工作原理

1.  **模板查找顺序**：
    - 首先在当前激活的主题中查找请求的模板
    - 如果找不到，则自动在 `default` 主题中查找
    - 如果 `default` 主题中也没有，则返回模板未找到的错误

2.  **回退条件**：
    - 当前主题不是 `default` 主题
    - 当前主题中不存在请求的模板文件
    - `default` 主题中存在对应的模板文件

3.  **日志记录**：
    - 当发生回退时，系统会在日志中记录信息
    - 格式：`主题 {theme_name} 缺少模板 {template_name}，回退到default主题`

#### 使用场景

- **自定义主题开发**: 开发者可以创建只包含部分模板的自定义主题，其他页面自动使用 `default` 主题的模板。
- **主题兼容性**: 当新版本 Noteblog 添加新的页面时，旧版本的主题仍然可以正常工作，通过回退机制使用 `default` 主题的新模板。
- **渐进式主题定制**: 用户可以逐步替换 `default` 主题的模板，而不需要一次性创建所有模板文件。

### 可选扩展

- **自定义路由**: 在 `extensions.py` 中定义 Flask Blueprint 并返回，Theme Manager 会在主题激活时自动注册。视图内部可继续使用 `plugin_manager`、`theme_manager` 提供的工具。
- **多语言/文案**: 避免写死中文/英文，尽量通过配置或后端传参控制。日期格式化可调用 `moment`/`datetime` helpers，或在模板中用 `post.created_at.strftime()`。
- **静态资源**: 推荐用构建工具输出到 `static/`，并在 `theme.json` 中声明版本；CDN 资源应提供本地 fallback，以便离线部署。

### 调试与发布检查表

- `scripts/test_template_render.py`, `scripts/test_admin_page.py` 等脚本可快速检验模板是否能被渲染；`THEME_FALLBACK_FEATURE.md` 解释了回退策略。
- **发布前自查**:
  - [ ] `theme.json` 填写元数据与 `config_schema`
  - [ ] `base.html` 具备所有核心 block
  - [ ] `plugin_hooks.*` 插槽全部保留并渲染 `|safe`
  - [ ] `.comments-*` 等约定类存在
  - [ ] 移动端宽度 < 768px 下布局正常，菜单可聚焦
  - [ ] Markdown 样式、代码块与图片不溢出容器
  - [ ] 若声明 `custom_pages` 或 Blueprint，均已测试 404/500 行为

## 🤝 贡献指南

1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开 Pull Request

## 🆘 支持

如果您遇到问题或有建议，请：

1. 搜索 [Issues]
3. 创建新的 Issue
4. 联系维护者

## 🙏 致谢

感谢所有为这个项目做出贡献的开发者！

## 📄 许可证

本项目采用 GPL-3.0 License 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

---

**Noteblog** - 让博客更简单，让开发更愉快！ 🚀
