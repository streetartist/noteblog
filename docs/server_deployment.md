# Noteblog 普通服务器部署指南

本文档提供在常规 Linux 服务器（如 Ubuntu 22.04、Debian 12、CentOS Stream 9 等）上部署 Noteblog 的示例流程，可根据自身环境调整命令与路径。

## 1. 环境准备

- 创建专用系统用户（示例 `noteblog`），限制其 sudo 权限。
- 安装基础组件：`git`、`python3.11+`、`python3-venv`、`build-essential`、`nginx`、`mysql-server`/`postgresql`（或 SQLite 仅作测试）、可选 `redis`、`certbot`。
- 开放 80/443 端口并限制其余端口；开启 `ufw`/`firewalld`。

```bash
sudo apt update && sudo apt install -y git python3.11 python3.11-venv python3-pip build-essential nginx mysql-server redis-server certbot
sudo useradd -m -s /bin/bash noteblog
sudo passwd noteblog
```

> 如果使用 PostgreSQL，请安装 `postgresql postgresql-contrib` 并创建数据库与账号。

## 2. 获取代码与安装依赖

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

## 3. 配置环境变量与服务依赖

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

## 4. 初始化数据库与基础数据

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

## 5. 启动 Noteblog 应用

### 5.1 临时启动

```bash
sudo -u noteblog bash <<'EOF'
cd /var/www/noteblog
source venv/bin/activate
gunicorn -w 4 -b 127.0.0.1:8000 run:app
EOF
```

### 5.2 Systemd 守护示例

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

## 6. Nginx 反向代理与静态文件

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

### HTTPS（推荐）

```bash
sudo certbot --nginx -d blog.example.com
```

Certbot 会自动写入 SSL 证书配置并设置定时续期。

## 7. 持久化与安全加固

- 保证 `/var/www/noteblog/instance/uploads`、`logs`、`migrations` 对运行用户可写。
- 数据库按需添加索引，例如：

```sql
CREATE INDEX idx_post_published ON post(status, published_at);
CREATE INDEX idx_comment_post ON comment(post_id, status);
```

- 启用 Fail2ban 或 Cloudflare 等防护；限制 SSH 登录；定期备份数据库与 `instance/uploads`。
- 每次升级：`git pull`、`pip install -r requirements.txt`、`flask db upgrade`、`sudo systemctl restart noteblog`。

## 8. 验证与运维

- 访问 `http(s)://blog.example.com/` 与 `/admin` 检查前台/后台。
- 查看日志：
  - 应用：`journalctl -u noteblog -f`
  - Nginx：`/var/log/nginx/access.log`、`error.log`
- 常见问题排查：
  - 数据库连不上：核对 `.env`、网络、权限。
  - 插件/主题导致启动失败：设置 `SKIP_PLUGIN_INIT=1`，启动后在后台逐个启用。
  - 静态资源 404：确认 Nginx `alias` 指向正确目录。

完成以上步骤，Noteblog 即可在普通服务器上稳定运行。若需要多实例或自动扩缩容，可进一步结合 Docker、Kubernetes 或 CI/CD 管道实现。

---

> **寻求 Docker 部署？**
> 
> 本项目同样提供了基于 Docker 和 Docker Compose 的一键部署方案，这是推荐用于生产环境的方式。
> 
> 请参阅：[**Noteblog Docker 部署指南](./docker_deployment.md)**
