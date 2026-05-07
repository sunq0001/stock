#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
上证交易所市场数据爬虫 - 完整历史数据版本

数据来源:
- 旧网站(历史API): 1999年 ~ 2021-12-24
  https://www.sse.com.cn/market/stockdata/overview/day/index_his.shtml
- 新网站(新版API): 2021-12-25 ~ 至今
  https://www.sse.com.cn/market/stockdata/overview/day/

支持: 1999年至今的完整历史数据
"""

import requests
import json
import time
import os
from datetime import datetime, timedelta


def format_date(raw_date, fallback):
    """格式化日期字符串，支持 YYYYMMDD 和 YYYY-MM-DD 格式"""
    if not raw_date:
        return fallback
    # 如果是 YYYYMMDD 格式
    if len(raw_date) == 8 and raw_date.isdigit():
        return f"{raw_date[:4]}-{raw_date[4:6]}-{raw_date[6:8]}"
    # 如果是 YYYY-MM-DD 格式
    if len(raw_date) >= 10:
        return raw_date[:10]
    return fallback


# ==================== InfluxDB 配置 ====================
INFLUXDB_CONFIG = {
    'url': os.environ.get('INFLUXDB_URL', 'http://localhost:8086'),
    'token': os.environ.get('INFLUXDB_TOKEN', 'my-super-secret-token'),
    'org': os.environ.get('INFLUXDB_ORG', 'stock'),
    'bucket': os.environ.get('INFLUXDB_BUCKET', 'market_data'),
    'measurement': 'sse_market',
}


def get_influxdb_client():
    """获取InfluxDB客户端"""
    try:
        from influxdb_client import InfluxDBClient
        return InfluxDBClient(
            url=INFLUXDB_CONFIG['url'],
            token=INFLUXDB_CONFIG['token'],
            org=INFLUXDB_CONFIG['org']
        )
    except ImportError:
        print("[ERROR] 请先安装 influxdb-client: pip install influxdb-client")
        return None


def get_existing_dates(start_date, end_date):
    """查询InfluxDB中已存在的日期"""
    client = get_influxdb_client()
    if not client:
        return set()
    
    try:
        query_api = client.query_api()
        query = f'''
        import "influxdata/influxdb/schema"
        schema.measurementFieldKeys(bucket: "{INFLUXDB_CONFIG['bucket']}", measurement: "{INFLUXDB_CONFIG['measurement']}")
        '''
        # 简化：查询指定日期范围内已有的trade_date
        query = f'''
        from(bucket: "{INFLUXDB_CONFIG['bucket']}")
          |> range(start: {start_date}, stop: {end_date})
          |> filter(fn: (r) => r["_measurement"] == "{INFLUXDB_CONFIG['measurement']}")
          |> filter(fn: (r) => r["_field"] == "trade_date")
          |> distinct(column: "_value")
        '''
        tables = query_api.query(query)
        existing = set()
        for table in tables:
            for record in table.records:
                existing.add(record.get_value())
        return existing
    except Exception as e:
        print(f"[WARN] 查询已有数据失败: {e}")
        return set()
    finally:
        client.close()


def write_to_influxdb(date_str, market_data):
    """将一天的数据写入InfluxDB"""
    client = get_influxdb_client()
    if not client:
        return False
    
    try:
        from influxdb_client import Point
        from influxdb_client.client.write_api import SYNCHRONOUS
        
        write_api = client.write_api(write_options=SYNCHRONOUS)
        points = []
        
        for product_code, data in market_data.items():
            # 构建 Point
            point = Point(INFLUXDB_CONFIG['measurement'])
            point.tag('product_code', str(product_code))
            point.tag('product_name', data.get('product_name', ''))
            
            # 添加 trade_date（用于去重查询）
            trade_date = data.get('trade_date', date_str)
            point.field('trade_date', trade_date)
            
            # 数值字段（转换'-'为None）
            def to_float(val):
                if val is None or val == '-' or val == '':
                    return None
                try:
                    return float(val)
                except:
                    return None
            
            # 添加所有数值字段
            fields_to_write = [
                ('pe_ratio', 'pe_ratio'),
                ('pe_ratio_full', 'pe_ratio_full'),
                ('listed_count', 'listed_count'),
                ('market_cap', 'market_cap'),
                ('market_cap_full', 'market_cap_full'),
                ('float_market_cap', 'float_market_cap'),
                ('float_market_cap_full', 'float_market_cap_full'),
                ('trade_amount', 'trade_amount'),
                ('trade_amount_full', 'trade_amount_full'),
                ('trade_vol', 'trade_vol'),
                ('trade_vol_full', 'trade_vol_full'),
                ('turnover_rate', 'turnover_rate'),
                ('turnover_rate_full', 'turnover_rate_full'),
                ('float_turnover_rate', 'float_turnover_rate'),
                ('float_turnover_rate_full', 'float_turnover_rate_full'),
            ]
            
            for field_key, field_name in fields_to_write:
                val = to_float(data.get(field_key))
                if val is not None:
                    point.field(field_name, val)
            
            # 使用日期作为时间戳
            timestamp = datetime.strptime(trade_date, '%Y-%m-%d')
            point.time(timestamp)
            
            points.append(point)
        
        if points:
            write_api.write(bucket=INFLUXDB_CONFIG['bucket'], org=INFLUXDB_CONFIG['org'], record=points)
            write_api.close()
            return True
        return False
        
    except Exception as e:
        print(f"[ERROR] 写入InfluxDB失败: {e}")
        return False
    finally:
        client.close()


def batch_crawl_and_save(start_date, end_date, skip_existing=True):
    """
    批量爬取并保存到InfluxDB
    
    Args:
        start_date: 开始日期 YYYY-MM-DD
        end_date: 结束日期 YYYY-MM-DD
        skip_existing: 是否跳过已有数据
    """
    start = datetime.strptime(start_date, '%Y-%m-%d')
    end = datetime.strptime(end_date, '%Y-%m-%d')
    
    # 如果需要跳过已有数据
    existing_dates = set()
    if skip_existing:
        existing_dates = get_existing_dates(start_date, end_date)
        print(f"[INFO] 已存在 {len(existing_dates)} 天的数据，将跳过")
    
    total_days = (end - start).days + 1
    success_count = 0
    skip_count = 0
    fail_count = 0
    
    current = start
    while current <= end:
        date_str = current.strftime('%Y-%m-%d')
        
        # 跳过已有数据
        if skip_existing and date_str in existing_dates:
            print(f"[SKIP] {date_str} - 数据已存在")
            skip_count += 1
            current += timedelta(days=1)
            continue
        
        # 爬取数据
        print(f"[CRAWL] {date_str}...", end=' ', flush=True)
        data = get_market_data(date_str)
        
        if data:
            # 写入InfluxDB
            if write_to_influxdb(date_str, data):
                print(f"[OK] ({len(data)} 个板块)")
                success_count += 1
            else:
                print("[FAIL] 写入失败")
                fail_count += 1
        else:
            print("[FAIL] 无数据")
            fail_count += 1
        
        # 避免请求过快
        time.sleep(0.3)
        current += timedelta(days=1)
    
    print(f"\n[完成] 成功: {success_count}, 跳过: {skip_count}, 失败: {fail_count}")
    print(f"[总计] {total_days} 天")
    return success_count, skip_count, fail_count

# 请求头
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Referer': 'https://www.sse.com.cn/market/stockdata/overview/day/index_his.shtml',
    'Accept': '*/*',
    'Accept-Language': 'zh-CN,zh;q=0.9',
}

# 产品类型映射（历史API）
HISTORY_PRODUCT_TYPE_MAP = {
    '1': {'name': '主板A', 'display_name': '主板A'},
    '2': {'name': '主板B', 'display_name': '主板B'},
    '12': {'name': '股票(汇总)', 'display_name': '股票'},
    '40': {'name': '股票(完整)', 'display_name': '股票'},
    '43': {'name': '股票回购', 'display_name': '股票回购'},
    '48': {'name': '科创板', 'display_name': '科创板'},
}


def fetch_json(url):
    """获取JSON数据"""
    try:
        resp = requests.get(url, headers=HEADERS, timeout=30)
        resp.raise_for_status()
        
        text = resp.text
        # 解析 JSONP: cb({...})
        if text.startswith('cb(') and text.endswith(')'):
            json_str = text[3:-1]
        elif '(' in text and text.endswith(')'):
            json_str = text[text.find('(')+1:-1]
        else:
            json_str = text
            
        return json.loads(json_str)
    except Exception as e:
        print(f"请求失败: {e}")
        return None


def fetch_market_data_by_new_api(date_str):
    """
    使用新版API获取指定日期的数据 (2021-12-25至今，新网站)
    date_str: YYYY-MM-DD
    """
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
    if not data or 'result' not in data:
        return None
    
    return data['result']


def fetch_market_data_by_history_api(date_str):
    """
    使用历史API获取指定日期的数据 (1999年至2021-12-24，旧网站)
    date_str: YYYY-MM-DD
    """
    ts = int(time.time() * 1000)
    
    url = (
        f"https://query.sse.com.cn/commonQuery.do"
        f"?sqlId=COMMON_SSE_SJ_GPSJ_CJGK_DAYCJGK_C"
        f"&stockType=90"
        f"&searchDate={date_str}"
        f"&jsonCallBack=cb&_={ts}"
    )
    
    data = fetch_json(url)
    if not data or 'result' not in data:
        return None
    
    return data['result']


def parse_history_data(raw_data, date_str):
    """解析历史API返回的数据"""
    market_data = {}
    
    for item in raw_data:
        product_type = str(item.get('PRODUCT_TYPE', ''))
        if product_type not in HISTORY_PRODUCT_TYPE_MAP:
            continue
        
        product_info = HISTORY_PRODUCT_TYPE_MAP[product_type]
        
        market_data[product_type] = {
            'trade_date': format_date(item.get('CAL_DATE', ''), date_str),
            'product_code': product_type,
            'product_name': product_info['name'],
            'display_name': product_info['display_name'],
            # 挂牌数 (TX_NUM)
            'listed_count': item.get('TX_NUM', '-'),
            # 市盈率
            'pe_ratio': item.get('AVG_PROFIT_RATE', '-'),
            'pe_ratio_full': item.get('AVG_PROFIT_RATE_FULL', '-'),
            # 市值
            'market_cap': item.get('MKT_VALUE', '-'),  # 市价总值
            'market_cap_full': item.get('MKT_VALUE_FULL', '-'),
            'float_market_cap': item.get('NEGOTIABLE_VALUE', '-'),  # 流通市值
            'float_market_cap_full': item.get('NEGOTIABLE_VALUE_FULL', '-'),
            # 成交
            'trade_amount': item.get('TX_AMOUNT', '-'),  # 成交金额（亿）
            'trade_amount_full': item.get('TX_AMOUNT_FULL', '-'),
            'trade_vol': item.get('TX_VOLUME', '-'),  # 成交量（亿股）
            'trade_vol_full': item.get('TX_VOLUME_FULL', '-'),
            # 换手率
            'turnover_rate': item.get('TOTAL_MK_CAP_RATE', '-'),  # 总市值换手率
            'turnover_rate_full': item.get('TOTAL_MK_CAP_RATE', '-'),
            'float_turnover_rate': item.get('EXCHANGE_RATE', '-'),  # 流通换手率
            'float_turnover_rate_full': item.get('EXCHANGE_RATE_FULL', '-'),
            # 次新股换手率
            'sub_new_stock_rate': item.get('SUB_NEW_STOCK_RATE', '-'),
            # 交易额（万笔）
            'trading_tx': item.get('TRADING_TX', '-'),
        }
    
    return market_data


def parse_new_api_data(raw_data):
    """解析新版API返回的数据"""
    PRODUCT_MAP = {
        '01': {'name': '主板A', 'col_name': '主板A'},
        '02': {'name': '主板B', 'col_name': '主板B'},
        '03': {'name': '科创板', 'col_name': '科创板'},
        '11': {'name': '股票回购', 'col_name': '股票回购'},
        '17': {'name': '股票', 'col_name': '股票'},
    }
    
    market_data = {}
    for item in raw_data:
        code = item.get('PRODUCT_CODE', '')
        if code not in PRODUCT_MAP:
            continue
        
        product_info = PRODUCT_MAP[code]
        
        # 处理日期格式：YYYYMMDD -> YYYY-MM-DD
        raw_date = item.get('TRADE_DATE', '')
        if raw_date and len(raw_date) == 8:
            trade_date = f"{raw_date[:4]}-{raw_date[4:6]}-{raw_date[6:8]}"
        else:
            trade_date = raw_date
        
        market_data[code] = {
            'trade_date': trade_date,
            'product_code': code,
            'product_name': product_info['name'],
            'display_name': product_info['col_name'],
            'listed_count': item.get('LIST_NUM', '-'),
            'market_cap': item.get('TOTAL_VALUE', '-'),
            'float_market_cap': item.get('NEGO_VALUE', '-'),
            'trade_amount': item.get('TRADE_AMT', '-'),
            'trade_vol': item.get('TRADE_VOL', '-'),
            'deal_num': item.get('TRADE_NUM', '-'),
            'pe_ratio': item.get('AVG_PE_RATE', '-'),
            'turnover_rate': item.get('TOTAL_TO_RATE', '-'),
            'float_turnover_rate': item.get('NEGO_TO_RATE', '-'),
        }
    
    return market_data


def get_market_data(date_str):
    """
    获取指定日期的市场数据
    自动选择合适的API
    date_str: YYYY-MM-DD
    
    数据源分界:
    - 旧网站(历史API): 1999 ~ 2021-12-24
    - 新网站(新版API): 2021-12-25 ~ 至今
    """
    # 转换日期
    date_obj = datetime.strptime(date_str, '%Y-%m-%d')
    new_api_start = datetime(2021, 12, 25)  # 新网站启用日期
    
    if date_obj >= new_api_start:
        # 使用新版API (2021-12-25起)
        raw_data = fetch_market_data_by_new_api(date_str)
        if raw_data:
            return parse_new_api_data(raw_data)
    
    # 使用历史API（支持1999年至2021-12-24）
    raw_data = fetch_market_data_by_history_api(date_str)
    if raw_data:
        return parse_history_data(raw_data, date_str)
    
    return None


def print_market_data(date_str, data):
    """打印市场数据表格"""
    if not data:
        print(f"[{date_str}] 无数据")
        return
    
    print(f"\n{'='*120}")
    print(f"上证交易所市场数据 - 日期: {date_str}")
    print(f"{'='*120}")
    
    fields = [
        ('挂牌数', 'listed_count'),
        ('市盈率', 'pe_ratio'),
        ('市价总值(亿)', 'market_cap'),
        ('流通市值(亿)', 'float_market_cap'),
        ('成交金额(亿)', 'trade_amount'),
        ('成交量(亿股)', 'trade_vol'),
        ('换手率(%)', 'turnover_rate'),
        ('次新股换手率(%)', 'sub_new_stock_rate'),
        ('流通换手率(%)', 'float_turnover_rate'),
    ]
    
    # 按显示顺序排列产品
    product_order = ['40', '1', '2', '48', '43']
    
    # 过滤存在的
    existing = [p for p in product_order if p in data]
    
    # 打印表头
    headers = ['指标'] + [data.get(p, {}).get('display_name', p) for p in existing]
    print(' | '.join([h.ljust(16) for h in headers]))
    print('-' * 100)
    
    # 打印每行
    for label, field in fields:
        row = [label.ljust(16)]
        for code in existing:
            value = data[code].get(field, '-')
            row.append(str(value).ljust(16))
        print(' | '.join(row))
    
    print(f"{'='*100}\n")


def fetch_date_range(start_date, end_date):
    """获取日期范围内的所有交易日数据"""
    start = datetime.strptime(start_date, '%Y-%m-%d')
    end = datetime.strptime(end_date, '%Y-%m-%d')
    
    all_data = {}
    current = start
    
    while current <= end:
        date_str = current.strftime('%Y-%m-%d')
        print(f"正在获取 {date_str}...", end=' ')
        
        data = get_market_data(date_str)
        if data:
            all_data[date_str] = data
            print(f"[OK] ({len(data)} 个板块)")
        else:
            print("[FAIL] 无数据")
        
        time.sleep(0.3)
        current += timedelta(days=1)
    
    return all_data


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='上证交易所市场数据爬虫 - 完整历史版本')
    parser.add_argument('--date', help='指定日期 (YYYY-MM-DD)，默认今天')
    parser.add_argument('--start', help='开始日期 (YYYY-MM-DD)')
    parser.add_argument('--end', help='结束日期 (YYYY-MM-DD)')
    parser.add_argument('--save', action='store_true', help='保存数据到InfluxDB')
    parser.add_argument('--no-skip', action='store_true', help='不要跳过已有数据（会覆盖）')
    parser.add_argument('--init', help='初始化历史数据: --init 1999-01-01,2025-12-31')
    
    args = parser.parse_args()
    
    # 初始化历史数据
    if args.init:
        try:
            start_dt, end_dt = args.init.split(',')
            print(f"[初始化] 开始爬取历史数据: {start_dt} ~ {end_dt}")
            success, skip, fail = batch_crawl_and_save(start_dt, end_dt, skip_existing=not args.no_skip)
            print(f"[完成] 成功: {success}, 跳过: {skip}, 失败: {fail}")
        except Exception as e:
            print(f"[错误] {e}")
    # 批量范围爬取
    elif args.start and args.end:
        if args.save:
            print(f"[批量保存] 开始日期: {args.start}, 结束日期: {args.end}")
            success, skip, fail = batch_crawl_and_save(args.start, args.end, skip_existing=not args.no_skip)
            print(f"[完成] 成功: {success}, 跳过: {skip}, 失败: {fail}")
        else:
            data = fetch_date_range(args.start, args.end)
            print(f"\n共获取 {len(data)} 天的数据")
    # 单日爬取
    else:
        date_str = args.date or datetime.now().strftime('%Y-%m-%d')
        data = get_market_data(date_str)
        print_market_data(date_str, data)
        
        if args.save and data:
            print(f"\n[保存到InfluxDB] {date_str}")
            if write_to_influxdb(date_str, data):
                print("[成功] 数据已保存到InfluxDB")
            else:
                print("[失败] 保存失败")
        
        if data:
            print("\n原始数据字段:")
            for code, item in list(data.items())[:2]:
                print(f"\n{code} ({item['product_name']}):")
                for k, v in item.items():
                    if k not in ['product_code', 'product_name', 'display_name']:
                        print(f"  {k}: {v}")
