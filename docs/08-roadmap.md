# 开发路线图

> 每次开始新迭代前，先看这张表，确定当前阶段目标。

## 状态标记

- ✅ 已完成
- 🔄 进行中
- ⏳ 待开始
- ❌ 已取消/不需要

---

## 阶段一：基础设施搭建 ✅

| 事项 | 状态 | 说明 |
|------|------|------|
| InfluxDB Schema 设计 | ✅ | `sse_market` 已完成，`stock_kline`/`stock_dividend`/`stock_allotment` 已规划 |
| SSE大盘爬虫 | ✅ | `sse_market_data_crawler.py` 可采集 1999~今 |
| Flask API 服务 | ✅ | `pe_data_service_influxdb.py` 提供全部接口 |
| Docker Compose 本地+生产 | ✅ | 两套 ports，容器内端口一致 |
| Nginx 反向代理 | ✅ | `/api/` → Flask，`/` → 静态文件 |
| 前端大盘PE图表 | ✅ | ECharts 折线图 + 统计信息 |
| 前端个股K线 | ✅ | ECharts K线图 + 成交量 |
| 前端分红配股标记 | ✅ | K线图下方标签 + tooltip |
| 前端收益计算器 | ✅ | 历史收益分析面板 |
| 文档体系搭建 | ✅ | docs/ 分层文档 + CLAUDE.md |

## 阶段二：文档整理 ✅

| 事项 | 状态 | 说明 |
|------|------|------|
| 清理根目录旧 .md | ✅ | 删掉过时的 DEVELOP_NOTES/LOCAL_DEVELOPMENT/README_DOCKER/SSE_API_DOC |
| 清理 check_* 测试文件 | ✅ | 3个check文件已删 |
| 清理 api_result.json | 🔄 | 文件被占用，后续再删 |
| 新建 docs/ 编号文档 | ✅ | 01~07 完整体系 |
| 新建 CLAUDE.md | ✅ | 含设计原则+禁止+索引+踩坑 |
| 文档去重精简 | ✅ | CLAUDE.md 60行 + 各文档不交叉 |

## 阶段三：数据持久化 ⏳

| 事项 | 状态 | 说明 |
|------|------|------|
| 个股K线写入 InfluxDB | ⏳ | 当前实时调腾讯API，需改为爬虫写入后查询 |
| 分红配股写入 InfluxDB | ⏳ | 当前实时调 akshare，需改为爬虫写入后查询 |
| 全量历史采集器 collector.py | ⏳ | 4000只股票×5000天K线 + 分红配股历史 |
| 股票清单写入 InfluxDB | ⏳ | 替代 stock_list.json |

## 阶段四：自动初始化 ⏳

| 事项 | 状态 | 说明 |
|------|------|------|
| 容器启动自动检查数据 | ⏳ | 检查 InfluxDB 是否已初始化 |
| 缺数据自动补齐 | ⏳ | 首次全量采集 / 每日增量 |
| InfluxDB 数据打包脚本 | ⏳ | 本地全量打包 → scp → 服务器恢复 |

## 阶段五：后端API迁移 ⏳

| 事项 | 状态 | 说明 |
|------|------|------|
| 个股K线 API 改为查 InfluxDB | ⏳ | 不再调腾讯API |
| 分红 API 改为查 InfluxDB | ⏳ | 不再调 akshare |
| 配股 API 改为查 InfluxDB | ⏳ | 不再调 akshare |
| 搜索 API 改为查 InfluxDB | ⏳ | 不再读 stock_list.json |

## 阶段六：功能增强 🔄

| 事项 | 状态 | 说明 |
|------|------|------|
| 大盘全量数据(products)返回 | ✅ | 已完成：所有产品代码×所有字段 |
| 换手率/市值等其他指标展示 | ⏳ | 前端 products 数据已就绪，只展示PE |
| 多品类图表切换 | ⏳ | 可选主板A/B/科创板/全部 |
| 涨幅榜/跌幅榜 | ⏳ | 待规划 |

## 阶段七：运维

| 事项 | 状态 | 说明 |
|------|------|------|
| GitHub 推送 | ⏳ | 网络问题阻塞，需找代理或换网络 |
| 服务器同步代码 | ⏳ | git push 后，SSH到服务器 docker compose up -d --build |
| InfluxDB 数据同步到服务器 | ⏳ | 全量同步 / 增量同步 |

---

## 当前阶段

**阶段三：数据持久化** — 把个股K线/分红/配股从实时调用改为 InfluxDB 存储。

## 参考文档

| 需求来源 | 文档 |
|---------|------|
| 数据采集方案 | `docs/05-database-schema.md` 第四节 |
| 数据库 Schema 设计 | `docs/05-database-schema.md` |
| API 端点 | `docs/04-api-reference.md` |
| 踩坑记录 | `docs/07-pitfalls.md` |
