# SSE 数据源参考

> 本文档记录 SSE 官网原始数据接口，供爬虫 `sse_market_data_crawler.py` 使用。**不是后端 API 文档。**

## 一、概述

数据来源：
- **旧网站（历史API）**：1999年 ~ 2021-12-24
- **新网站（新版API）**：2021-12-25 ~ 至今

具体端点、参数、字段见下。

---

## 二、历史数据源（旧网站）

**适用日期**：1999年 ~ 2021-12-24

**端点**：`https://query.sse.com.cn/commonQuery.do`

**参数**：

| 参数 | 说明 | 示例值 |
|------|------|--------|
| sqlId | SQL ID（固定值） | `COMMON_SSE_SJ_GPSJ_CJGK_DAYCJGK_C` |
| stockType | 股票类型（固定值） | `90` |
| searchDate | 查询日期 | `2021-12-24` |
| jsonCallBack | JSONP 回调 | `cb` |

**返回 6 条记录**：

| PRODUCT_TYPE | 名称 | 说明 |
|--------------|------|------|
| 40 | 股票（汇总） | 推荐使用 |
| 1 | 主板A | - |
| 2 | 主板B | - |
| 48 | 科创板 | - |
| 43 | 股票回购 | - |
| 12 | 股票（子汇总） | 与40相同 |

**字段**：

| 字段名 | 中文 | 单位 |
|--------|------|------|
| TX_NUM | 挂牌数 | 个 |
| MKT_VALUE | 市价总值 | 亿元 |
| NEGOTIABLE_VALUE | 流通市值 | 亿元 |
| TX_AMOUNT | 成交金额 | 亿元 |
| TX_VOLUME | 成交量 | 亿股 |
| AVG_PROFIT_RATE | 平均市盈率 | 倍 |
| AVG_PROFIT_RATE_FULL | 完整市盈率（滚动） | 倍 |
| TOTAL_MK_CAP_RATE | 换手率 | % |
| SUB_NEW_STOCK_RATE | 次新股换手率 | % |
| EXCHANGE_RATE | 流通换手率 | % |
| TRADING_TX | 交易笔数 | 万笔 |

---

## 三、新版数据源（新网站）

**适用日期**：2021-12-25 ~ 至今

**端点**：`https://query.sse.com.cn/commonQuery.do`

**参数**：

| 参数 | 说明 | 示例值 |
|------|------|--------|
| sqlId | SQL ID（固定值） | `COMMON_SSE_SJ_GPSJ_CJGK_MRGK_C` |
| PRODUCT_CODE | 产品代码 | `01,02,03,11,17` |
| type | 固定值 | `inParams` |
| SEARCH_DATE | 查询日期 | `20211227` |
| jsonCallBack | JSONP 回调 | `cb` |

**产品代码**：

| code | 名称 |
|------|------|
| 01 | 主板A |
| 02 | 主板B |
| 03 | 科创板 |
| 11 | 股票回购 |
| 17 | 全部 |

**字段**：

| 字段名 | 中文 | 单位 |
|--------|------|------|
| LIST_NUM | 挂牌数 | 个 |
| TOTAL_VALUE | 市价总值 | 亿元 |
| NEGO_VALUE | 流通市值 | 亿元 |
| TRADE_AMT | 成交金额 | 亿元 |
| TRADE_VOL | 成交量 | 亿股 |
| AVG_PE_RATE | 平均市盈率 | 倍 |
| TOTAL_TO_RATE | 换手率 | % |
| NEGO_TO_RATE | 流通换手率 | % |

---

## 四、新旧字段对照

| 指标 | 历史字段 | 新版字段 | 单位 |
|------|---------|---------|------|
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

## 五、爬虫自动选择

```python
def get_market_data(date_str):
    date_obj = datetime.strptime(date_str, '%Y-%m-%d')
    if date_obj >= datetime(2021, 12, 25):
        raw = fetch_new_api(date_str)
        if raw: return parse_new(raw)
    raw = fetch_history_api(date_str)
    if raw: return parse_history(raw)
    return None
```
