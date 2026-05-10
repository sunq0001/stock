#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批量数据采集器 - 遍历所有股票，采集K线/分红/配股数据写入InfluxDB

使用方式：
  python collector.py                          # 采集全部股票（默认）
  python collector.py --limit 10               # 只采前10只
  python collector.py --code 000001,000651     # 指定股票
  python collector.py --check                  # 只检查数据覆盖情况，不采集

数据写入由 API 内部完成（pe_data_service_influxdb.py 的写穿缓存逻辑）。
本脚本只需调用对应 HTTP 端点即可触发。
"""
import os
import json
import sys
import time
import requests

API_BASE = os.environ.get('API_BASE', 'http://localhost:5000')
STOCK_LIST_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'stock_list.json')


def load_stock_list():
    """加载股票清单"""
    with open(STOCK_LIST_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)


def check_coverage(stocks):
    """检查InfluxDB中已有数据的股票数量"""
    try:
        from influxdb_client import InfluxDBClient
        c = InfluxDBClient(
            url=os.environ.get('INFLUXDB_URL', 'http://localhost:8086'),
            token=os.environ.get('INFLUXDB_TOKEN', 'my-super-secret-token'),
            org=os.environ.get('INFLUXDB_ORG', 'stock')
        )
        q = c.query_api()
        results = {}
        for m in ['stock_kline', 'stock_dividend', 'stock_allotment']:
            t = q.query(f'from(bucket:"market_data")|>range(start:0)|>filter(fn:(r)=>r._measurement=="{m}")|>group(columns:["code"])|>count()')
            codes = set()
            total = 0
            for t2 in t:
                for r in t2.records:
                    codes.add(r.values.get('code', ''))
                    total += r.get_value() or 0
            results[m] = {'count': total, 'stocks': len(codes)}
        c.close()
        return results
    except ImportError:
        return None


def collect_stock(code, name, index, total):
    """采集单只股票的K线、分红、配股"""
    endpoints = [
        (f'{API_BASE}/api/stock/{code}', 'K线'),
        (f'{API_BASE}/api/dividend/{code}', '分红'),
        (f'{API_BASE}/api/allotment/{code}', '配股'),
    ]
    for url, label in endpoints:
        try:
            r = requests.get(url, timeout=30)
            if r.status_code == 200:
                data = r.json()
                count = 0
                if label == 'K线':
                    count = len(data.get('kline', []))
                elif label == '分红':
                    count = len(data.get('dividends', []))
                elif label == '配股':
                    count = len(data.get('allotments', []))
                print(f'  [{label}] {count}条')
            else:
                print(f'  [{label}] HTTP {r.status_code}')
        except Exception as e:
            print(f'  [{label}] 失败: {e}')
        time.sleep(0.3)  # 避免请求过快


def main():
    print('=' * 60)
    print('批量数据采集器')
    print(f'API: {API_BASE}')
    print(f'股票清单: {STOCK_LIST_PATH}')
    print('=' * 60)

    # 参数解析
    args = sys.argv[1:]
    only_check = '--check' in args
    limit = None
    codes = None

    for i, a in enumerate(args):
        if a == '--limit' and i + 1 < len(args):
            limit = int(args[i + 1])
        elif a == '--code' and i + 1 < len(args):
            codes = args[i + 1].split(',')

    # 加载股票
    stocks = load_stock_list()
    print(f'\n股票总数: {len(stocks)}')

    # 检查覆盖
    coverage = check_coverage(stocks)
    if coverage:
        print(f'\nInfluxDB 当前覆盖情况:')
        for m, info in coverage.items():
            print(f'  {m}: {info["count"]}条数据, {info["stocks"]}只股票')

    if only_check:
        print('\n检查完成（--check 模式，未采集）')
        return

    # 筛选股票
    if codes:
        stock_list = [s for s in stocks if s['c'] in codes]
        print(f'指定股票: {len(stock_list)}只')
    elif limit:
        stock_list = stocks[:limit]
        print(f'限采前 {limit} 只')
    else:
        stock_list = stocks
        print(f'全量采集: {len(stock_list)}只')

    # 逐个采集
    ok = 0
    fail = 0
    for i, s in enumerate(stock_list):
        code, name = s['c'], s['n']
        print(f'\n[{i+1}/{len(stock_list)}] {code} {name}')
        try:
            collect_stock(code, name, i + 1, len(stock_list))
            ok += 1
        except Exception as e:
            print(f'  失败: {e}')
            fail += 1

        # 每10只暂停1秒
        if (i + 1) % 10 == 0:
            time.sleep(1)

    print(f'\n{"=" * 60}')
    print(f'采集完成: 成功 {ok}, 失败 {fail}')

    # 再次检查覆盖
    coverage2 = check_coverage(stocks)
    if coverage2:
        print(f'\n采集后 InfluxDB 覆盖情况:')
        for m, info in coverage2.items():
            print(f'  {m}: {info["count"]}条数据, {info["stocks"]}只股票')


if __name__ == '__main__':
    main()
