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
