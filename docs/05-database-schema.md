# 数据库 Schema 设计

## 一、概述

使用 **InfluxDB 2.x** 时序数据库，所有市场数据统一存储。

| 连接参数 | 值 |
|---------|-----|
| Bucket | `market_data` |
| Token | `my-super-secret-token` |
| Org | `stock` |
| URL | `http://localhost:8086`（容器内） / `http://localhost:18086`（本地） |

---

## 二、Measurement: `sse_market`

存储上证交易所大盘市场概览数据。

### Tags

| 标签 | 类型 | 说明 | 示例 |
|------|------|------|------|
| `product_code` | tag | 产品代码 | `01`, `02`, `03`, `11`, `17` |
| `product_name` | tag | 产品名称 | `主板A`, `主板B`, `科创板` |

### Fields

| 字段名 | 类型 | 说明 | 单位 | 来源 |
|--------|------|------|------|------|
| `trade_date` | string | 交易日（用于去重） | YYYY-MM-DD | 爬虫 |
| `pe_ratio` | float | 平均市盈率 | 倍 | 新旧API均有 |
| `pe_ratio_full` | float | 完整市盈率（滚动） | 倍 | 仅历史API |
| `listed_count` | float | 挂牌数（上市股票数） | 个 | 新旧API均有 |
| `market_cap` | float | 市价总值 | 亿元 | 新旧API均有 |
| `market_cap_full` | float | 完整市价总值 | 亿元 | 仅历史API |
| `float_market_cap` | float | 流通市值 | 亿元 | 新旧API均有 |
| `float_market_cap_full` | float | 完整流通市值 | 亿元 | 仅历史API |
| `trade_amount` | float | 成交金额 | 亿元 | 新旧API均有 |
| `trade_amount_full` | float | 完整成交金额 | 亿元 | 仅历史API |
| `trade_vol` | float | 成交量 | 亿股 | 新旧API均有 |
| `trade_vol_full` | float | 完整成交量 | 亿股 | 仅历史API |
| `turnover_rate` | float | 换手率 | % | 新旧API均有 |
| `turnover_rate_full` | float | 完整换手率 | % | 仅历史API |
| `float_turnover_rate` | float | 流通换手率 | % | 新旧API均有 |
| `float_turnover_rate_full` | float | 完整流通换手率 | % | 仅历史API |

### 产品代码对照

| product_code | 名称 | 说明 |
|--------------|------|------|
| `01` | 主板A | A股主板 |
| `02` | 主板B | B股主板 |
| `03` | 科创板 | 科创板 |
| `11` | 股票回购 | 回购数据（部分字段为空正常） |
| `17` | 全部 | 全市场汇总 |

### 时间戳

每个数据点的时间戳为交易日日期，格式 `YYYY-MM-DD`。

### Flux 查询示例

```flux
# 查全部数据
from(bucket: "market_data")
  |> range(start: 0)
  |> filter(fn: (r) => r["_measurement"] == "sse_market")
  |> sort(columns: ["_time"])

# 只查主板A和主板的市盈率
from(bucket: "market_data")
  |> range(start: 0)
  |> filter(fn: (r) => r["_measurement"] == "sse_market")
  |> filter(fn: (r) => r["product_code"] == "01" or r["product_code"] == "02")
  |> filter(fn: (r) => r["_field"] == "pe_ratio")
  |> sort(columns: ["_time"])

# 查最近30天所有品类所有字段
from(bucket: "market_data")
  |> range(start: -30d)
  |> filter(fn: (r) => r["_measurement"] == "sse_market")
```

---

## 三、Measurement: `stock_kline` ✅ 已实现

存储个股日K线（前复权），API查询时自动写入。

**Tags**：

| 标签 | 说明 | 示例 |
|------|------|------|
| `code` | 股票代码 | `000001` |

**Fields**：

| 字段名 | 类型 | 说明 | 单位 |
|--------|------|------|------|
| `trade_date` | string | 交易日 | YYYY-MM-DD |
| `open` | float | 开盘价 | 元 |
| `close` | float | 收盘价 | 元 |
| `high` | float | 最高价 | 元 |
| `low` | float | 最低价 | 元 |
| `volume` | float | 成交量 | 股 |

**时间戳**：交易日日期

---

## 四、Measurement: `stock_dividend` ✅ 已实现

存储个股分红送转数据，API查询时自动写入。

**Tags**：

| 标签 | 说明 |
|------|------|
| `code` | 股票代码 |

**Fields**：

| 字段名 | 类型 | 说明 | 单位 |
|--------|------|------|------|
| `ex_date` | string | 除权日 | YYYY-MM-DD |
| `date` | string | 股权登记日 | YYYY-MM-DD |
| `cash` | float | 现金分红 | 元/股 |
| `bonus` | float | 送股 | 股/股 |
| `transfer` | float | 转增 | 股/股 |
| `desc` | string | 分红说明 | 文本 |

**时间戳**：除权日日期

---

## 五、Measurement: `stock_allotment` ✅ 已实现

存储个股配股数据，API查询时自动写入。

**Tags**：

| 标签 | 说明 |
|------|------|
| `code` | 股票代码 |

**Fields**：

| 字段名 | 类型 | 说明 | 单位 |
|--------|------|------|------|
| `ex_date` | string | 除权基准日 | YYYY-MM-DD |
| `date` | string | 股权登记日 | YYYY-MM-DD |
| `ratio` | float | 配股比例 | 股/股（每股配股数） |
| `price` | float | 配股价 | 元 |
| `pay_start` | string | 缴款开始日 | YYYY-MM-DD |
| `pay_end` | string | 缴款截止日 | YYYY-MM-DD |

**时间戳**：除权基准日

---

## 六、Measurement: `stock_list` ✅ 已实现

存储股票代码与名称映射，启动时自动从 `stock_list.json` 加载。

**Tags**：

| 标签 | 说明 |
|------|------|
| `code` | 股票代码 |

**Fields**：

| 字段名 | 类型 | 说明 |
|--------|------|------|
| `name` | string | 股票名称 |
| `py` | string | 拼音缩写 |

---

## 七、数据采集策略

### 当前采集方式（被动缓存）

目前采用**写穿缓存**策略，用户在浏览器查股票时自动写入：

```
用户查股票 → API调外部数据 → 同时写入InfluxDB → 数据自然积累
```

个股K线/分红/配股：API查询时自动写入 `stock_kline` / `stock_dividend` / `stock_allotment`
股票清单：服务启动时自动从 `stock_list.json` 加载到 `stock_list`
大盘数据：由 `sse_market_data_crawler.py` 或 `data_collector.py` 采集到 `sse_market`

### 全量采集（可选）

```
1. 大盘历史（sse_market）：sse_market_data_crawler.py --start 1999-01-01 --end 2026-12-31
2. 个股全量：遍历 stock_list.json，逐一查K线/分红/配股（数据自动写入库中）
```

### 增量更新（每日收盘后）

```
1. 检查大盘当天数据是否已存在 → 不存在则采集
2. 遍历所有股票 → 检查当天K线 → 不存在则采集
3. 检查是否有新分红/配股公告 → 有则补充
4. 检查新股 → 补充股票清单 + 历史K线
```

### 增量判断方式

InfluxDB 中的 `trade_date` 字段可用于判断某天数据是否已存在：

```flux
# 检查某天是否已有数据
from(bucket: "market_data")
  |> range(start: 2026-05-06, stop: 2026-05-07)
  |> filter(fn: (r) => r["_measurement"] == "sse_market")
  |> filter(fn: (r) => r["product_code"] == "01")
  |> limit(n: 1)
```

---

## 五、后端查询映射

后端 API 通过 Flux 查询 InfluxDB，返回给前端 JSON。

| API 端点 | 查询的 Measurement | 数据聚合方式 |
|---------|-------------------|-------------|
| `/api/market/pe/history` | `sse_market` | 按 (日期, product_code) 分组，组装为 `products` 结构 |
| `/api/market/pe` | `sse_market` | 最近365天，计算统计摘要 |
| `/api/stock/<code>` | （腾讯API实时，待迁移） | - |
| `/api/dividend/<code>` | （akshare实时，待迁移） | - |
| `/api/allotment/<code>` | （akshare实时，待迁移） | - |
