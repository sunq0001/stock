# 系统架构设计

## 一、整体架构

```
┌──────────────────┐     ┌──────────────────┐     ┌─────────────────┐     ┌──────────────┐
│  数据采集器       │     │                  │     │                 │     │              │
│                  │ ──→ │   InfluxDB        │ ──→ │   Flask API     │ ──→ │  前端页面     │
│ sse_market_data_ │ 写入 │   时序数据库       │ 查询 │   pe_data_      │ JSON │  ECharts渲染  │
│ crawler.py       │     │   (市场数据源)     │     │   service_      │     │  market.html │
│ data_collector.py│     │                  │     │   influxdb.py   │     │              │
└──────────────────┘     └──────────────────┘     └─────────────────┘     └──────────────┘
                                                            ↑
                                                    ┌───────┴────────┐
                                                    │   Nginx 反向代理 │
                                                    │  (nginx/conf)  │
                                                    └────────────────┘
```

### 数据流向

1. **采集层**：爬虫从外部数据源获取原始数据，写入 InfluxDB
   - SSE大盘概览：`sse_market_data_crawler.py` → 上交所官网API
   - 个股K线/分红/配股：`data_collector.py` → 腾讯API / akshare
2. **存储层**：InfluxDB 时序数据库，唯一数据源
3. **服务层**：Flask API 从 InfluxDB 查询，返回 JSON
4. **代理层**：Nginx 反向代理 `/api/` 到 Flask，并提供前端静态文件
5. **展示层**：前端 HTML + ECharts 渲染图表

## 二、技术栈

| 组件 | 技术 | 说明 |
|------|------|------|
| 后端框架 | Flask + Flask-CORS | Python Web 服务 |
| 数据库 | InfluxDB 2.x | 时序数据库 |
| 数据库查询 | Flux 语言 | InfluxDB 查询语言 |
| 前端 | HTML + CSS + ECharts 5.x | 数据可视化 |
| 反向代理 | Nginx | 路由、静态文件服务 |
| 容器化 | Docker + Docker Compose | 部署运行 |
| 部署 | Ansible / deploy.py | 服务器自动化部署 |
| 数据采集 | requests / akshare | 外部数据源调用 |

## 三、容器架构

### 本地开发（docker-compose.local.yml）

| 服务 | 容器名 | 宿主机端口 | 容器内端口 |
|------|--------|-----------|-----------|
| nginx | stock-nginx | 18080 | 80 |
| Web API | sse-pe-service | 18082 | 5000 |
| InfluxDB | stock-influxdb | 18086 | 8086 |

### 生产部署（docker-compose.production.yml）

| 服务 | 宿主机端口 | 容器内端口 |
|------|-----------|-----------|
| nginx | 8080 | 80 |
| Web API | 8082 | 5000 |
| InfluxDB | 8086 | 8086 |

## 四、设计原则与规范

### 1. 数据源统一原则

**所有数据存储在 InfluxDB**，后端 API 全部从 InfluxDB 查询。

**禁止**：前端直接调用外部API（腾讯API、akshare等）、后端实时调外部API返回。

**正确做法**：
```
外部数据 → 爬虫采集 → InfluxDB → API查询 → 前端展示
```

### 2. 端口固定原则

本地端口和生产端口分开，但容器内端口一致：

| 服务 | 容器内端口 | 本地映射 | 生产映射 |
|------|-----------|---------|---------|
| nginx | 80 | 18080 | 8080 |
| Flask | 5000 | 18082 | 8082 |
| InfluxDB | 8086 | 18086 | 8086 |

> 生产环境通过 Nginx 暴露 8080 端口，配域名后可用 80/443。

### 3. 代码与数据分离

- **代码**：Docker 镜像只打包 Python 代码 + 前端 HTML
- **数据**：InfluxDB 数据通过 Volume 持久化，与容器生命周期无关
- **初始化**：容器启动时自动判断数据库是否初始化，未初始化则采集

### 4. 本地开发 → 服务器同步流程

```
本地开发测试
    ↓ (git commit + push)
服务器拉取代码
    ↓
重新构建镜像
    ↓
重启容器
    ↓
初始化/补齐数据（如有需要）
```

## 五、核心文件说明

| 文件 | 用途 |
|------|------|
| `pe_data_service_influxdb.py` | Flask API 服务，InfluxDB 查询 |
| `sse_market_data_crawler.py` | SSE大盘数据爬虫（写入InfluxDB） |
| `data_collector.py` | 个股K线/分红/配股采集器 |
| `html/market.html` | 前端页面 |
| `nginx/default.conf` | Nginx 配置 |
| `stock_list.json` | 股票代码清单 |
| `Dockerfile.web` | Web 服务容器镜像 |
| `docker-compose.local.yml` | 本地 Docker 编排 |
| `docker-compose.production.yml` | 生产 Docker 编排 |
| `deploy.py` | 简易部署脚本 |
| `ansible/` | Ansible 自动化部署 |
| `docs/` | 项目文档 |
