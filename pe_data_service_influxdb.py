#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
上证大盘PE数据服务 - InfluxDB版本
支持本地InfluxDB和远程API两种模式
"""
import os
import re
import json
import math
import sqlite3
import requests
from datetime import datetime, timedelta
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
import pandas as pd

app = Flask(__name__)
CORS(app)

# 全局替换NaN为null（Flask jsonify默认会把NaN序列化为无效的NaN字符串）
import math as _math
def _clean_nan(obj):
    if isinstance(obj, float) and _math.isnan(obj):
        return None
    if isinstance(obj, dict):
        return {k: _clean_nan(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_clean_nan(v) for v in obj]
    return obj

_orig_jsonify = jsonify
def _safe_jsonify(*args, **kwargs):
    return _orig_jsonify(*[_clean_nan(a) if isinstance(a, (dict, list)) else a for a in args], **{k: _clean_nan(v) if isinstance(v, (dict, list)) else v for k, v in kwargs.items()})
import flask
flask.jsonify = _safe_jsonify

# 配置
DATA_SOURCE = os.environ.get('DATA_SOURCE', 'influxdb')
INFLUXDB_URL = os.environ.get('INFLUXDB_URL', 'http://localhost:18086')
INFLUXDB_TOKEN = os.environ.get('INFLUXDB_TOKEN', 'my-super-secret-token')
INFLUXDB_ORG = os.environ.get('INFLUXDB_ORG', 'stock')
INFLUXDB_BUCKET = os.environ.get('INFLUXDB_BUCKET', 'market_data')

# 腾讯股票API
def fetch_tencent_stock(code):
    """从腾讯API获取股票实时数据"""
    try:
        url = f"http://qt.gtimg.cn/q={code}"
        headers = {'User-Agent': 'Mozilla/5.0'}
        resp = requests.get(url, headers=headers, timeout=5)
        if resp.status_code == 200:
            content = resp.text
            parts = content.split('~')
            if len(parts) > 40:
                return {
                    'name': parts[1],
                    'code': parts[2],
                    'price': float(parts[3]) if parts[3] else 0,
                    'yesterday_close': float(parts[4]) if parts[4] else 0,
                    'open': float(parts[5]) if parts[5] else 0,
                    'volume': int(parts[6]) if parts[6] else 0,
                    'pe': float(parts[39]) if parts[39] else 0,
                }
        return None
    except Exception as e:
        print(f"[ERROR] 获取股票 {code} 失败: {e}")
        return None

def get_influxdb_client():
    """获取InfluxDB客户端"""
    try:
        from influxdb_client import InfluxDBClient
        return InfluxDBClient(url=INFLUXDB_URL, token=INFLUXDB_TOKEN, org=INFLUXDB_ORG)
    except Exception as e:
        print(f"[ERROR] 无法连接InfluxDB: {e}")
        return None

def query_influxdb(measurement, tags=None, time_range=None):
    """从InfluxDB查询数据"""
    try:
        client = get_influxdb_client()
        if not client:
            return []
        
        query_api = client.query_api()
        
        # 构建查询
        tag_filters = ""
        if tags:
            for k, v in tags.items():
                tag_filters += f' and {k}="{v}"'
        
        # 时间范围
        time_filter = ""
        if time_range:
            if 'start' in time_range:
                time_filter += f" and time >= {time_range['start']}"
            if 'end' in time_range:
                time_filter += f" and time <= {time_range['end']}"
        
        query = f'''
        from(bucket: "{INFLUXDB_BUCKET}")
          |> range(start: -30d{time_filter})
          |> filter(fn: (r) => r["_measurement"] == "{measurement}"{tag_filters})
          |> limit(n: 10000)
        '''
        
        tables = query_api.query(query)
        results = []
        for table in tables:
            for record in table.records:
                results.append({
                    'time': record.get_time(),
                    'value': record.get_value(),
                    'field': record.get_field()
                })
        
        client.close()
        return results
    except Exception as e:
        print(f"[ERROR] InfluxDB查询失败: {e}")
        return []

def get_sse_pe_data():
    """从腾讯API获取上证PE数据并存储到InfluxDB"""
    try:
        # 获取上证指数数据
        stock = fetch_tencent_stock('sh000001')
        if stock:
            print(f"[INFO] 上证指数: {stock['name']} 价格: {stock['price']} PE: {stock['pe']}")
            return {
                'date': datetime.now().strftime('%Y%m%d'),
                'pe': stock['pe'] if stock['pe'] > 0 else 15.0,  # 默认PE
                'price': stock['price'],
                'volume': stock['volume']
            }
        return None
    except Exception as e:
        print(f"[ERROR] 获取上证PE失败: {e}")
        return None

# 内存中的股票列表缓存
_stock_list = []
_stock_list_loaded = False

def _load_stock_list():
    global _stock_list, _stock_list_loaded
    if _stock_list_loaded:
        return
    list_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'stock_list.json')
    if os.path.exists(list_path):
        try:
            with open(list_path, 'r', encoding='utf-8') as f:
                _stock_list = json.load(f)
            print(f'[INFO] 加载股票列表: {len(_stock_list)} 条')
        except Exception as e:
            print(f'[ERROR] 加载失败: {e}')
    _stock_list_loaded = True

def search_stocks(query, limit=15):
    _load_stock_list()
    if not _stock_list:
        return []
    q = query.strip().lower()
    if not q:
        return []
    results = []
    is_code = q.isdigit()
    for s in _stock_list:
        code, name, py_full, py_abbr = s['c'], s['n'], s['p'], s['a']
        match_type = 0
        if is_code:
            if code == q:
                match_type = 5
            elif code.startswith(q):
                match_type = 4
        else:
            if name == q:
                match_type = 5
            elif name.startswith(q):
                match_type = 4
            elif q in name:
                match_type = 3
            elif py_full.startswith(q) or q in py_full:
                match_type = 2
            elif py_abbr.startswith(q) or q in py_abbr:
                match_type = 1
        if match_type > 0:
            results.append({'code': code, 'name': name, '_match': match_type})
    results.sort(key=lambda x: (-x['_match'], x['code']))
    return [{'code': r['code'], 'name': r['name']} for r in results[:limit]]

def get_stock_kline(code, days=180):
    """获取股票K线数据"""
    try:
        market_code = f'sz{code}' if code.startswith(('0', '3')) else f'sh{code}'
        # 腾讯API K线
        url = f"https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?_var=kline_dayqfq&param={market_code},day,,,{days},qfq"
        resp = requests.get(url, timeout=10)
        if resp.status_code == 200:
            content = resp.text
            # 解析返回数据
            data_match = re.search(r'kline_dayqfq=(.+)', content)
            if data_match:
                data = json.loads(data_match.group(1))
                day_data = data.get('data', {}).get(market_code, {}).get('qfqday', [])
                kline = []
                for item in day_data[-days:]:
                    if len(item) >= 6:
                        kline.append({
                            "日期": item[0],
                            "开盘": float(item[1]),
                            "收盘": float(item[2]),
                            "最高": float(item[3]),
                            "最低": float(item[4]),
                            "成交量": int(float(item[5])) if item[5] else 0
                        })
                stock_name = fetch_tencent_stock(market_code)
                # 写入InfluxDB持久化
                _save_kline_to_influxdb(code, kline)
                return {
                    "name": stock_name['name'] if stock_name else f"股票{code}",
                    "kline": kline
                }
        return {"name": f"股票{code}", "kline": []}
    except Exception as e:
        print(f"[ERROR] 获取K线失败: {e}")
        return {"name": f"股票{code}", "kline": []}

@app.route('/api/market/pe')
def get_market_pe():
    """获取上证PE数据 - 从InfluxDB读取"""
    try:
        client = get_influxdb_client()
        if not client:
            return jsonify({"error": "无法连接InfluxDB"}), 500
        
        query_api = client.query_api()
        
        # 查询最近365天的数据（用于计算统计）
        query = '''
        from(bucket: "market_data")
          |> range(start: -365d)
          |> filter(fn: (r) => r["_measurement"] == "sse_market")
          |> filter(fn: (r) => r["type"] == "股票汇总" or r["type"] == "全部")
        '''
        
        tables = query_api.query(query)
        
        # 收集所有PE数据
        pe_data = {}
        for table in tables:
            for record in table.records:
                if record.get_field() == 'pe':
                    date = record.get_time().strftime('%Y-%m-%d') if hasattr(record.get_time(), 'strftime') else str(record.get_time())
                    pe_data[date] = record.get_value()
        
        # 按日期排序
        sorted_dates = sorted(pe_data.keys())
        pe_values = [pe_data[d] for d in sorted_dates]
        
        if not pe_values:
            return jsonify({
                "data": [],
                "stats": {"current": 0, "percentile": 0, "avg": 0, "max": 0, "min": 0, "count": 0},
                "data_source": "influxdb"
            })
        
        # 计算统计数据
        latest_date = sorted_dates[-1]
        latest_pe = pe_data[latest_date]
        avg_pe = sum(pe_values) / len(pe_values)
        max_pe = max(pe_values)
        min_pe = min(pe_values)
        
        # 计算当前分位
        below_count = sum(1 for p in pe_values if p < latest_pe)
        percentile = round(below_count / len(pe_values) * 100, 1)
        
        # 获取上证指数价格
        stock = fetch_tencent_stock('sh000001')
        price = stock['price'] if stock else 0
        
        # 返回当前PE数据
        data = [{
            'date': latest_date,
            'pe': latest_pe,
            'price': price,
            'turnover': 0
        }]
        
        client.close()
        
        return jsonify({
            "data": data,
            "stats": {
                "current": latest_pe,
                "percentile": percentile,
                "avg": avg_pe,
                "max": max_pe,
                "min": min_pe,
                "count": len(pe_values)
            },
            "data_source": "influxdb"
        })
    except Exception as e:
        print(f"[ERROR] 获取PE数据失败: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/market/pe/history')
def get_market_pe_history():
    """获取完整市场历史数据 - 按天返回所有产品类别(主板A/B/科创板/全部)的所有字段"""

    # 产品代码说明（用于前端展示）
    PRODUCT_CODES = {
        '01': '主板A', '02': '主板B', '03': '科创板',
        '11': '股票回购', '17': '全部'
    }

    try:
        client = get_influxdb_client()
        if not client:
            return jsonify({"error": "无法连接InfluxDB"}), 500

        query_api = client.query_api()

        # 查询所有字段、所有产品代码
        query = '''
        from(bucket: "market_data")
          |> range(start: 0)
          |> filter(fn: (r) => r["_measurement"] == "sse_market")
          |> sort(columns: ["_time"])
        '''

        tables = query_api.query(query)

        # 按 (日期, product_code) 分组收集所有字段
        product_data = {}       # (date, code) -> {field: value}
        product_names = {}      # code -> name（冗余存储方便读取）

        for table in tables:
            for record in table.records:
                time = record.get_time()
                date = time.strftime('%Y-%m-%d') if hasattr(time, 'strftime') else str(time)[:10]

                code = record.values.get('product_code', '')
                name = record.values.get('product_name', '')
                field = record.get_field()
                value = record.get_value()

                if not code:
                    continue
                product_names[code] = name or PRODUCT_CODES.get(code, code)

                key = (date, code)
                if key not in product_data:
                    product_data[key] = {}
                product_data[key][field] = value

        # 按日期聚合，每天包含所有 product_code 的数据
        date_groups = {}
        for (date, code), fields in product_data.items():
            if date not in date_groups:
                date_groups[date] = {'date': date, 'products': {}}
            # 排除 trade_date（去重辅助字段，前端不需要）
            clean_fields = {k: v for k, v in fields.items() if k != 'trade_date'}
            date_groups[date]['products'][code] = {
                'name': product_names.get(code, code),
                **clean_fields
            }

        kline = list(date_groups.values())
        kline.sort(key=lambda x: x['date'])

        # 提取市盈率（向后兼容）：优先主板A(01)，其次全部(17)
        def _get_pe(day_data):
            products = day_data.get('products', {})
            for pref in ['01', '17']:
                if pref in products:
                    val = products[pref].get('pe_ratio') or products[pref].get('pe')
                    if val is not None and val != '-' and val != '':
                        try:
                            return float(val)
                        except ValueError:
                            pass
            return None

        pe_values = []
        for k in kline:
            pe = _get_pe(k)
            if pe is not None:
                pe_values.append(pe)
                k['pe'] = pe  # 向后兼容

        # 统计
        if pe_values:
            avg_pe = sum(pe_values) / len(pe_values)
            max_pe = max(pe_values)
            min_pe = min(pe_values)
            latest_pe = pe_values[-1]
            below_count = sum(1 for p in pe_values if p < latest_pe)
            percentile = round(below_count / len(pe_values) * 100, 1)
        else:
            avg_pe = max_pe = min_pe = latest_pe = 0
            percentile = 0

        client.close()

        return jsonify({
            "data": kline,
            "stats": {
                "current": latest_pe,
                "percentile": percentile,
                "avg": avg_pe,
                "max": max_pe,
                "min": min_pe,
                "count": len(pe_values)
            },
            "data_source": "influxdb"
        })

    except Exception as e:
        print(f"[ERROR] 获取市场历史数据失败: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/search')
def search_stocks_api():
    q = request.args.get('q', '').strip()
    if not q:
        return jsonify([])
    return jsonify(search_stocks(q))

@app.route('/api/stock/<code>')
def get_stock_kline_api(code):
    if not re.match(r'^\d{6}$', code):
        return jsonify({"error": "股票代码格式错误"}), 400
    return jsonify(get_stock_kline(code))

@app.route('/api/stock/<code>/history')
def get_stock_kline_history(code):
    """增量加载更早的历史K线数据"""
    if not re.match(r'^\d{6}$', code):
        return jsonify({"error": "股票代码格式错误"}), 400
    before_date = request.args.get('before', '')
    try:
        market = 'sz' if code.startswith('0') or code.startswith('3') else 'sh'
        url = f"https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?_var=kline_dayqfq&param={market}{code},day,{before_date},,365,qfq"
        resp = requests.get(url, timeout=10)
        content = resp.text
        data_match = re.search(r'kline_dayqfq=(.+)', content)
        if not data_match:
            return jsonify({"kline": [], "all_loaded": True})
        data = json.loads(data_match.group(1))
        day_data = data.get('data', {}).get(market + code, {}).get('qfqday', [])
        kline = []
        for item in day_data:
            kline.append({
                "日期": item[0], "开盘": float(item[1]), "收盘": float(item[2]),
                "最高": float(item[3]), "最低": float(item[4]),
                "成交量": int(float(item[5])) if len(item) > 5 and item[5] else 0
            })
        # 写入InfluxDB持久化
        _save_kline_to_influxdb(code, kline)
        return jsonify({"kline": kline, "all_loaded": True})
    except Exception as e:
        print(f"[ERROR] 获取历史K线失败 {code}: {e}")
        return jsonify({"kline": [], "all_loaded": False, "error": str(e)})

def _fmt_date(val):
    """统一格式化日期为 YYYY-MM-DD"""
    if val is None or (isinstance(val, float) and (pd.isna(val) or math.isnan(val))):
        return ''
    if hasattr(val, 'strftime'):
        return val.strftime('%Y-%m-%d')
    s = str(val).strip()
    return s[:10] if len(s) >= 10 else s

def _safe_str(val):
    """安全转字符串，处理NaN"""
    if val is None or (isinstance(val, float) and math.isnan(val)):
        return ''
    return str(val).strip()

def _safe_float(val):
    """安全转float，处理NaN"""
    if val is None or (isinstance(val, float) and math.isnan(val)):
        return 0.0
    try:
        v = float(val)
        return v if not math.isnan(v) else 0.0
    except:
        return 0.0


def _market_prefix(code):
    """根据股票代码判断市场前缀"""
    return 'sz' if code.startswith(('0', '3')) else 'sh'


def _save_kline_to_influxdb(code, kline_list):
    """将个股K线数据写入InfluxDB（stock_kline measurement）"""
    try:
        from influxdb_client import Point
        from influxdb_client.client.write_api import SYNCHRONOUS

        client = get_influxdb_client()
        if not client:
            return

        write_api = client.write_api(write_options=SYNCHRONOUS)
        points = []
        for item in kline_list:
            date_str = item.get('日期', '')
            if not date_str:
                continue
            try:
                ts = datetime.strptime(date_str, '%Y-%m-%d')
            except ValueError:
                continue

            point = Point('stock_kline')
            point.tag('code', code)
            point.field('trade_date', date_str)
            point.field('open', _safe_float(item.get('开盘')))
            point.field('close', _safe_float(item.get('收盘')))
            point.field('high', _safe_float(item.get('最高')))
            point.field('low', _safe_float(item.get('最低')))
            point.field('volume', _safe_float(item.get('成交量')))
            point.time(ts)
            points.append(point)

        if points:
            write_api.write(bucket=INFLUXDB_BUCKET, org=INFLUXDB_ORG, record=points)
            print(f"[INFO] K线写入InfluxDB: {code} {len(points)}条", flush=True)
        client.close()
    except Exception as e:
        print(f"[WARN] K线写入InfluxDB失败: {code} {e}", flush=True)


def _save_dividend_to_influxdb(code, dividend_list):
    """将分红数据写入InfluxDB（stock_dividend measurement）"""
    try:
        from influxdb_client import Point
        from influxdb_client.client.write_api import SYNCHRONOUS

        client = get_influxdb_client()
        if not client:
            return

        write_api = client.write_api(write_options=SYNCHRONOUS)
        points = []
        for item in dividend_list:
            d = item.get('ex_date') or item.get('date')
            if not d:
                continue
            try:
                ts = datetime.strptime(d, '%Y-%m-%d')
            except ValueError:
                continue

            point = Point('stock_dividend')
            point.tag('code', code)
            point.field('ex_date', d)
            point.field('date', item.get('date', ''))
            point.field('cash', _safe_float(item.get('cash')))
            point.field('bonus', _safe_float(item.get('bonus')))
            point.field('transfer', _safe_float(item.get('transfer')))
            point.field('desc', item.get('desc', ''))
            point.time(ts)
            points.append(point)

        if points:
            write_api.write(bucket=INFLUXDB_BUCKET, org=INFLUXDB_ORG, record=points)
            print(f"[INFO] 分红写入InfluxDB: {code} {len(points)}条", flush=True)
        client.close()
    except Exception as e:
        print(f"[WARN] 分红写入InfluxDB失败: {code} {e}", flush=True)


def _save_allotment_to_influxdb(code, allotment_list):
    """将配股数据写入InfluxDB（stock_allotment measurement）"""
    try:
        from influxdb_client import Point
        from influxdb_client.client.write_api import SYNCHRONOUS

        client = get_influxdb_client()
        if not client:
            return

        write_api = client.write_api(write_options=SYNCHRONOUS)
        points = []
        for item in allotment_list:
            d = item.get('ex_date') or item.get('date')
            if not d:
                continue
            try:
                ts = datetime.strptime(d, '%Y-%m-%d')
            except ValueError:
                continue

            point = Point('stock_allotment')
            point.tag('code', code)
            point.field('ex_date', d)
            point.field('date', item.get('date', ''))
            point.field('ratio', _safe_float(item.get('ratio')))
            point.field('price', _safe_float(item.get('price')))
            point.field('pay_start', item.get('pay_start', ''))
            point.field('pay_end', item.get('pay_end', ''))
            point.time(ts)
            points.append(point)

        if points:
            write_api.write(bucket=INFLUXDB_BUCKET, org=INFLUXDB_ORG, record=points)
            print(f"[INFO] 配股写入InfluxDB: {code} {len(points)}条", flush=True)
        client.close()
    except Exception as e:
        print(f"[WARN] 配股写入InfluxDB失败: {code} {e}", flush=True)


@app.route('/api/dividend/<code>')
def get_dividend_data(code):
    """获取个股分红送转数据 - 使用akshare"""
    if not re.match(r'^\d{6}$', code):
        return jsonify({"error": "股票代码格式错误"}), 400
    try:
        import akshare as ak
        div = ak.stock_dividend_cninfo(symbol=code)
        dividends = []
        for _, row in div.iterrows():
            cash = _safe_float(row.get('派息比例'))
            bonus = _safe_float(row.get('送股比例'))
            transfer = _safe_float(row.get('转增比例'))
            dividends.append({
                'date': _fmt_date(row.get('股权登记日')),
                'ex_date': _fmt_date(row.get('除权日')),
                'cash': cash / 10.0 if cash else 0.0,
                'bonus': bonus / 10.0 if bonus else 0.0,
                'transfer': transfer / 10.0 if transfer else 0.0,
                'rights': 0,
                'desc': _safe_str(row.get('实施方案分红说明')),
                'report_time': _safe_str(row.get('报告时间'))
            })
        # 写入InfluxDB持久化
        _save_dividend_to_influxdb(code, dividends)
        return jsonify({"dividends": dividends})
    except ImportError:
        return jsonify({"dividends": [], "error": "akshare未安装"})
    except Exception as e:
        print(f"[ERROR] 获取分红数据失败 {code}: {e}")
        return jsonify({"dividends": [], "error": str(e)})

@app.route('/api/allotment/<code>')
def get_allotment_data(code):
    """获取个股配股数据 - 使用akshare"""
    if not re.match(r'^\d{6}$', code):
        return jsonify({"error": "股票代码格式错误"}), 400
    try:
        import akshare as ak
        all = ak.stock_allotment_cninfo(symbol=code)
        allotments = []
        for _, row in all.iterrows():
            price = _safe_float(row.get('配股价格'))
            ratio = _safe_float(row.get('配股比例'))
            allotments.append({
                'date': _fmt_date(row.get('股权登记日')),
                'ex_date': _fmt_date(row.get('除权基准日')),
                'price': price,
                'ratio': ratio / 10.0 if ratio else 0.0,
                'pay_start': _fmt_date(row.get('配股缴款起始日')),
                'pay_end': _fmt_date(row.get('配股缴款截止日')),
            })
        # 写入InfluxDB持久化
        _save_allotment_to_influxdb(code, allotments)
        return jsonify({"allotments": allotments})
    except ImportError:
        return jsonify({"allotments": [], "error": "akshare未安装"})
    except Exception as e:
        print(f"[ERROR] 获取配股数据失败 {code}: {e}")
        return jsonify({"allotments": [], "error": str(e)})

@app.route('/api/stock/<code>/realtime')
def get_stock_realtime(code):
    stock = fetch_tencent_stock(f'sh{code}' if code.startswith('6') else f'sz{code}')
    if stock:
        return jsonify(stock)
    return jsonify({"error": "无法获取数据"}), 500

@app.route('/api/health')
def health_check():
    return jsonify({
        "status": "healthy",
        "data_source": DATA_SOURCE,
        "timestamp": datetime.now().isoformat()
    })

@app.route('/')
def serve_index():
    return send_from_directory('html', 'index.html')

@app.route('/market.html')
def serve_market():
    return send_from_directory('html', 'market.html')

@app.route('/<path:filename>')
def serve_static(filename):
    return send_from_directory('html', filename)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 18082))
    print(f"启动服务，数据源: {DATA_SOURCE}")
    print(f"服务端口: {port}")
    app.run(host='0.0.0.0', port=port, debug=False)