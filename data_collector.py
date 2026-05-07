#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据采集器 - 从上证官网获取PE数据并存入InfluxDB
数据来源: sse_market_data_crawler.py (SSE_API_DOC.md)
"""
import os
import time
from datetime import datetime, timedelta
from influxdb_client import InfluxDBClient, Point, WritePrecision

# InfluxDB配置
INFLUXDB_URL = os.environ.get('INFLUXDB_URL', 'http://localhost:8086')
INFLUXDB_TOKEN = os.environ.get('INFLUXDB_TOKEN', 'my-super-secret-token')
INFLUXDB_ORG = os.environ.get('INFLUXDB_ORG', 'stock')
INFLUXDB_BUCKET = os.environ.get('INFLUXDB_BUCKET', 'market_data')

# 上证API请求头
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Referer': 'https://www.sse.com.cn/market/stockdata/overview/day/',
    'Accept': '*/*',
    'Accept-Language': 'zh-CN,zh;q=0.9',
}


def fetch_json(url):
    """获取JSON数据"""
    import requests
    try:
        resp = requests.get(url, headers=HEADERS, timeout=30)
        resp.raise_for_status()
        text = resp.text
        if text.startswith('cb(') and text.endswith(')'):
            json_str = text[3:-1]
        else:
            json_str = text
        import json
        return json.loads(json_str)
    except Exception as e:
        print(f"请求失败: {e}")
        return None


def fetch_market_data_by_new_api(date_str):
    """新版API获取指定日期数据 (2021-12-25至今)"""
    import time
    ts = int(time.time() * 1000)
    url = (
        f"https://query.sse.com.cn/commonQuery.do"
        f"?sqlId=COMMON_SSE_SJ_GPSJ_CJGK_MRGK_C"
        f"&PRODUCT_CODE=01%2C02%2C03%2C11%2C17"
        f"&type=inParams"
        f"&SEARCH_DATE={date_str.replace('-', '')}"
        f"&jsonCallBack=cb&_={ts}"
    )
    data = fetch_json(url)
    return data.get('result') if data else None


def fetch_market_data_by_history_api(date_str):
    """历史API获取指定日期数据 (1999年至2021-12-24)"""
    import time
    ts = int(time.time() * 1000)
    url = (
        f"https://query.sse.com.cn/commonQuery.do"
        f"?sqlId=COMMON_SSE_SJ_GPSJ_CJGK_DAYCJGK_C"
        f"&stockType=90"
        f"&searchDate={date_str}"
        f"&jsonCallBack=cb&_={ts}"
    )
    data = fetch_json(url)
    return data.get('result') if data else None


def get_market_data(date_str):
    """获取指定日期的市场数据（自动选择API）"""
    date_obj = datetime.strptime(date_str, '%Y-%m-%d')
    new_api_start = datetime(2021, 12, 25)
    
    if date_obj >= new_api_start:
        raw_data = fetch_market_data_by_new_api(date_str)
        if raw_data:
            return parse_new_api_data(raw_data, date_str)
    
    raw_data = fetch_market_data_by_history_api(date_str)
    if raw_data:
        return parse_history_api_data(raw_data, date_str)
    
    return None


def parse_new_api_data(result, date_str):
    """解析新版API数据"""
    # 新版API直接返回列表
    records = result if isinstance(result, list) else result.get('result', [])
    data = {}
    for rec in records:
        product_code = rec.get('PRODUCT_CODE', '')
        name = {'01': '主板A', '02': '主板B', '03': '科创板', '11': '股票回购', '17': '全部'}.get(product_code, product_code)
        data[name] = {
            'date': date_str,
            'pe': rec.get('AVG_PE_RATE', 0),
            'total_value': rec.get('TOTAL_VALUE', 0),
            'nego_value': rec.get('NEGO_VALUE', 0),
            'trade_amt': rec.get('TRADE_AMT', 0),
            'trade_vol': rec.get('TRADE_VOL', 0),
            'total_to_rate': rec.get('TOTAL_TO_RATE', 0),
            'nego_to_rate': rec.get('NEGO_TO_RATE', 0),
        }
    return data


def parse_history_api_data(result, date_str):
    """解析历史API数据"""
    # 历史API返回 {'result': {'result': [...]}}
    inner = result.get('result', result) if isinstance(result, dict) else result
    records = inner.get('result', inner) if isinstance(inner, dict) else inner
    data = {}
    for rec in records:
        product_type = rec.get('PRODUCT_TYPE', '')
        name = {'1': '主板A', '2': '主板B', '40': '股票汇总', '43': '股票回购', '48': '科创板'}.get(product_type, product_type)
        data[name] = {
            'date': date_str,
            'pe': rec.get('AVG_PROFIT_RATE', 0),
            'total_value': rec.get('MKT_VALUE', 0),
            'nego_value': rec.get('NEGIABLE_VALUE', 0),
            'trade_amt': rec.get('TX_AMOUNT', 0),
            'trade_vol': rec.get('TX_VOLUME', 0),
            'total_to_rate': rec.get('TOTAL_MK_CAP_RATE', 0),
            'nego_to_rate': rec.get('EXCHANGE_RATE', 0),
        }
    return data


def write_to_influxdb(measurement, tags, fields, timestamp=None):
    """写入数据到InfluxDB"""
    import requests
    try:
        client = InfluxDBClient(url=INFLUXDB_URL, token=INFLUXDB_TOKEN, org=INFLUXDB_ORG)
        write_api = client.write_api()
        
        point = Point(measurement)
        for k, v in tags.items():
            point.tag(k, v)
        for k, v in fields.items():
            point.field(k, v)
        
        if timestamp:
            point.time(timestamp, WritePrecision.NS)
        else:
            point.time(datetime.utcnow(), WritePrecision.NS)
        
        write_api.write(bucket=INFLUXDB_BUCKET, org=INFLUXDB_ORG, record=point)
        client.close()
        return True
    except Exception as e:
        print(f"[ERROR] 写入InfluxDB失败: {e}")
        return False


def save_to_influxdb(data, date_str):
    """保存数据到InfluxDB"""
    try:
        dt = datetime.strptime(date_str, '%Y-%m-%d')
        timestamp = int(dt.timestamp() * 1e9)
    except:
        timestamp = None
    
    for market_type, values in data.items():
        if market_type == '股票汇总' or market_type == '全部':
            tags = {'market': 'SSE', 'type': market_type}
            fields = {
                'pe': float(values.get('pe', 0)) if values.get('pe') else 0,
                'total_value': float(values.get('total_value', 0)) if values.get('total_value') else 0,
                'nego_value': float(values.get('nego_value', 0)) if values.get('nego_value') else 0,
                'trade_amt': float(values.get('trade_amt', 0)) if values.get('trade_amt') else 0,
                'trade_vol': float(values.get('trade_vol', 0)) if values.get('trade_vol') else 0,
                'total_to_rate': float(values.get('total_to_rate', 0)) if values.get('total_to_rate') else 0,
            }
            write_to_influxdb('sse_market', tags, fields, timestamp)
            print(f"  保存: {date_str} {market_type} PE={fields['pe']}")


def collect_date_range(start_date, end_date):
    """采集日期范围的数据"""
    start = datetime.strptime(start_date, '%Y-%m-%d')
    end = datetime.strptime(end_date, '%Y-%m-%d')
    
    current = start
    while current <= end:
        date_str = current.strftime('%Y-%m-%d')
        print(f"\n采集: {date_str}")
        
        data = get_market_data(date_str)
        if data:
            save_to_influxdb(data, date_str)
        else:
            print(f"  无数据或获取失败")
        
        current += timedelta(days=1)
        time.sleep(0.5)  # 避免请求过快


def main():
    print("=" * 60)
    print("数据采集器 - 从上证官网获取PE数据")
    print(f"InfluxDB: {INFLUXDB_URL}")
    print(f"Bucket: {INFLUXDB_BUCKET}")
    print("=" * 60)
    
    # 采集最近5个交易日
    today = datetime.now()
    dates = []
    for i in range(10, 0, -1):
        d = today - timedelta(days=i)
        # 跳过周末
        if d.weekday() < 5:
            dates.append(d.strftime('%Y-%m-%d'))
        if len(dates) >= 5:
            break
    
    print(f"\n采集最近5个交易日: {dates[0]} ~ {dates[-1]}")
    collect_date_range(dates[0], dates[-1])
    
    print("\n数据采集完成!")


if __name__ == '__main__':
    main()
