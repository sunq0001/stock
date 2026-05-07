# 股票数据可视化项目

上证交易所市场数据平台。爬虫采集 → InfluxDB 存储 → Flask API 查询 → ECharts 前端展示。

## 快速启动

```bash
# 1. 启动本地 InfluxDB
docker compose -f docker-compose.local.yml up -d influxdb

# 2. 设置环境变量并启动 API
$env:INFLUXDB_URL="http://localhost:18086"
$env:INFLUXDB_TOKEN="my-super-secret-token"
$env:INFLUXDB_ORG="stock"
$env:INFLUXDB_BUCKET="market_data"
$env:PORT="5000"
python pe_data_service_influxdb.py

# 3. 访问 http://localhost:18082/
```

## 文档

详细文档统一放在 [`docs/`](docs/) 目录：

| 文档 | 说明 |
|------|------|
| [`docs/README.md`](docs/README.md) | 文档目录索引 |
| [`docs/CLAUDE.md`](docs/CLAUDE.md) | AI 项目说明书（设计原则、规范、速查） |
| [`docs/01-architecture.md`](docs/01-architecture.md) | 系统架构设计 |
| [`docs/02-development.md`](docs/02-development.md) | 本地开发指南 |
| [`docs/03-deployment.md`](docs/03-deployment.md) | 部署指南 |
| [`docs/04-api-reference.md`](docs/04-api-reference.md) | API 接口文档 |
| [`docs/05-database-schema.md`](docs/05-database-schema.md) | 数据库 Schema |
| [`docs/SSE_API_DOC.md`](docs/SSE_API_DOC.md) | SSE 原始 API 参考 |

## 项目结构

```
├── pe_data_service_influxdb.py   # Flask API
├── sse_market_data_crawler.py    # SSE大盘爬虫
├── data_collector.py             # 个股数据采集
├── html/market.html              # 前端页面
├── nginx/default.conf            # Nginx 配置
├── docker-compose.local.yml      # 本地部署
├── docker-compose.production.yml # 生产部署
├── Dockerfile.web                # 容器镜像
└── docs/                         # 全部文档
```
