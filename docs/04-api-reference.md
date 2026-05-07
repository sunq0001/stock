# API 接口文档

## 一、概览

所有 API 端点由 `pe_data_service_influxdb.py` 提供，数据来源为 InfluxDB。

| 前缀 | 说明 |
|------|------|
| `GET /api/market/...` | 大盘市场数据 |
| `GET /api/stock/...` | 个股数据 |
| `GET /api/...` | 搜索、健康检查等 |

---

## 二、大盘数据

### 2.1 市场历史全量数据

**接口**：`GET /api/market/pe/history`

**说明**：获取大盘每日完整市场数据，按天返回所有产品类别的所有字段。

**返回格式**：
```json
{
  "data": [
    {
      "date": "2025-05-06",
      "pe": 13.56,
      "products": {
        "01": {
          "name": "主板A",
          "pe_ratio": 13.56,
          "turnover_rate": 0.93,
          "float_turnover_rate": 1.11,
          "market_cap": 515376.26,
          "float_market_cap": 432198.23,
          "trade_amount": 4785.61,
          "trade_vol": 391.11,
          "listed_count": 2073
        },
        "02": { "name": "主板B", "pe_ratio": 8.12, ... },
        "03": { "name": "科创板", "pe_ratio": 45.6, ... },
        "17": { "name": "全部", "pe_ratio": 15.2, ... }
      }
    }
  ],
  "stats": {
    "current": 16.97,
    "percentile": 92.6,
    "avg": 15.67,
    "max": 17.21,
    "min": 13.56,
    "count": 242
  },
  "data_source": "influxdb"
}
```

**`products.{code}` 字段说明**：

| 字段名 | 中文说明 | 单位 |
|--------|----------|------|
| `name` | 产品名称 | - |
| `pe_ratio` | 平均市盈率 | 倍 |
| `pe_ratio_full` | 完整市盈率（仅历史API） | 倍 |
| `listed_count` | 挂牌数 | 个 |
| `market_cap` | 市价总值 | 亿元 |
| `market_cap_full` | 完整市值（仅历史API） | 亿元 |
| `float_market_cap` | 流通市值 | 亿元 |
| `float_market_cap_full` | 完整流通市值（仅历史API） | 亿元 |
| `trade_amount` | 成交金额 | 亿元 |
| `trade_amount_full` | 完整成交金额（仅历史API） | 亿元 |
| `trade_vol` | 成交量 | 亿股 |
| `trade_vol_full` | 完整成交量（仅历史API） | 亿股 |
| `turnover_rate` | 换手率 | % |
| `turnover_rate_full` | 完整换手率（仅历史API） | % |
| `float_turnover_rate` | 流通换手率 | % |
| `float_turnover_rate_full` | 完整流通换手率（仅历史API） | % |

**product_code 对照**：

| code | 名称 |
|------|------|
| `01` | 主板A |
| `02` | 主板B |
| `03` | 科创板 |
| `11` | 股票回购 |
| `17` | 全部 |

### 2.2 当前市场概要

**接口**：`GET /api/market/pe`

**说明**：获取当前大盘PE值及历史统计摘要（最近365天）。轻量概要用。

**返回格式**：
```json
{
  "data": [{ "date": "2026-05-07", "pe": 16.97, "price": 3340, "turnover": 0 }],
  "stats": { "current": 16.97, "percentile": 92.6, "avg": 15.67, "max": 17.21, "min": 13.56, "count": 242 },
  "data_source": "influxdb"
}
```

---

## 三、个股数据

### 3.1 股票搜索

**接口**：`GET /api/search?q=<查询词>`

**说明**：按股票代码或名称搜索。

**返回**：
```json
[
  { "code": "000001", "name": "平安银行" },
  { "code": "000002", "name": "万科A" }
]
```

### 3.2 个股K线

**接口**：`GET /api/stock/<code>`

**说明**：获取个股历史K线数据（最近约180天，前复权）。

**参数**：`code` — 6位股票代码

**返回**：
```json
{
  "name": "平安银行",
  "kline": [
    { "日期": "2026-05-06", "开盘": 11.48, "收盘": 11.41, "最高": 11.49, "最低": 11.40, "成交量": 12345678 },
    ...
  ],
  "all_loaded": false
}
```

### 3.3 个股K线历史增量（更早数据）

**接口**：`GET /api/stock/<code>/history?before=<date>`

**说明**：获取指定日期之前的历史K线（用于用户拖动加载更早数据）。

**参数**：`before` — 当前最早日期

**返回**：同上，`all_loaded: true` 表示已无更早数据。

### 3.4 个股实时行情

**接口**：`GET /api/stock/<code>/realtime`

**说明**：获取个股实时行情。

### 3.5 分红数据

**接口**：`GET /api/dividend/<code>`

**说明**：获取个股历史分红送转数据。

**返回**：
```json
{
  "dividends": [
    {
      "date": "2025-06-12",
      "ex_date": "2025-06-13",
      "cash": 0.35,
      "bonus": 0,
      "transfer": 0,
      "rights": 0,
      "desc": "10派3.5元",
      "report_time": "2024年报"
    }
  ]
}
```

### 3.6 配股数据

**接口**：`GET /api/allotment/<code>`

**说明**：获取个股历史配股数据。

**返回**：
```json
{
  "allotments": [
    {
      "date": "2023-07-28",
      "ex_date": "2023-07-31",
      "ratio": 0.15,
      "price": 8.45,
      "pay_start": "2023-08-01",
      "pay_end": "2023-08-07"
    }
  ]
}
```

> `ratio` 为每股配股数（例如 0.15 = 10配1.5股）

---

## 四、系统状态

### 4.1 健康检查

**接口**：`GET /api/health`

**返回**：
```json
{
  "status": "healthy",
  "data_source": "influxdb",
  "timestamp": "2026-05-07T12:00:00"
}
```

---

## 五、InfluxDB Schema

### 5.1 连接信息

| 参数 | 值 |
|------|-----|
| URL | http://localhost:8086（容器内） |
| Token | my-super-secret-token |
| Org | stock |
| Bucket | market_data |

### 5.2 Measurement: `sse_market`

存储大盘市场概览数据（各品类市盈率、换手率、市值等）。

**Tags**：

| 标签 | 说明 | 示例 |
|------|------|------|
| `product_code` | 产品代码 | `01`, `02`, `03`, `11`, `17` |
| `product_name` | 产品名称 | `主板A`, `主板B`, `科创板` |

**Fields**：见上文 2.1 节 `products.{code}` 字段列表。

**时间戳**：交易日日期，格式 `YYYY-MM-DD`

### 5.3 Fluent Query 示例

```flux
# 查询所有大盘数据
from(bucket: "market_data")
  |> range(start: 0)
  |> filter(fn: (r) => r["_measurement"] == "sse_market")
  |> sort(columns: ["_time"])
```

---

## 六、前后端数据交互

### 6.1 加载大盘图表

```
前端 fetch(/api/market/pe/history)
    → Nginx 代理到 Flask:5000
    → Flask 查询 InfluxDB
    → 返回 JSON → 前端渲染 ECharts
```

### 6.2 加载个股K线 + 分红 + 配股

```
前端并发请求:
  fetch(/api/stock/<code>)
  fetch(/api/dividend/<code>)
  fetch(/api/allotment/<code>)

→ 后端分别处理 → 返回 JSON
→ 前端合并渲染 K线图 + 分红标记 + 收益计算
```

### 6.3 前端依赖的字段

| 字段路径 | 用途 |
|---------|------|
| `json.data[].date` | PE图日期标签 |
| `json.data[].pe` | PE值（取自主板A，向后兼容） |
| `json.data[].products` | 全量市场数据（后续扩展） |
| `json.stats.current` | 当前PE |
| `json.stats.percentile` | 历史分位 |
| `json.stats.avg` | 历史均值 |
| `json.name` | 个股名称 |
| `json.kline[].日期/开盘/收盘/最高/最低/成交量` | K线数据 |
| `json.dividends[].ex_date/cash/bonus/transfer` | 分红数据 |
| `json.allotments[].ex_date/ratio/price` | 配股数据 |
