# 上证交易所( SSE )市场数据 API 文档

## 一、概述

本文档记录上证交易所官网市场数据 API 的使用方法、数据范围、以及新旧网站的 API 差异。

数据来源：
- **旧网站（历史API）**：1999年 ~ 2021-12-24
  https://www.sse.com.cn/market/stockdata/overview/day/index_his.shtml
- **新网站（新版API）**：2021-12-25 ~ 至今
  https://www.sse.com.cn/market/stockdata/overview/day/

---

## 二、API 端点

### 2.1 历史 API（旧网站）

**适用日期**：1999年 ~ 2021-12-24

**端点地址**：
```
https://query.sse.com.cn/commonQuery.do
```

**请求参数**：
| 参数 | 说明 | 示例值 |
|------|------|--------|
| sqlId | SQL ID（固定值） | `COMMON_SSE_SJ_GPSJ_CJGK_DAYCJGK_C` |
| stockType | 股票类型（固定值） | `90` |
| searchDate | 查询日期 | `2021-12-24` |
| jsonCallBack | JSONP 回调函数名 | `cb` |
| _ | 时间戳（毫秒） | `1777306252544` |

**完整请求示例**：
```
https://query.sse.com.cn/commonQuery.do?sqlId=COMMON_SSE_SJ_GPSJ_CJGK_DAYCJGK_C&stockType=90&searchDate=2021-12-24&jsonCallBack=cb&_=1777306252544
```

**返回数据说明**：
返回 6 条记录，包含以下 PRODUCT_TYPE：

| PRODUCT_TYPE | 名称 | 说明 |
|--------------|------|------|
| 40 | 股票（汇总） | 完整的市场汇总数据，推荐使用 |
| 1 | 主板A | 主板A股市盈率等 |
| 2 | 主板B | 主板B股市盈率等 |
| 48 | 科创板 | 科创板市盈率等 |
| 43 | 股票回购 | 回购数据 |
| 12 | 股票（子汇总） | 与 TYPE=40 数据相同 |

**返回字段列表**：
| 字段名 | 中文说明 | 示例值 |
|--------|----------|--------|
| PRODUCT_TYPE | 产品类型代码 | `40` |
| CAL_DATE | 日期 | `2021-12-24 00:00:00.0` |
| LIST_NUM | （备用字段） | - |
| TX_NUM | **挂牌数** | `2073` |
| MKT_VALUE | **市价总值（亿元）** | `515376.26` |
| NEGOTIABLE_VALUE | **流通市值（亿元）** | `432198.23` |
| TX_AMOUNT | **成交金额（亿元）** | `4785.61` |
| TX_VOLUME | **成交量（亿股）** | `391.11` |
| AVG_PROFIT_RATE | **平均市盈率（倍）** | `17.89` |
| AVG_PROFIT_RATE_FULL | 平均市盈率（滚动） | `17.892` |
| TOTAL_MK_CAP_RATE | **换手率（%）** | `0.9286` |
| SUB_NEW_STOCK_RATE | **次新股换手率（%）** | `1.075` |
| EXCHANGE_RATE | **流通换手率（%）** | `1.1073` |
| TRADING_TX | 交易额（万笔） | `3550.8108` |

---

### 2.2 新版 API（新网站）

**适用日期**：2021-12-25 ~ 至今

**端点地址**：
```
https://query.sse.com.cn/commonQuery.do
```

**请求参数**：
| 参数 | 说明 | 示例值 |
|------|------|--------|
| sqlId | SQL ID（固定值） | `COMMON_SSE_SJ_GPSJ_CJGK_MRGK_C` |
| PRODUCT_CODE | 产品代码（逗号分隔） | `01,02,03,11,17` |
| type | 参数类型（固定值） | `inParams` |
| SEARCH_DATE | 查询日期 | `20211227`（YYYYMMDD格式） |
| jsonCallBack | JSONP 回调函数名 | `cb` |
| _ | 时间戳（毫秒） | `1777306252544` |

**完整请求示例**：
```
https://query.sse.com.cn/commonQuery.do?sqlId=COMMON_SSE_SJ_GPSJ_CJGK_MRGK_C&PRODUCT_CODE=01%2C02%2C03%2C11%2C17&type=inParams&SEARCH_DATE=20211227&jsonCallBack=cb&_=1777306252544
```

**产品代码说明**：
| PRODUCT_CODE | 名称 |
|--------------|------|
| 01 | 主板A |
| 02 | 主板B |
| 03 | 科创板 |
| 11 | 股票回购 |
| 17 | 全部 |

**返回字段列表**：
| 字段名 | 中文说明 |
|--------|----------|
| PRODUCT_CODE | 产品代码 |
| TRADE_DATE | 日期 |
| LIST_NUM | 挂牌数 |
| TOTAL_VALUE | 市价总值 |
| NEGO_VALUE | 流通市值 |
| TRADE_AMT | 成交金额 |
| TRADE_VOL | 成交量 |
| AVG_PE_RATE | 平均市盈率 |
| TOTAL_TO_RATE | 换手率 |
| NEGO_TO_RATE | 流通换手率 |

---

## 三、数据时间范围

```
1999-01-01 ─────────────────── 2021-12-24 ─────────────────── 2026-04-29
        │                              │                              │
        └──── 历史API（旧网站） ────────┘                              │
                                      └──── 新版API（新网站） ─────────┘
```

| API | 适用日期 | 分类数量 | 特殊说明 |
|-----|----------|----------|----------|
| 历史API | 1999年 ~ 2021-12-24 | 6个分类 | 包含完整的所有字段 |
| 新版API | 2021-12-25 ~ 至今 | 5个分类 | 不包含TYPE=40/TYPE=12 |

**产品类型代码对照表**：

| 产品名称 | 历史API代码 | 新版API代码 |
|----------|------------|------------|
| 主板A股 | 1, 12, 40 | 01 |
| 主板B股 | 2 | 02 |
| 科创板 | 48 | 03 |
| 股票回购 | 43 | 11 |
| 全部股票 | 40 | 17 |

---

## 四、爬虫使用

### 4.1 基本用法

```bash
# 查询单日数据
python sse_market_data_crawler.py --date 2026-04-28

# 查询日期范围
python sse_market_data_crawler.py --start 2021-12-20 --end 2021-12-26
```

### 4.2 爬虫自动选择逻辑

```python
def get_market_data(date_str):
    date_obj = datetime.strptime(date_str, '%Y-%m-%d')
    new_api_start = datetime(2021, 12, 25)  # 新网站启用日期

    if date_obj >= new_api_start:
        # 使用新版API (2021-12-25 及之后)
        raw_data = fetch_market_data_by_new_api(date_str)
        if raw_data:
            return parse_new_api_data(raw_data)

    # 使用历史API（支持1999年至2021-12-24）
    raw_data = fetch_market_data_by_history_api(date_str)
    if raw_data:
        return parse_history_data(raw_data, date_str)

    return None
```

---

## 五、新旧API字段对比

| 指标 | 历史API字段 | 新版API字段 | 单位 |
|------|------------|------------|------|
| 挂牌数 | TX_NUM | LIST_NUM | 个 |
| 市盈率 | AVG_PROFIT_RATE | AVG_PE_RATE | 倍 |
| 完整市盈率 | AVG_PROFIT_RATE_FULL | - | 倍 |
| 市价总值 | MKT_VALUE | TOTAL_VALUE | 亿元 |
| 流通市值 | NEGOTIABLE_VALUE | NEGO_VALUE | 亿元 |
| 成交金额 | TX_AMOUNT | TRADE_AMT | 亿元 |
| 成交量 | TX_VOLUME | TRADE_VOL | 亿股 |
| 换手率 | TOTAL_MK_CAP_RATE | TOTAL_TO_RATE | % |
| 流通换手率 | EXCHANGE_RATE | NEGO_TO_RATE | % |
| 次新股换手率 | SUB_NEW_STOCK_RATE | - | % |
| 交易笔数 | TRADING_TX | - | 万笔 |

---

## 六、常见问题

### 6.1 为什么 2021-12-24 的数据新旧API不同？

2021-12-24 是两个 API 的**分界点**：
- 历史API在2021-12-24有完整数据（6个分类）
- 新版API在2021-12-24没有数据（从2021-12-25开始才有）

**解决方案**：爬虫会自动判断，2021-12-24及之前的日期使用历史API。

### 6.2 TYPE=40 和 TYPE=12 有什么区别？

| TYPE | 说明 |
|------|------|
| 40 | 完整的市场汇总数据，**推荐使用** |
| 12 | 同样是汇总数据，与TYPE=40数据相同 |

两者数据完全一致，使用时只取 TYPE=40 即可。

### 6.3 TX_NUM 字段的含义？

TX_NUM 在返回数据中实际表示的是**挂牌数**（上市股票数量），而不是成交笔数。

### 6.4 股票回购(TYPE=43)数据特点

| 字段 | 值 |
|------|-----|
| 市盈率 | 0 |
| 市价总值 | - |
| 流通市值 | - |
| 换手率 | 0 |

股票回购是特殊分类，部分字段为空或为0是正常的。

---

## 七、参考链接

- 新市场数据页面：https://www.sse.com.cn/market/stockdata/overview/day/
- 旧市场数据页面：https://www.sse.com.cn/market/stockdata/overview/day/index_his.shtml
- SSE投资者教育：https://edu.sse.com.cn/

---

## 八、系统架构与部署

### 8.1 整体架构

```
┌──────────┐      ┌──────────┐      ┌─────────────┐      ┌──────────┐
│  爬虫     │ ──→  │ InfluxDB  │ ──→  │  Web服务    │ ──→  │  前端    │
│ (Docker)  │ 写入 │ 时序数据库│ 查询 │ Flask API   │ JSON  │ ECharts  │
└──────────┘      └──────────┘      └─────────────┘      └──────────┘
                                          ↑
                                    ┌─────┴──────┐
                                    │  Nginx代理   │
                                    │ (反向代理)   │
                                    └────────────┘
```

**数据流向**：
1. **爬虫** (sse_market_data_crawler.py) 从上交所官网爬取数据
2. 爬虫将数据写入 **InfluxDB**（时序数据库）
3. **Web服务** (pe_data_service_influxdb.py) 提供 REST API，从 InfluxDB 查询数据
4. **Nginx** 将 `/api/` 请求代理到 Web 服务
5. **前端** (index.html) 通过 `fetch('/api/...')` 调用 API 获取数据并渲染图表

### 8.2 端口配置（固定）

**本地开发（docker-compose.local.yml）**：

| 服务 | 宿主机端口 | 容器内端口 | 说明 |
|------|-----------|-----------|------|
| nginx | **18080** | 80 | 前端页面入口 |
| Web API | **18082** | 5000 | 后端API（Flask） |
| InfluxDB | **18086** | 8086 | 时序数据库 |

**访问方式**：
- 前端页面：`http://localhost:18080`
- API直连：`http://localhost:18082/api/market/pe/history`
- InfluxDB管理界面：`http://localhost:18086`（Token: `my-super-secret-token`）

### 8.3 InfluxDB Schema

**Bucket**：`market_data`

**Measurement**：`sse_market`

**Tags**：

| 标签名 | 说明 | 示例值 |
|--------|------|--------|
| `product_code` | 产品代码 | `01`（主板A）, `02`（主板B）, `03`（科创板）, `11`（股票回购）, `17`（全部）|
| `product_name` | 产品名称 | `主板A`, `主板B`, `科创板` |

**Fields**（爬虫写入的原始字段）：

| 字段名 | 类型 | 说明 | 单位 |
|--------|------|------|------|
| `trade_date` | string | 交易日（用于去重） | YYYY-MM-DD |
| `pe_ratio` | float | 平均市盈率 | 倍 |
| `pe_ratio_full` | float | 完整市盈率（仅历史API） | 倍 |
| `listed_count` | float | 挂牌数（上市股票数） | 个 |
| `market_cap` | float | 市价总值 | 亿元 |
| `market_cap_full` | float | 完整市值（仅历史API） | 亿元 |
| `float_market_cap` | float | 流通市值 | 亿元 |
| `float_market_cap_full` | float | 完整流通市值（仅历史API） | 亿元 |
| `trade_amount` | float | 成交金额 | 亿元 |
| `trade_amount_full` | float | 完整成交金额（仅历史API） | 亿元 |
| `trade_vol` | float | 成交量 | 亿股 |
| `trade_vol_full` | float | 完整成交量（仅历史API） | 亿股 |
| `turnover_rate` | float | 换手率 | % |
| `turnover_rate_full` | float | 完整换手率（仅历史API） | % |
| `float_turnover_rate` | float | 流通换手率 | % |
| `float_turnover_rate_full` | float | 完整流通换手率（仅历史API） | % |

**时间戳**：每个数据点的日期（交易日），格式为 YYYY-MM-DD

---

## 九、后端 API 接口

### 9.1 市场历史数据（全量）

**接口**：`GET /api/market/pe/history`

**说明**：获取大盘每日完整市场数据，按天返回所有产品类别（主板A/主板B/科创板/全部）的所有字段（市盈率、换手率、市值、成交额等）。

**查询逻辑**：从 InfluxDB 的 `sse_market` measurement 查询所有字段，按 `(日期, product_code)` 分组聚合。

**Flux 查询**：
```flux
from(bucket: "market_data")
  |> range(start: 0)
  |> filter(fn: (r) => r._measurement == "sse_market")
  |> sort(columns: ["_time"])
```

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

**可用字段说明**（每个 `products.{code}` 中）：

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

**产品代码对照**：

| product_code | 名称 |
|--------------|------|
| `01` | 主板A |
| `02` | 主板B |
| `03` | 科创板 |
| `11` | 股票回购 |
| `17` | 全部 |

### 9.2 当前市场概要

**接口**：`GET /api/market/pe`

**说明**：获取当前大盘PE值及历史统计摘要（最近365天），快速概要接口。**前端主图表已改用 9.1 全量接口。**

### 9.3 股票搜索

**接口**：`GET /api/search?q=<查询词>`

**说明**：按股票代码或名称搜索，返回匹配的股票列表。

**返回示例**：
```json
[
  {"code": "000001", "name": "平安银行"},
  {"code": "000002", "name": "万科A"}
]
```

### 9.4 个股K线

**接口**：`GET /api/stock/<code>`

**说明**：获取个股历史K线数据（180天），数据来源腾讯API。

### 9.5 个股实时行情

**接口**：`GET /api/stock/<code>/realtime`

**说明**：获取个股实时行情数据，数据来源腾讯API。

### 9.6 健康检查

**接口**：`GET /api/health`

**返回示例**：
```json
{
  "status": "healthy",
  "data_source": "influxdb",
  "timestamp": "2026-05-03T10:00:00"
}
```

---

## 十、前端数据加载

### 10.1 数据获取方式

前端（html/market.html）不直接连接数据库，而是通过调用后端 API 获取数据。

**大盘数据加载**（market.html 第764-797行）：
```javascript
async function loadMarketPeData() {
  const res = await fetch('/api/market/pe/history');  // 调用全量市场数据接口
  const json = await res.json();

  // data 中每个元素包含:
  //   date          - 日期
  //   pe            - 向后兼容的主板A市盈率
  //   products      - 所有产品类别的完整字段（主板A/B/科创板/全部）
  //     .01.pe_ratio
  //     .01.turnover_rate
  //     .02.pe_ratio
  //     ...
  //
  // 当前只渲染市盈率折线，products 数据保留给后续扩展
  const dates = json.data.map(d => d.date);
  const peValues = json.data.map(d => d.pe);

  if (json.stats) {
    currentPe = json.stats.current;
    peAvg = json.stats.avg;
  }

  initPeChart();
}
```

### 10.2 请求流程

```
浏览器: fetch('/api/market/pe/history')
             │
             ▼
   Nginx (localhost:18080)  →  代理到 http://web:5000/api/market/pe/history
             │
             ▼
   Flask Web服务  →  Flux查询 →  InfluxDB
             │
             ▼
   JSON响应  →  前端渲染ECharts图表
```

### 10.3 前端依赖的API返回值字段

前端使用了以下 API 返回字段：

| 字段路径 | 用途 | 对应前端变量 |
|---------|------|------------|
| `json.data[].date` | 日期标签 | `dates` |
| `json.data[].pe` | PE值（向后兼容，取自主板A） | `peValues` |
| `json.data[].products` | 全量市场数据（各产品代码×各字段） | `allData`（暂存，后续扩展） |
| `json.data[].products.01.pe_ratio` | 主板A市盈率 | 后续扩展可独立引用 |
| `json.data[].products.02.turnover_rate` | 主板B换手率 | 后续扩展 |
| `json.stats.current` | 当前PE | `currentPe` |
| `json.stats.percentile` | 当前分位 | `currentPct` |
| `json.stats.avg` | 历史均值 | `peAvg` |
| `json.stats.max` | 历史最高 | 显示在统计栏 |
| `json.stats.min` | 历史最低 | 显示在统计栏 |
| `json.stats.count` | 数据点数量 | 显示在统计栏 |

---

## 十一、更新日志

| 日期 | 版本 | 说明 |
|------|------|------|
| 2026-05-03 | v2.0 | 新增系统架构、InfluxDB Schema、后端API文档、前端数据加载说明 |
| 2026-04-29 | v1.1 | 修正API分界日期为2021-12-25 |
| 2026-04-28 | v1.0 | 初版文档创建 |
