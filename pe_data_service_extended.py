#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
上证大盘PE数据服务 - 扩展版（支持个股功能）
支持两种数据源模式：
1. 本地SQLite数据库（用于测试）
2. 远程API代理（连接服务器API）
3. 个股功能（集成neoData金融数据API）
"""
import os
import json
import sqlite3
import requests
import re
import sys
from datetime import datetime, timedelta
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# 配置模式
DATA_SOURCE = os.environ.get('DATA_SOURCE', 'remote_api')  # 'local_db' 或 'remote_api'
LOCAL_DB_PATH = os.environ.get('LOCAL_DB_PATH', 'sse_pe_data.db')
REMOTE_API_URL = os.environ.get('REMOTE_API_URL', 'http://101.43.3.247:8082/api/market/pe')

# neoData配置
NEODATA_QUERY_SCRIPT = os.environ.get('NEODATA_QUERY_SCRIPT', '/app/neodata_query.py')

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

def run_neodata_query(query_text, data_type="all"):
    """运行neoData查询"""
    try:
        # 直接导入neodata_query模块中的函数
        import neodata_query
        return neodata_query.query_neodata(query_text, data_type)
    except ImportError:
        # 如果无法导入，尝试作为脚本运行
        try:
            import subprocess
            import sys
            
            cmd = [sys.executable, NEODATA_QUERY_SCRIPT, '--query', query_text]
            if data_type != "all":
                cmd.extend(['--data-type', data_type])
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                try:
                    return json.loads(result.stdout.strip())
                except json.JSONDecodeError:
                    # 尝试从输出中提取JSON
                    lines = result.stdout.strip().split('\n')
                    for line in lines:
                        if line.startswith('{') and line.endswith('}'):
                            try:
                                return json.loads(line)
                            except:
                                pass
                    return None
            else:
                print(f"[ERROR] neoData查询失败: {result.stderr}")
                return None
        except Exception as e:
            print(f"[ERROR] 执行neoData查询异常: {e}")
            return None

def search_stocks(query):
    """搜索股票"""
    result = run_neodata_query(query)
    if not result or 'data' not in result or 'apiData' not in result['data']:
        return []
    
    api_data = result['data']['apiData']
    stocks = []
    
    # 从entity中提取股票信息
    if 'entity' in api_data:
        for entity in api_data['entity']:
            code = entity.get('name', '')  # 通常是代码，如 "600519.SH"
            name = entity.get('code', '')  # 通常是名称，如 "贵州茅台"
            
            # 提取纯数字代码
            match = re.search(r'(\d{6})', code)
            if match:
                code = match.group(1)
            
            if code and name:
                stocks.append({
                    "code": code,
                    "name": name
                })
    
    return stocks

def get_stock_kline(code, days=180):
    """获取股票K线数据"""
    # 使用neoData获取股票信息
    result = run_neodata_query(f"{code}股票行情")
    if not result or 'data' not in result or 'apiData' not in result['data']:
        return {"error": "无法获取股票数据"}
    
    api_data = result['data']['apiData']
    
    # 提取股票名称
    stock_name = ""
    if 'entity' in api_data and api_data['entity']:
        stock_name = api_data['entity'][0].get('code', '')
    
    # 这里应该从apiRecall中解析历史数据，但neoData返回的是实时数据
    # 为了演示，我们生成模拟的历史数据
    kline_data = generate_mock_kline_data(days)
    
    return {
        "name": stock_name or f"股票{code}",
        "kline": kline_data
    }

def generate_mock_kline_data(days):
    """生成模拟的K线数据（用于演示）"""
    import random
    from datetime import datetime, timedelta
    
    data = []
    base_price = 100.0
    current_date = datetime.now() - timedelta(days=days)
    
    for i in range(days):
        date_str = current_date.strftime("%Y-%m-%d")
        
        # 模拟价格波动
        change = random.uniform(-0.03, 0.03)
        close_price = base_price * (1 + change)
        open_price = close_price * random.uniform(0.99, 1.01)
        high_price = max(open_price, close_price) * random.uniform(1.0, 1.02)
        low_price = min(open_price, close_price) * random.uniform(0.98, 1.0)
        volume = random.randint(1000000, 10000000)
        
        data.append({
            "日期": date_str,
            "开盘": round(open_price, 2),
            "收盘": round(close_price, 2),
            "最高": round(high_price, 2),
            "最低": round(low_price, 2),
            "成交量": volume
        })
        
        base_price = close_price
        current_date += timedelta(days=1)
    
    return data

def get_dividend_data(code):
    """获取分红数据"""
    # 这里应该从金融数据API获取真实的分红数据
    # 暂时返回模拟数据
    return {
        "dividends": [
            {
                "date": "2024-06-20",
                "cash": 23.7,
                "bonus": 0,
                "transfer": 0,
                "ex_date": "2024-06-19"
            },
            {
                "date": "2023-06-21",
                "cash": 21.9,
                "bonus": 0,
                "transfer": 0,
                "ex_date": "2023-06-20"
            }
        ]
    }

def get_allotment_data(code):
    """获取配股数据"""
    # 这里应该从金融数据API获取真实的配股数据
    # 暂时返回模拟数据
    return {
        "allotments": [
            {
                "date": "2022-12-08",
                "ex_date": "2022-12-07",
                "price": 109.1,
                "ratio": 0.1
            }
        ]
    }

# ========== 原有的大盘PE API ==========

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
        
        return jsonify({
            "data": data,
            "stats": {
                "count": len(data),
                "latest_date": data[-1]["date"] if data else None,
                "latest_pe": data[-1]["pe"] if data and "pe" in data[-1] else None,
                "avg_pe": round(sum(pe_values) / len(pe_values), 2) if pe_values else None,
                "min_pe": round(min(pe_values), 2) if pe_values else None,
                "max_pe": round(max(pe_values), 2) if pe_values else None
            },
            "data_source": DATA_SOURCE
        })
    except Exception as e:
        return jsonify({"error": str(e), "data_source": DATA_SOURCE}), 500

@app.route('/api/market/pe/latest')
def get_market_pe_latest():
    """获取最新PE数据"""
    try:
        data = get_sse_pe_data()
        if data:
            latest = data[-1]
            return jsonify({
                "date": latest["date"],
                "pe": latest["pe"],
                "turnover": latest.get("turnover"),
                "data_source": DATA_SOURCE
            })
        else:
            return jsonify({
                "error": "暂无数据",
                "data_source": DATA_SOURCE
            }), 404
    except Exception as e:
        return jsonify({"error": str(e), "data_source": DATA_SOURCE}), 500

@app.route('/api/health')
def health_check():
    """健康检查接口"""
    return jsonify({
        "status": "healthy",
        "service": "sse-pe-service",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat(),
        "data_source": DATA_SOURCE
    })

# ========== 新增的个股API ==========

@app.route('/api/search')
def search_stocks_api():
    """搜索股票API"""
    query = request.args.get('q', '').strip()
    if not query:
        return jsonify([])
    
    try:
        stocks = search_stocks(query)
        return jsonify(stocks)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/stock/<code>')
def get_stock_kline_api(code):
    """获取股票K线数据API"""
    try:
        # 验证股票代码格式
        if not re.match(r'^\d{6}$', code):
            return jsonify({"error": "股票代码格式错误，应为6位数字"}), 400
        
        data = get_stock_kline(code)
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/dividend/<code>')
def get_dividend_api(code):
    """获取分红数据API"""
    try:
        if not re.match(r'^\d{6}$', code):
            return jsonify({"error": "股票代码格式错误，应为6位数字"}), 400
        
        data = get_dividend_data(code)
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/allotment/<code>')
def get_allotment_api(code):
    """获取配股数据API"""
    try:
        if not re.match(r'^\d{6}$', code):
            return jsonify({"error": "股票代码格式错误，应为6位数字"}), 400
        
        data = get_allotment_data(code)
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ========== 静态文件服务 ==========

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
    print(f"启动服务，端口: {port}")
    print(f"数据源模式: {DATA_SOURCE}")
    print(f"远程API: {REMOTE_API_URL}")
    print(f"服务已启动: http://localhost:{port}")
    print(f"前端页面: http://localhost:{port}/stock.html")
    print(f"大盘PE API: http://localhost:{port}/api/market/pe")
    print(f"股票搜索API: http://localhost:{port}/api/search?q=茅台")
    print(f"健康检查: http://localhost:{port}/api/health")
    
    app.run(host='0.0.0.0', port=port, debug=False)