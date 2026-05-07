# 股票数据可视化项目

> 位置：`docs/CLAUDE.md`（AI 项目说明书，首次对话自动加载了解项目）

## 项目概述

上证交易所市场数据可视化平台。爬虫采集大盘指标、个股K线、分红配股数据存入 InfluxDB，Flask API 查询后通过 ECharts 前端展示。

## 技术栈

- **后端**：Python Flask + Flask-CORS
- **数据库**：InfluxDB 2.x（时序数据库），Flux 查询语言
- **前端**：纯静态 HTML + ECharts 5.x，无框架
- **代理**：Nginx 反向代理
- **部署**：Docker Compose + Ansible

## 设计原则

### 1. 数据源统一（高内聚）

```
外部API → 爬虫采集 → InfluxDB → API查询 → 前端展示
```

**所有数据必须存储在 InfluxDB。禁止前端或后端实时调外部API。**

当前数据层：

| 数据种类 | 存储位置 | 采集方式 |
|---------|---------|---------|
| 大盘指标 (PE/换手率/市值) | InfluxDB `sse_market` | `sse_market_data_crawler.py` → SSE官网 |
| 个股K线（前复权） | 腾讯API实时查询（待迁移到 InfluxDB） | `pe_data_service_influxdb.py` 直接调腾讯API |
| 分红配股 | akshare实时查询（待迁移到 InfluxDB） | `pe_data_service_influxdb.py` 直接调 akshare |

> ⚠️ 个股K线和分红配股目前还是实时调用外部API，属于过渡状态。后续应统一写入 InfluxDB。

### 2. 低耦合

- 爬虫、API、前端三个模块独立，通过 InfluxDB 连接
- 修改前端不涉及后端，修改后端不涉及爬虫
- 前端不直接感知数据来源（API 还是数据库），只通过 `/api/` 获取 JSON
- 容器间通过网络通信，不共享文件系统

### 3. 代码与数据分离

- Docker 镜像只打包代码，不包含数据库
- InfluxDB 数据通过 Volume 持久化
- 容器销毁不丢数据，重建容器不丢数据

### 4. 端口规范（固定不变）

| 服务 | 容器内端口 | 本地映射 | 生产映射 |
|------|-----------|---------|---------|
| Nginx | 80 | 18080 | 8080 |
| Flask API | 5000 | 18082 | 8082 |
| InfluxDB | 8086 | 18086 | 8086 |

**不要在代码或配置中硬编码宿主端口。** 容器内统一用服务名（`web:5000`、`influxdb:8086`）通信。

### 5. 本地 ↔ 服务器一致性

同一份代码、两套 compose 文件（端口不同），启动时自动判断数据库状态，缺数据则补齐。

## 目录结构

```
stock-project-local/
│
├── pe_data_service_influxdb.py   # Flask API 主服务（所有数据查询入口）
├── sse_market_data_crawler.py    # SSE大盘爬虫（写入 InfluxDB）
├── data_collector.py             # 个股数据采集器（待完善）
│
├── html/
│   └── market.html               # 前端页面（ECharts 可视化）
│
├── nginx/
│   └── default.conf              # Nginx 反向代理配置
│
├── docker-compose.local.yml      # 本地 Docker 编排
├── docker-compose.production.yml # 生产 Docker 编排
├── Dockerfile.web                # Web 服务容器镜像
│
├── stock_list.json               # 股票代码清单
├── requirements.txt              # Python 依赖
├── deploy.py                     # 简易部署脚本
├── README.md                     # 项目入口 README（指向 docs/）
│
├── ansible/
│   ├── deploy.yml                # Ansible 部署剧本
│   └── ansible.cfg
│
└── docs/                         # 项目文档
    ├── README.md                 # 文档目录
    ├── CLAUDE.md                 # 本文档：AI 项目说明书
    ├── 01-architecture.md        # 系统架构
    ├── 02-development.md         # 本地开发
    ├── 03-deployment.md          # 部署指南
    ├── 04-api-reference.md       # API 接口文档
    ├── 05-database-schema.md     # 数据库 Schema 设计
    └── SSE_API_DOC.md            # SSE原始API参考
```

## API 端点速查

| 端点 | 说明 |
|------|------|
| `GET /api/market/pe/history` | 大盘全量历史（所有产品类别的所有字段） |
| `GET /api/market/pe` | 当前大盘概要 |
| `GET /api/search?q=<查询词>` | 搜索股票 |
| `GET /api/stock/<code>` | 个股K线（最近约180天） |
| `GET /api/stock/<code>/history?before=<date>` | 更早K线（增量加载） |
| `GET /api/stock/<code>/realtime` | 实时行情 |
| `GET /api/dividend/<code>` | 分红数据 |
| `GET /api/allotment/<code>` | 配股数据 |
| `GET /api/health` | 健康检查 |

## 关键注意事项

### ✅ 应该做的

- 修改后端后直接 `python pe_data_service_influxdb.py` 验证，再 build Docker
- 前端改完直接刷新浏览器（纯静态，修改即生效）
- 所有数据操作走 InfluxDB Flux 查询
- 写文档同步更新 `docs/`

### ❌ 禁止做的

- **不要新增端口映射**（用已有的 18080/18082/18086 或 8080/8082/8086）
- **不要新增数据源**（所有数据必须从 InfluxDB 出）
- **不要在前端直接调外部 API**
- **不要改容器内端口**（Flask 固定 5000，InfluxDB 固定 8086）
- **不要在根目录创建新的 .md 文档**（统一放 `docs/`）
- **不要修改 git 配置**（用户有严格限制）

### ⚠️ 已知问题

- 个股K线目前还是腾讯API实时查询，数据未持久化
- 分红配股用 akshare 实时查询，未持久化
- 全量历史采集（4000只股票×20年）尚未实现，数据迁移待完成

## 快速启动

```bash
$env:INFLUXDB_URL="http://localhost:18086"; $env:INFLUXDB_TOKEN="my-super-secret-token"
$env:INFLUXDB_ORG="stock"; $env:INFLUXDB_BUCKET="market_data"; $env:PORT="5000"
python pe_data_service_influxdb.py
# → http://localhost:18082/
```

详情见 `docs/02-development.md`、`docs/03-deployment.md`。
