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

## 三、规划中的 Measurement

以下数据尚未迁移到 InfluxDB，当前由 API 实时调用外部数据源。后续应统一入库。

### Measurement: `stock_kline`

存储个股日K线（前复权）。

| 标签 | 说明 |
|------|------|
| `code` | 股票代码（如 `000001`） |

| 字段 | 说明 | 单位 |
|------|------|------|
| `open` | 开盘价 | 元 |
| `close` | 收盘价 | 元 |
| `high` | 最高价 | 元 |
| `low` | 最低价 | 元 |
| `volume` | 成交量 | 股 |
| `amount` | 成交额 | 元 |

### Measurement: `stock_dividend`

存储个股分红送转数据。

| 标签 | 说明 |
|------|------|
| `code` | 股票代码 |

| 字段 | 说明 | 单位 |
|------|------|------|
| `cash` | 现金分红（每股） | 元 |
| `bonus` | 送股（每股） | 股 |
| `transfer` | 转增（每股） | 股 |
| `ex_date` | 除权日 | 日期 |
| `date` | 股权登记日 | 日期 |
| `desc` | 分红说明 | 文本 |

### Measurement: `stock_allotment`

存储个股配股数据。

| 标签 | 说明 |
|------|------|
| `code` | 股票代码 |

| 字段 | 说明 | 单位 |
|------|------|------|
| `ratio` | 配股比例（每股） | 股 |
| `price` | 配股价 | 元 |
| `ex_date` | 除权日 | 日期 |
| `date` | 股权登记日 | 日期 |
| `pay_start` | 缴款开始日 | 日期 |
| `pay_end` | 缴款截止日 | 日期 |

### Measurement: `stock_list`

存储股票代码与名称映射。

| 标签 | 说明 |
|------|------|
| `code` | 股票代码 |

| 字段 | 说明 |
|------|------|
| `name` | 股票名称 |
| `market` | 市场（SH/SZ） |

---

## 四、数据采集策略

### 全量采集（首次）

```
1. 采集大盘历史（sse_market）：1999年 ~ 至今，一次性
2. 采集所有个股K线（stock_kline）：上市日 ~ 至今
3. 采集所有个股分红配股（stock_dividend / stock_allotment）
4. 写入股票清单（stock_list）
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
