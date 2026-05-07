# 本地开发指南

## 一、环境准备

### 1.1 Python 环境

```bash
# 创建虚拟环境（推荐）
python -m venv venv

# 激活
# Windows PowerShell:
.\venv\Scripts\Activate.ps1
# Windows CMD:
.\venv\Scripts\activate.bat
# Linux/Mac:
source venv/bin/activate

# 安装依赖（使用国内镜像）
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple --trusted-host pypi.tuna.tsinghua.edu.cn
```

### 1.2 外部依赖

- **InfluxDB 2.x**：本地开发用 Docker 启动（见下方）
- **akshare**：用于分红配股数据采集（`pip install akshare`）
- **Node.js / npm**：不需要，前端纯静态 HTML

## 二、启动服务

### 2.1 启动 InfluxDB（Docker）

```bash
# 启动 InfluxDB 容器
docker run -d --name stock-influxdb ^
  -p 18086:8086 ^
  -e DOCKER_INFLUXDB_INIT_MODE=setup ^
  -e DOCKER_INFLUXDB_INIT_USERNAME=admin ^
  -e DOCKER_INFLUXDB_INIT_PASSWORD=admin123 ^
  -e DOCKER_INFLUXDB_INIT_ORG=stock ^
  -e DOCKER_INFLUXDB_INIT_BUCKET=market_data ^
  -e DOCKER_INFLUXDB_INIT_ADMIN_TOKEN=my-super-secret-token ^
  influxdb:2.7

# 或使用 docker-compose
docker compose -f docker-compose.local.yml up -d influxdb
```

### 2.2 启动 Flask API 服务

```bash
# 设置环境变量
$env:INFLUXDB_URL="http://localhost:18086"
$env:INFLUXDB_TOKEN="my-super-secret-token"
$env:INFLUXDB_ORG="stock"
$env:INFLUXDB_BUCKET="market_data"
$env:PORT="5000"

# 启动
python pe_data_service_influxdb.py
```

### 2.3 启动 Nginx + 完整服务（Docker Compose）

```bash
# 构建并启动所有服务
docker compose -f docker-compose.local.yml up -d --build

# 查看日志
docker compose -f docker-compose.local.yml logs -f

# 停止
docker compose -f docker-compose.local.yml down
```

### 2.4 访问地址

| 服务 | 地址 |
|------|------|
| 前端页面 | http://localhost:18080/market.html |
| API 直连 | http://localhost:18082/api/market/pe/history |
| InfluxDB 管理 | http://localhost:18086 |
| 健康检查 | http://localhost:18082/api/health |

## 三、数据采集（备用）

> 通常情况下 InfluxDB 中已有数据，以下仅当需要从零采集时使用。

### 3.1 采集大盘数据

```bash
# 采集一天
python sse_market_data_crawler.py --date 2026-05-06

# 采集一段时间
python sse_market_data_crawler.py --start 2021-12-20 --end 2021-12-26
```

### 3.2 采集个股数据

```bash
python data_collector.py
```

## 四、开发规范与注意事项

### 4.1 代码修改后的验证流程

```
改代码 → 确认语法无误 → 启动Flask服务 → 浏览器验证 → git commit
```

**不要**：
- 每次都重新 build Docker，开发时直接 `python pe_data_service_influxdb.py` 运行
- 直接在生产环境改代码测试

### 4.2 前端开发

前端（`html/market.html`）是纯静态文件，修改后直接刷新浏览器即可。

**API_BASE 切换**：
```javascript
// 第 634 行
const API_BASE = '/api';                              // 生产（Nginx代理）
// const API_BASE = 'http://localhost:5000/api';      // 本地开发直连 Flask
```

### 4.3 Docker 热重载

`docker-compose.local.yml` 中 `pe_data_service_influxdb.py` 通过 volume 挂载，修改后自动生效。

### 4.4 常见问题

**Flask 启动报端口占用**：
```bash
# 查看谁占了端口
netstat -ano | findstr :5000
# 杀掉进程
taskkill /PID <PID> /F
```

**InfluxDB 连不上**：
```bash
# 检查容器是否运行
docker ps | findstr influxdb
# 检查 URL/Token 是否正确
curl http://localhost:18086/health
```

**akshare 报错**：
- 确保 Python 版本 ≤ 3.11（akshare 对 3.12+ 支持有限）
- 使用国内镜像重装：`pip install akshare --upgrade`
