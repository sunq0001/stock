#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
上证大盘PE数据服务 - 本地开发版本
支持两种数据源模式：
1. 本地SQLite数据库（用于测试）
2. 远程API代理（连接服务器API）
3. 个股搜索（本地股票列表 + 拼音匹配）
"""
import os
import re
import sys
import json
import sqlite3
import requests
import pandas as pd
from datetime import datetime
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# 配置模式
DATA_SOURCE = os.environ.get('DATA_SOURCE', 'remote_api')  # 'local_db' 或 'remote_api'
LOCAL_DB_PATH = os.environ.get('LOCAL_DB_PATH', 'sse_pe_data.db')
REMOTE_API_URL = os.environ.get('REMOTE_API_URL', 'http://101.43.3.247:8082/api/market/pe')

# ========== 本地股票搜索 ==========

# 内存中的股票列表缓存
_stock_list = []
_stock_list_loaded = False


def _load_stock_list():
    """从 stock_list.json 加载股票列表到内存"""
    global _stock_list, _stock_list_loaded
    if _stock_list_loaded:
        return
    list_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'stock_list.json')
    if not os.path.exists(list_path):
        print(f'[WARN] stock_list.json 不存在，搜索功能不可用: {list_path}')
        _stock_list_loaded = True
        return
    try:
        with open(list_path, 'r', encoding='utf-8') as f:
            _stock_list = json.load(f)
        print(f'[INFO] 加载股票列表成功: {len(_stock_list)} 条')
    except Exception as e:
        print(f'[ERROR] 加载 stock_list.json 失败: {e}')
    _stock_list_loaded = True


def search_stocks(query, limit=15):
    """多维度搜索股票：代码 / 名称 / 全拼 / 首字母
    返回 [{code, name}, ...] 列表，按匹配度排序
    """
    _load_stock_list()
    if not _stock_list:
        return []

    q = query.strip().lower()
    if not q:
        return []

    results = []

    # 判断是否纯数字（股票代码搜索）
    is_code = q.isdigit()

    for s in _stock_list:
        code, name, py_full, py_abbr = s['c'], s['n'], s['p'], s['a']

        # 计算匹配度和类型
        match_type = 0  # 0=不匹配, 1=首字母, 2=全拼, 3=名称包含, 4=名称开头, 5=代码精确

        if is_code:
            # 股票代码匹配
            if code == q:
                match_type = 5
            elif code.startswith(q):
                match_type = 4
        else:
            # 名称匹配（最高优先级）
            if name == q:
                match_type = 5
            elif name.startswith(q):
                match_type = 4
            elif q in name:
                match_type = 3
            # 全拼匹配
            elif py_full.startswith(q):
                match_type = 2
            elif q in py_full:
                match_type = 2
            # 首字母匹配
            elif py_abbr.startswith(q):
                match_type = 1
            elif q in py_abbr:
                match_type = 1

        if match_type > 0:
            results.append({'code': code, 'name': name, '_match': match_type})

    # 按匹配度降序，同匹配度按代码排序（主板优先）
    results.sort(key=lambda x: (-x['_match'], x['code']))

    # 去掉内部排序字段，限制返回数量
    return [{'code': r['code'], 'name': r['name']} for r in results[:limit]]


# ========== neoData API（保留供其他功能使用）==========

NEODATA_URL = 'https://copilot.tencent.com/agenttool/v1/neodata'

def _load_neodata_token():
    """从本地 token 文件或环境变量加载 neoData token"""
    home_token = os.path.join(os.path.expanduser('~'), '.workbuddy', '.neodata_token')
    local_token = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'neodata_token.txt')
    for path in [home_token, local_token]:
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                token = f.read().strip()
                if token and not token.startswith('#'):
                    return token
    return os.environ.get('NEODATA_TOKEN', '')

def _query_neodata(query_text, data_type='api'):
    """调用 neoData API 获取金融数据"""
    token = _load_neodata_token()
    if not token:
        print('[WARN] neoData token 未配置')
        return None
    try:
        resp = requests.post(
            NEODATA_URL,
            headers={'Content-Type': 'application/json', 'Authorization': f'Bearer {token}'},
            json={'query': query_text, 'channel': 'neodata', 'sub_channel': 'workbuddy', 'data_type': data_type},
            timeout=15
        )
        if resp.status_code == 200:
            return resp.json()
        print(f'[WARN] neoData 返回 {resp.status_code}')
        return None
    except Exception as e:
        print(f'[ERROR] neoData 请求失败: {e}')
        return None

# ========== 个股数据函数（AKShare 真实数据源）==========

import akshare as ak

# ========== K线增量加载缓存 ==========
# code -> {"earliest_date": "YYYY-MM-DD", "loading": bool, "all_loaded": bool}
_kline_extent = {}


def _code_to_tx_symbol(code):
    """将6位股票代码转为腾讯格式: 6xxxxx -> sh6xxxxx, 0/3xxxxx -> sz0/3xxxxx"""
    if code.startswith('6'):
        return f'sh{code}'
    else:
        return f'sz{code}'


def _fetch_kline_data(code, days, adjust=''):
    """实际获取K线数据的核心函数（可被同步和异步调用）
    adjust: 'qfq'(前复权), 'hfq'(后复权), ''(不复权)
    默认不复权，确保分红配股时K线有真实跳空缺口
    """
    try:
        import akshare as ak
    except ImportError:
        print('[ERROR] akshare 未安装，无法获取K线数据')
        return None

    from datetime import timedelta
    start_dt = (datetime.now() - timedelta(days=int(days * 1.5))).strftime('%Y%m%d')
    end_dt = datetime.now().strftime('%Y%m%d')
    tx_symbol = _code_to_tx_symbol(code)

    try:
        df = ak.stock_zh_a_hist_tx(
            symbol=tx_symbol,
            start_date=start_dt,
            end_date=end_dt,
            adjust=adjust
        )
        use_tx = True
    except Exception as e:
        print(f'[WARN] 腾讯源失败({e})，尝试东方财富源')
        use_tx = False
        try:
            df = ak.stock_zh_a_hist(
                symbol=code,
                period='daily',
                start_date=start_dt,
                end_date=end_dt,
                adjust=adjust
            )
        except Exception as e2:
            print(f'[ERROR] 东方财富源也失败: {e2}')
            return None

    if df is None or df.empty:
        print(f'[WARN] 未获取到 {code} K线数据')
        return None

    df = df.tail(days)

    kline = []
    for _, row in df.iterrows():
        if use_tx:
            date_val = row['date']
            kline.append({
                "日期": date_val.strftime('%Y-%m-%d') if hasattr(date_val, 'strftime') else str(date_val),
                "开盘": float(row['open']),
                "收盘": float(row['close']),
                "最高": float(row['high']),
                "最低": float(row['low']),
                "成交量": int(row.get('amount', 0))
            })
        else:
            kline.append({
                "日期": row['日期'].strftime('%Y-%m-%d') if hasattr(row['日期'], 'strftime') else str(row['日期']),
                "开盘": float(row['开盘']),
                "收盘": float(row['收盘']),
                "最高": float(row['最高']),
                "最低": float(row['最低']),
                "成交量": int(row['成交量'])
            })

    return kline, use_tx


def _get_stock_name(code):
    """获取股票名称"""
    stock_name = f"股票{code}"
    try:
        result = _query_neodata(f"{code}股票行情")
        if result and 'data' in result and 'apiData' in result['data']:
            entity = result['data']['apiData'].get('entity', [])
            if entity:
                stock_name = entity[0].get('code', stock_name)
    except Exception:
        pass
    return stock_name



def get_stock_kline(code, days=1200):
    """获取股票K线数据（初始加载，返回最近N条）"""
    result = _fetch_kline_data(code, days)
    if result is None:
        return {"name": f"股票{code}", "kline": [], "earliest_date": None, "all_loaded": False}

    kline, use_tx = result
    stock_name = _get_stock_name(code)
    earliest = kline[0]["日期"] if kline else None

    # 记录当前最早日期
    _kline_extent[code] = {"earliest_date": earliest, "loading": False, "all_loaded": False}

    print(f'[INFO] 获取 {code} K线数据成功，共 {len(kline)} 条 ({"腾讯源" if use_tx else "东方财富"})')
    return {"name": stock_name, "kline": kline, "earliest_date": earliest, "all_loaded": False}


def get_stock_kline_before(code, before_date):
    """增量加载更早的K线数据（炒股软件式按需加载）
    before_date: 当前最早日期，从该日期往前再拉5年
    返回: {"kline": [...], "earliest_date": "...", "all_loaded": bool}
    """
    extent = _kline_extent.get(code)
    if not extent:
        return {"kline": [], "earliest_date": before_date, "all_loaded": False}

    # 防止并发重复请求
    if extent.get("loading"):
        return {"kline": [], "earliest_date": before_date, "all_loaded": False}

    extent["loading"] = True
    try:
        # 将 before_date 往前推约5年(1800天)去拉数据
        from datetime import timedelta
        from dateutil.parser import parse as parse_date
        target_start = (parse_date(before_date) - timedelta(days=1800)).strftime('%Y%m%d')
        target_end = before_date.replace('-', '')

        print(f'[INFO] 增量加载 {code} 历史数据: {target_start} ~ {target_end}')

        tx_symbol = _code_to_tx_symbol(code)
        try:
            import akshare as ak
            df = ak.stock_zh_a_hist_tx(
                symbol=tx_symbol,
                start_date=target_start,
                end_date=target_end,
                adjust=''
            )
            use_tx = True
        except Exception as e:
            print(f'[WARN] 腾讯源失败({e})，尝试东方财富源')
            use_tx = False
            try:
                import akshare as ak
                df = ak.stock_zh_a_hist(
                    symbol=code,
                    period='daily',
                    start_date=target_start,
                    end_date=target_end,
                    adjust=''
                )
            except Exception as e2:
                print(f'[ERROR] 增量加载失败: {e2}')
                return {"kline": [], "earliest_date": before_date, "all_loaded": False}

        if df is None or df.empty:
            print(f'[INFO] {code} 已无更早数据，标记为全部加载完成')
            extent["all_loaded"] = True
            return {"kline": [], "earliest_date": before_date, "all_loaded": True}

        # 构建kline
        kline = []
        for _, row in df.iterrows():
            if use_tx:
                date_val = row['date']
                kline.append({
                    "日期": date_val.strftime('%Y-%m-%d') if hasattr(date_val, 'strftime') else str(date_val),
                    "开盘": float(row['open']),
                    "收盘": float(row['close']),
                    "最高": float(row['high']),
                    "最低": float(row['low']),
                    "成交量": int(row.get('amount', 0))
                })
            else:
                kline.append({
                    "日期": row['日期'].strftime('%Y-%m-%d') if hasattr(row['日期'], 'strftime') else str(row['日期']),
                    "开盘": float(row['开盘']),
                    "收盘": float(row['收盘']),
                    "最高": float(row['最高']),
                    "最低": float(row['最低']),
                    "成交量": int(row['成交量'])
                })

        new_earliest = kline[0]["日期"] if kline else before_date
        # 如果拉回来的数据量和请求的差不多，可能还有更早的
        # 如果拉回来的数据量很少（比如<100条），可能已经到头了
        all_loaded = len(kline) < 100
        extent["earliest_date"] = new_earliest
        extent["all_loaded"] = all_loaded

        print(f'[INFO] 增量加载 {code} 完成: +{len(kline)}条, 最早={new_earliest}, all_loaded={all_loaded}')
        return {"kline": kline, "earliest_date": new_earliest, "all_loaded": all_loaded}

    except Exception as e:
        print(f'[ERROR] get_stock_kline_before({code}): {e}')
        return {"kline": [], "earliest_date": before_date, "all_loaded": False}
    finally:
        extent["loading"] = False



def get_dividend_data(code):
    """获取分红数据（AKShare 巨潮资讯）"""
    try:
        import akshare as ak
    except ImportError:
        return {"dividends": []}

    try:
        df = ak.stock_dividend_cninfo(symbol=code)
        if df is None or df.empty:
            return {"dividends": []}

        dividends = []
        for _, row in df.iterrows():
            # 派息比例是每10股分红金额，转换为每股
            cash = float(row.get('派息比例', 0) or 0) / 10.0 if pd.notna(row.get('派息比例')) else 0
            # 送股比例是每10股送几股
            bonus = float(row.get('送股比例', 0) or 0) / 10.0 if pd.notna(row.get('送股比例')) else 0
            # 转增比例是每10股转增几股
            transfer = float(row.get('转增比例', 0) or 0) / 10.0 if pd.notna(row.get('转增比例')) else 0

            # 跳过全零行
            if cash == 0 and bonus == 0 and transfer == 0:
                continue

            ex_date = ''
            if pd.notna(row.get('除权日')):
                ex_date = str(row['除权日'])[:10]

            dividends.append({
                "date": str(row.get('实施方案公告日期', ''))[:10],
                "cash": cash,
                "bonus": bonus,
                "transfer": transfer,
                "ex_date": ex_date
            })

        print(f'[INFO] 获取 {code} 分红数据成功，共 {len(dividends)} 条')
        return {"dividends": dividends}

    except Exception as e:
        print(f'[ERROR] get_dividend_data({code}): {e}')
        return {"dividends": []}


def get_allotment_data(code):
    """获取配股数据（AKShare 巨潮资讯）"""
    try:
        import akshare as ak
    except ImportError:
        return {"allotments": []}

    try:
        df = ak.stock_allotment_cninfo(symbol=code)
        if df is None or df.empty:
            return {"allotments": []}

        allotments = []
        for _, row in df.iterrows():
            price = float(row.get('配股价格', 0) or 0) if pd.notna(row.get('配股价格')) else 0
            ratio = float(row.get('配股比例', 0) or 0) if pd.notna(row.get('配股比例')) else 0

            if price == 0 and ratio == 0:
                continue

            ex_date = ''
            if pd.notna(row.get('除权基准日')):
                ex_date = str(row['除权基准日'])[:10]

            allotments.append({
                "date": str(row.get('上市公告日期', ''))[:10],
                "ex_date": ex_date,
                "price": price,
                "ratio": ratio
            })

        print(f'[INFO] 获取 {code} 配股数据成功，共 {len(allotments)} 条')
        return {"allotments": allotments}

    except Exception as e:
        print(f'[ERROR] get_allotment_data({code}): {e}')
        return {"allotments": []}

# ========== 大盘PE数据函数 ==========

def get_sse_pe_from_local_db(start_date=None, end_date=None):
    """从本地SQLite数据库获取上证PE数据"""
    if not os.path.exists(LOCAL_DB_PATH):
        return []
    
    conn = sqlite3.connect(LOCAL_DB_PATH)
    cursor = conn.cursor()
    
    query = "SELECT date, pe, turnover FROM sse_pe WHERE 1=1"
    params = []
    
    if start_date:
        query += " AND date >= ?"
        params.append(start_date)
    if end_date:
        query += " AND date <= ?"
        params.append(end_date)
    
    query += " ORDER BY date ASC"
    
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    
    return [
        {"date": row[0], "pe": row[1], "turnover": row[2]}
        for row in rows
    ]

def get_sse_pe_from_remote_api(start_date=None, end_date=None):
    """从远程API获取上证PE数据"""
    try:
        params = {}
        if start_date:
            params['start'] = start_date
        if end_date:
            params['end'] = end_date
        
        response = requests.get(REMOTE_API_URL, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            # 远程API返回格式可能不同，需要适配
            if 'data' in data:
                return data['data']
            elif isinstance(data, list):
                return data
        return []
    except Exception as e:
        print(f"[ERROR] 远程API请求失败: {e}")
        return []

def get_sse_pe_data(start_date=None, end_date=None):
    """根据配置获取数据"""
    if DATA_SOURCE == 'local_db':
        return get_sse_pe_from_local_db(start_date, end_date)
    else:  # remote_api
        return get_sse_pe_from_remote_api(start_date, end_date)

@app.route('/api/market/pe')
def get_market_pe():
    """获取上证大盘PE历史数据"""
    start_date = request.args.get('start')
    end_date = request.args.get('end')
    
    try:
        data = get_sse_pe_data(start_date, end_date)
        
        if not data:
            return jsonify({
                "error": "暂无数据，请稍后重试",
                "message": "数据源无数据返回",
                "data_source": DATA_SOURCE
            }), 404
        
        # 计算统计信息
        pe_values = [d["pe"] for d in data if "pe" in d and d["pe"] is not None and d["pe"] > 0]
        if pe_values:
            stats = {
                "min": round(min(pe_values), 2),
                "max": round(max(pe_values), 2),
                "avg": round(sum(pe_values) / len(pe_values), 2),
                "current": round(pe_values[-1], 2),
                "count": len(pe_values)
            }
            
            # 计算当前百分位
            if len(pe_values) > 1:
                sorted_pe = sorted(pe_values)
                current_rank = sum(1 for p in sorted_pe if p <= stats["current"])
                stats["percentile"] = round(current_rank / len(sorted_pe) * 100, 1)
        else:
            stats = {}
        
        return jsonify({
            "data": data,
            "stats": stats,
            "updated_at": datetime.now().isoformat(),
            "data_source": DATA_SOURCE
        })
        
    except Exception as e:
        print(f"[ERROR] get_market_pe failed: {e}")
        return jsonify({"error": str(e), "data_source": DATA_SOURCE}), 500

@app.route('/api/market/pe/latest')
def get_market_pe_latest():
    """获取最新PE数据"""
    try:
        data = get_sse_pe_data()
        if data:
            latest = data[-1]
            return jsonify({
                "date": latest.get("date"),
                "pe": latest.get("pe"),
                "turnover": latest.get("turnover"),
                "data_source": DATA_SOURCE
            })
        else:
            return jsonify({
                "error": "无数据",
                "data_source": DATA_SOURCE
            }), 404
    except Exception as e:
        print(f"[ERROR] get_market_pe_latest failed: {e}")
        return jsonify({"error": str(e), "data_source": DATA_SOURCE}), 500

@app.route('/api/health')
def health_check():
    """健康检查接口"""
    return jsonify({
        "status": "healthy",
        "service": "sse-pe-service",
        "data_source": DATA_SOURCE,
        "timestamp": datetime.now().isoformat()
    })

@app.route('/api/search')
def search_stocks_api():
    """股票搜索接口，供首页搜索框调用"""
    q = request.args.get('q', '').strip()
    if not q:
        return jsonify([])
    try:
        stocks = search_stocks(q)
        return jsonify(stocks)
    except Exception as e:
        print(f'[ERROR] search_stocks_api: {e}')
        return jsonify([])

@app.route('/api/stock/<code>')
def get_stock_kline_api(code):
    """获取股票K线数据（快速返回近期数据）"""
    if not re.match(r'^\d{6}$', code):
        return jsonify({"error": "股票代码格式错误"}), 400
    try:
        return jsonify(get_stock_kline(code))
    except Exception as e:
        print(f'[ERROR] get_stock_kline_api: {e}')
        return jsonify({"error": str(e)}), 500

@app.route('/api/stock/<code>/history')
def get_stock_kline_history_api(code):
    """增量加载更早的K线数据（前端拖到边界时调用）"""
    if not re.match(r'^\d{6}$', code):
        return jsonify({"error": "股票代码格式错误"}), 400
    before_date = request.args.get('before')
    if not before_date:
        return jsonify({"error": "缺少 before 参数"}), 400
    try:
        return jsonify(get_stock_kline_before(code, before_date))
    except Exception as e:
        print(f'[ERROR] get_stock_kline_history_api: {e}')
        return jsonify({"error": str(e)}), 500

@app.route('/api/dividend/<code>')
def get_dividend_api(code):
    """获取分红数据"""
    if not re.match(r'^\d{6}$', code):
        return jsonify({"error": "股票代码格式错误"}), 400
    try:
        return jsonify(get_dividend_data(code))
    except Exception as e:
        print(f'[ERROR] get_dividend_api: {e}')
        return jsonify({"error": str(e)}), 500

@app.route('/api/allotment/<code>')
def get_allotment_api(code):
    """获取配股数据"""
    if not re.match(r'^\d{6}$', code):
        return jsonify({"error": "股票代码格式错误"}), 400
    try:
        return jsonify(get_allotment_data(code))
    except Exception as e:
        print(f'[ERROR] get_allotment_api: {e}')
        return jsonify({"error": str(e)}), 500

# 静态文件服务
@app.route('/')
def serve_index():
    return send_from_directory('html', 'index.html')

@app.route('/stock.html')
def serve_stock():
    return send_from_directory('html', 'stock.html')

# 提供静态文件（CSS、JS等）
@app.route('/<path:filename>')
def serve_static(filename):
    return send_from_directory('html', filename)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8082))
    print(f"启动上证PE数据服务 (数据源: {DATA_SOURCE})")
    print(f"本地数据库路径: {LOCAL_DB_PATH}")
    print(f"远程API地址: {REMOTE_API_URL}")
    print(f"服务端口: {port}")
    
    app.run(host='0.0.0.0', port=port, debug=True)