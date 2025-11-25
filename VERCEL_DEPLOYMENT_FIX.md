# Vercel 部署修复说明

## 问题分析

原始错误：
```
sqlite3.OperationalError: unable to open database file
```

**根本原因：**
1. Vercel 是无服务器环境，文件系统是临时的
2. 数据库初始化时序问题
3. 数据库连接在请求间无法保持状态

## 修复方案

### 1. 数据库策略优化

**使用内存数据库：**
- 在 Vercel 环境中优先使用 `sqlite:///:memory:`
- 避免文件系统依赖问题
- 每个函数调用都有独立的数据库实例

**配置文件更新：**
```json
{
  "env": {
    "USE_MEMORY_DB": "true",
    "DATABASE_URL": "sqlite:///:memory:"
  }
}
```

### 2. 数据库初始化优化

**请求级别的初始化：**
- 使用 `@app.before_request` 钩子
- 在每个请求前检查数据库状态
- 全局变量跟踪初始化状态

**错误处理增强：**
- 所有数据库操作都包含 try-catch
- 失败时提供默认值
- 自动回滚机制

### 3. SettingManager 容错处理

**数据库连接失败时的降级策略：**
```python
@staticmethod
def get(key, default=None):
    try:
        setting = Setting.query.filter_by(key=key).first()
        if setting:
            return setting.get_typed_value()
        return default
    except Exception:
        # 如果数据库连接失败，返回默认值
        return default
```

## 部署步骤

### 1. 环境变量配置

在 Vercel 控制台设置以下环境变量：
```
FLASK_ENV=production
SKIP_PLUGIN_INIT=1
DATABASE_URL=sqlite:///:memory:
USE_MEMORY_DB=true
PYTHONPATH=/var/task
SECRET_KEY=your-secret-key-here
```

### 2. 部署命令

```bash
# 安装 Vercel CLI
npm install -g vercel

# 部署到 Vercel
vercel --prod
```

### 3. 验证部署

部署完成后，访问以下端点验证：
- `/` - 首页（应该显示默认设置）
- `/auth/login` - 登录页面
- `/admin` - 管理后台（使用 admin/admin123 登录）

## 重要注意事项

### 1. 数据持久性

**内存数据库限制：**
- 数据在函数调用间不持久化
- 每次冷启动都会重新初始化
- 适合演示和测试，不适合生产环境

**生产环境建议：**
- 使用外部数据库服务（如 Vercel Postgres）
- 或使用 Redis 等缓存服务
- 考虑使用 Vercel KV 存储关键配置

### 2. 性能优化

**冷启动优化：**
- 减少初始化时间
- 使用全局变量缓存状态
- 避免重复的数据库操作

**内存使用：**
- 监控内存使用情况
- 及时释放不需要的资源
- 考虑使用连接池

### 3. 安全考虑

**敏感信息：**
- 使用 Vercel 环境变量存储密钥
- 不要在代码中硬编码敏感信息
- 定期轮换密钥

**访问控制：**
- 启用 HTTPS
- 配置适当的 CORS 策略
- 实施速率限制

## 故障排除

### 常见问题

1. **数据库连接失败**
   - 检查环境变量设置
   - 确认使用内存数据库
   - 查看函数日志

2. **初始化失败**
   - 检查 `SKIP_PLUGIN_INIT` 设置
   - 确认所有依赖都已安装
   - 验证 Python 版本兼容性

3. **性能问题**
   - 监控冷启动时间
   - 检查内存使用情况
   - 优化数据库查询

### 调试技巧

1. **查看日志：**
   ```bash
   vercel logs
   ```

2. **本地测试：**
   ```bash
   # 设置环境变量
   export USE_MEMORY_DB=true
   export SKIP_PLUGIN_INIT=1
   
   # 运行应用
   python api/index.py
   ```

3. **监控指标：**
   - 函数执行时间
   - 内存使用量
   - 错误率

## 后续改进建议

1. **数据库迁移：**
   - 迁移到 Vercel Postgres
   - 实施数据备份策略
   - 添加数据库监控

2. **缓存策略：**
   - 使用 Vercel Edge Cache
   - 实施 Redis 缓存
   - 优化静态资源

3. **监控和告警：**
   - 集成 Vercel Analytics
   - 设置错误告警
   - 监控性能指标

4. **CI/CD 优化：**
   - 自动化测试流程
   - 分环境部署策略
   - 回滚机制
