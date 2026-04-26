# Docker Compose 启动指南

## 项目结构

本项目使用 Docker Compose 启动完整的服务栈：

- **web服务** (端口 5000): Flask后端服务，提供API接口
- **nginx服务** (端口 8080): 反向代理，提供前端页面和API代理

## 快速启动

### 1. 使用 Docker Compose 启动

```bash
# 启动服务（后台运行）
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down
```

### 2. 访问服务

- **前端页面**: http://localhost:8080/stock.html
- **API健康检查**: http://localhost:8080/api/health
- **大盘PE数据**: http://localhost:8080/api/market/pe
- **股票搜索**: http://localhost:8080/api/search?q=茅台
- **股票K线**: http://localhost:8080/api/stock/600519

### 3. 测试服务

```bash
# 运行测试脚本
python test_extended_service.py
```

## 服务架构

### nginx配置
nginx作为反向代理，配置在 `nginx/conf.d/default.conf`:
- 前端页面: `/` → 静态文件服务
- API接口: `/api/` → 代理到 `http://web:5000`

### web服务配置
Flask后端服务，使用扩展的 `pe_data_service_extended.py`:
- 支持大盘PE数据（从远程API获取）
- 支持个股搜索和K线数据（通过neoData API）
- 支持分红和配股数据（模拟数据）

## 环境变量

### web服务环境变量
- `DATA_SOURCE`: 数据源模式 (`remote_api` 或 `local_db`)
- `REMOTE_API_URL`: 远程大盘PE API地址
- `PORT`: 服务端口 (默认: 5000)
- `NEODATA_QUERY_SCRIPT`: neoData查询脚本路径

### neoData配置
neoData token存储在 `neodata_token.txt` 文件中，用于访问金融数据API。

## 故障排除

### 1. 服务启动失败
```bash
# 检查Docker是否运行
docker version

# 检查docker-compose配置
docker-compose config

# 重新构建镜像
docker-compose build --no-cache
```

### 2. 个股搜索功能异常
- 检查 `neodata_token.txt` 文件是否存在且有效
- 检查网络连接，确保可以访问 `https://copilot.tencent.com`
- 查看web服务日志: `docker-compose logs web`

### 3. 前端页面无法访问
- 检查nginx服务是否运行: `docker-compose ps`
- 检查端口是否被占用: `netstat -ano | findstr :8080`
- 查看nginx日志: `docker-compose logs nginx`

## 开发说明

### 本地开发（不使用Docker）
```bash
# 设置环境变量
set DATA_SOURCE=remote_api
set PORT=5000

# 安装依赖
pip install -r requirements.txt

# 启动服务
python pe_data_service_extended.py
```

### 更新代码后
```bash
# 重新构建并启动
docker-compose up -d --build
```

## API接口文档

### 大盘数据
- `GET /api/market/pe` - 获取上证PE历史数据
- `GET /api/market/pe/latest` - 获取最新PE数据

### 个股数据
- `GET /api/search?q={query}` - 搜索股票
- `GET /api/stock/{code}` - 获取股票K线数据
- `GET /api/dividend/{code}` - 获取分红数据
- `GET /api/allotment/{code}` - 获取配股数据

### 系统状态
- `GET /api/health` - 健康检查