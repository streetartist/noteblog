# Noteblog Docker 部署指南

本文档提供了使用 Docker 和 Docker Compose 部署 Noteblog 的标准流程。这是推荐用于生产环境的部署方式，因为它简化了环境配置和依赖管理。

## 1. 先决条件

- 已安装 [Docker](https://docs.docker.com/engine/install/)
- 已安装 [Docker Compose](https://docs.docker.com/compose/install/) (通常随 Docker Desktop 一起安装)
- `git` 用于克隆项目代码

## 2. 获取代码

克隆 Noteblog 项目到你的服务器：

```bash
git clone https://github.com/streetartist/noteblog.git
cd noteblog
```

## 3. 环境配置

Docker Compose 使用 `.env` 文件来管理环境变量。你需要创建并配置这个文件。

1.  **复制示例文件**:
    ```bash
    cp .env.example .env
    ```

2.  **编辑 `.env` 文件**:
    打开 `.env` 文件并根据你的环境修改以下关键变量：

    - `SECRET_KEY`: **必须修改**。运行以下命令生成一个安全的随机密钥，并将其粘贴到此处。
      ```bash
      openssl rand -hex 32
      ```
    - `DATABASE_URL`: 默认配置已链接到 Docker Compose 中的 MySQL 服务。**强烈建议**修改 `docker-compose.yml` 中 `db` 服务的 `MYSQL_ROOT_PASSWORD` 和 `MYSQL_PASSWORD` 的默认值，并在此处同步更新。
      ```
      # 示例 (如果修改了 docker-compose.yml 中的密码为 'your-strong-password')
      DATABASE_URL=mysql+pymysql://noteblog:your-strong-password@db:3306/noteblog
      ```
    - `REDIS_URL`: 默认配置已链接到 Redis 服务，通常无需修改。
    - `FLASK_ENV`: 保持 `production`。

## 4. 构建并启动服务

使用 Docker Compose 在后台构建并启动所有服务（Noteblog 应用, MySQL, Redis, Nginx）。

```bash
docker-compose up --build -d
```

- `--build`: 强制重新构建镜像，确保代码更改生效。
- `-d`: 在后台（detached mode）运行容器。

你可以使用 `docker-compose ps` 查看所有正在运行的服务状态。

## 5. 初始化应用

首次启动时，你需要执行初始化命令来创建数据库表和默认的管理员账户。

```bash
docker-compose exec noteblog python run.py init
```

- `docker-compose exec noteblog`: 在名为 `noteblog` 的服务容器内执行命令。
- `python run.py init`: 运行初始化脚本。

脚本会提示你设置管理员的用户名、邮箱和密码。

## 6. 访问你的博客

完成以上步骤后，你的 Noteblog 实例应该已经成功运行。

- **前台**: 访问 `http://<你的服务器IP或域名>`
- **后台**: 访问 `http://<你的服务器IP或域名>/admin`

## 7. Nginx 与 HTTPS (生产环境推荐)

`docker-compose.yml` 中的 Nginx 服务已配置为监听 80 和 443 端口。为了在生产环境中启用 HTTPS，请执行以下操作：

1.  **获取 SSL 证书**: 使用 Certbot 或其他方式为你的域名获取 SSL 证书 (`cert.pem`) 和私钥 (`key.pem`)。

2.  **放置证书**: 将你的证书和私钥文件放入 `docker/ssl/` 目录。如果该目录不存在，请创建它。

3.  **修改 Nginx 配置**:
    - 打开 `docker/nginx/conf.d/default.conf`。
    - 在 `server { listen 80; ... }` 块中，取消注释 `return 301 https://$server_name$request_uri;` 这一行，以强制将 HTTP 请求重定向到 HTTPS。
    - 将 `server_name` 从 `localhost` 修改为你的域名。
    - 在 `server { listen 443 ssl; ... }` 块中，同样将 `server_name` 修改为你的域名。

4.  **重启 Nginx 服务**:
    ```bash
    docker-compose restart nginx
    ```

## 8. 日常运维

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
