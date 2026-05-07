# 股票数据可视化项目

> AI 项目说明书。**设计原则 + 禁止事项 + 索引。** 详细内容去 `docs/` 按需查阅。

## 一句话

爬虫采集大盘/个股数据 → InfluxDB → Flask API → ECharts 前端。

## 技术栈

后端: Python Flask · 数据库: InfluxDB 2.x (Flux) · 前端: 纯静态 HTML + ECharts · 代理: Nginx · 部署: Docker Compose + Ansible

## 设计原则

- **数据源统一**（高内聚）：全部走 InfluxDB，禁止前端/后端实时调外部API
- **低耦合**：爬虫/API/前端三个独立模块，通过 InfluxDB 连接
- **代码与数据分离**：镜像只含代码，数据走 Volume
- **端口固定** → 见下方端口表
- **本地=服务器**：同一套代码，两套 compose，启动自动补齐数据

## 端口表（不要新增/修改）

| 服务 | 容器内 | 本地 | 生产 |
|------|--------|------|------|
| Nginx | 80 | 18080 | 8080 |
| Flask | 5000 | 18082 | 8082 |
| InfluxDB | 8086 | 18086 | 8086 |

容器内用服务名通信（`web:5000`），不硬编码宿主端口。

## API 速查

`GET /api/market/pe/history` — 大盘全量 · `GET /api/market/pe` — 大盘概要
`GET /api/search?q=<查询词>` — 搜股票 · `GET /api/stock/<code>` — K线
`GET /api/stock/<code>/history?before=<date>` — 更早K线
`GET /api/dividend/<code>` — 分红 · `GET /api/allotment/<code>` — 配股
`GET /api/health` — 健康检查

## 目录

```
根: pe_data_service_influxdb.py(API)  sse_market_data_crawler.py(爬虫)
    html/market.html(前端)  nginx/default.conf  Dockerfile.web
    docker-compose.local.yml  docker-compose.production.yml
    stock_list.json  requirements.txt  README.md
docs: CLAUDE.md(本文) 01架构 02开发 03部署 04API 05Schema 06数据源 07踩坑
```

## 禁止事项

- ❌ 不新增/修改端口映射
- ❌ 不新增数据源（全走 InfluxDB）
- ❌ 不前端直接调外部API
- ❌ 不改容器内端口（Flask=5000, InfluxDB=8086）
- ❌ 不在根目录新建 .md（放 docs/）
- ❌ 不改 git 配置

## 已知问题

个股K线和分红配股当前实时调腾讯API/akshare，未持久化。待迁移到 InfluxDB。

## 快速启动

```bash
$env:INFLUXDB_URL="http://localhost:18086";$env:INFLUXDB_TOKEN="my-super-secret-token"
$env:INFLUXDB_ORG="stock";$env:INFLUXDB_BUCKET="market_data";$env:PORT="5000"
python pe_data_service_influxdb.py  # → http://localhost:18082/
```
