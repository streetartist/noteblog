# Vercel 部署指南

## 概述
本指南将帮助您将 Noteblog 应用部署到 Vercel 平台。

## 前提条件
- 已安装 Vercel CLI: `npm i -g vercel`
- 已注册 Vercel 账户
- 准备好数据库（推荐使用 Vercel Postgres）

## 部署步骤

### 1. 安装 Vercel CLI
```bash
npm i -g vercel
```

### 2. 登录 Vercel
```bash
vercel login
```

### 3. 配置环境变量
在部署之前，需要在 Vercel 控制台中设置以下环境变量：

#### 必需的环境变量：
- `SECRET_KEY`: Flask 应用密钥，用于会话加密
- `DATABASE_URL`: 数据库连接字符串

#### 可选的环境变量：
- `FLASK_ENV`: 设置为 `production`
- `SKIP_PLUGIN_INIT`: 设置为 `0` 或 `1`

### 4. 部署应用
在项目根目录运行：
```bash
vercel
```

按照提示完成部署配置。

### 5. 更新环境变量
部署完成后，可以在 Vercel 控制台中更新环境变量：
1. 访问 [Vercel Dashboard](https://vercel.com/dashboard)
2. 选择您的项目
3. 进入 Settings > Environment Variables
4. 添加或更新环境变量

## 数据库配置

### 使用 SQLite（默认，推荐用于简单部署）
Noteblog 在 Vercel 上默认使用 SQLite 数据库，无需额外配置：
- 数据库文件路径：`sqlite:///tmp/noteblog.db`（临时目录）
- 适用于个人博客或小型网站
- 零配置，部署简单
- **注意**：在 serverless 环境中，如果文件系统权限受限，会自动切换到内存数据库

### 使用 Vercel Postgres（生产环境推荐）
对于生产环境或需要更高性能的场景：
1. 在 Vercel 控制台中创建 Postgres 数据库
2. 获取连接字符串
3. 将连接字符串设置为 `DATABASE_URL` 环境变量

### 使用其他数据库
确保数据库可以通过互联网访问，并提供正确的连接字符串。

## 注意事项

### Serverless 环境限制
- Vercel 使用 serverless 架构，应用会在不活动时休眠
- 首次访问可能会有冷启动延迟
- 文件系统写入可能受限，已配置为使用临时目录进行数据库操作
- SQLite 数据库文件存储在 `/tmp/` 目录下（serverless环境的可写区域）

### 修复的只读文件系统问题
✅ **已解决**：应用已针对 Vercel 的只读文件系统环境进行了优化
- 使用 `tempfile.gettempdir()` 作为实例路径
- SQLite 数据库存储在可写的临时目录中
- 避免了 `OSError: [Errno 30] Read-only file system` 错误

### 静态文件处理
- 主题静态文件通过 Flask 路由提供
- 上传的文件建议存储在云存储服务中

### 插件系统
- 插件初始化在 serverless 环境中可能需要特殊处理
- 可以通过设置 `SKIP_PLUGIN_INIT=1` 跳过插件初始化

## 故障排除

### 数据库连接问题
- 确保数据库连接字符串正确
- 检查数据库是否允许外部连接
- 验证数据库凭据

### 应用启动失败
- 检查环境变量是否正确设置
- 查看 Vercel 函数日志获取详细错误信息
- 确保所有依赖项都在 `requirements.txt` 中

### 性能问题
- 考虑使用数据库连接池
- 优化查询性能
- 使用 CDN 加速静态资源

## 更新部署
```bash
vercel --prod
```

## 回滚
在 Vercel 控制台中可以轻松回滚到之前的部署版本。

## 支持
如遇到问题，请查看 Vercel 官方文档或提交 issue 到项目仓库。
