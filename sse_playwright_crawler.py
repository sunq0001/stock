#!/usr/bin/env python3
"""
简单版上证PE数据爬虫
使用API直接获取数据，避免浏览器操作
"""

import sqlite3
import json
import requests
import time
from datetime import datetime, timedelta

# 数据库路径
DB_PATH = "/app/data/sse_pe_data.db"
JSON_PATH = "/app/html/pe_daily.json"

def init_db():
    """初始化数据库"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS sse_pe (
            date TEXT PRIMARY KEY,
            pe REAL,
            turnover REAL,
            volume REAL,
            amount REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            source TEXT
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS crawl_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT,
            success INTEGER,
            error TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def save_to_db(date, pe_data):
    """保存数据到数据库"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    try:
        c.execute('''
            INSERT OR REPLACE INTO sse_pe (date, pe, turnover, volume, amount, source)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (date, pe_data.get('pe'), pe_data.get('turnover'), 
              pe_data.get('volume'), pe_data.get('amount'), 'api'))
        conn.commit()
        print(f"[INFO] 数据保存成功: {date}")
    except Exception as e:
        print(f"[ERROR] 保存数据失败: {e}")
    finally:
        conn.close()

def log_crawl(date, success, error=None):
    """记录爬取日志"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    try:
        c.execute('''
            INSERT INTO crawl_log (date, success, error)
            VALUES (?, ?, ?)
        ''', (date, 1 if success else 0, error))
        conn.commit()
    except Exception as e:
        print(f"[ERROR] 记录日志失败: {e}")
    finally:
        conn.close()

def update_json():
    """更新JSON文件"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    try:
        c.execute('''
            SELECT date, pe FROM sse_pe 
            WHERE date >= date('now', '-365 days')
            ORDER BY date
        ''')
        rows = c.fetchall()
        
        data = [{"date": row[0], "pe": row[1]} for row in rows]
        
        with open(JSON_PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        print(f"[INFO] JSON文件更新成功，共 {len(data)} 条记录")
    except Exception as e:
        print(f"[ERROR] 更新JSON失败: {e}")
    finally:
        conn.close()

def get_pe_data_from_api(target_date):
    """从API获取PE数据"""
    date_str = target_date.strftime("%Y%m%d")
    
    # 尝试上证交易所的API
    # 根据历史经验，上证交易所的API endpoint
    api_urls = [
        f"https://query.sse.com.cn/commonQuery.do?jsonCallBack=&sqlId=COMMON_SSE_CP_GPJCTJZ_GPLB_OVERVIEW_L&SEARCH_DATE={date_str}",
        f"https://www.sse.com.cn/market/stockdata/overview/day/detail/?date={date_str}"
    ]
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Referer': 'https://www.sse.com.cn/'
    }
    
    for api_url in api_urls:
        try:
            print(f"[INFO] 尝试API: {api_url}")
            response = requests.get(api_url, headers=headers, timeout=30)
            
            if response.status_code == 200:
                # 尝试解析数据
                content = response.text
                
                # 简单尝试提取PE值
                # 上证官网的PE数据通常以"市盈率"或"PE"开头
                import re
                
                # 尝试查找市盈率数据
                pe_patterns = [
                    r'市盈率[^0-9]*([0-9.]+)',
                    r'PE[^0-9]*([0-9.]+)',
                    r'pe[^0-9]*([0-9.]+)',
                    r'"pe"\s*:\s*([0-9.]+)',
                    r'市盈率.*?([0-9.]+)'
                ]
                
                for pattern in pe_patterns:
                    matches = re.search(pattern, content, re.IGNORECASE)
                    if matches:
                        pe_value = float(matches.group(1))
                        print(f"[INFO] 找到PE数据: {pe_value}")
                        return {
                            "date": target_date.strftime("%Y-%m-%d"),
                            "pe": pe_value,
                            "turnover": None,
                            "volume": None,
                            "amount": None
                        }
                
                # 如果没有找到，尝试其他方法
                # 查看是否有JSON格式的数据
                if '{"' in content:
                    # 尝试提取JSON
                    import json as json_module
                    try:
                        # 查找可能的JSON数据
                        json_start = content.find('{')
                        json_end = content.rfind('}') + 1
                        if json_start != -1 and json_end > json_start:
                            json_str = content[json_start:json_end]
                            data = json_module.loads(json_str)
                            
                            # 在JSON中查找PE数据
                            def find_pe_in_obj(obj):
                                if isinstance(obj, dict):
                                    for key, value in obj.items():
                                        if key.lower() in ['pe', '市盈率', 'pe_ratio'] and isinstance(value, (int, float)):
                                            return value
                                        elif isinstance(value, (dict, list)):
                                            result = find_pe_in_obj(value)
                                            if result is not None:
                                                return result
                                elif isinstance(obj, list):
                                    for item in obj:
                                        result = find_pe_in_obj(item)
                                        if result is not None:
                                            return result
                                return None
                            
                            pe_value = find_pe_in_obj(data)
                            if pe_value:
                                print(f"[INFO] 从JSON中找到PE数据: {pe_value}")
                                return {
                                    "date": target_date.strftime("%Y-%m-%d"),
                                    "pe": float(pe_value),
                                    "turnover": None,
                                    "volume": None,
                                    "amount": None
                                }
                    except:
                        pass
            
            time.sleep(1)  # 短暂延迟
            
        except Exception as e:
            print(f"[ERROR] API请求失败: {e}")
            continue
    
    return None

def get_latest_pe_data():
    """获取最新PE数据"""
    print("=== 上证PE数据获取 (API版) ===\n")
    
    # 初始化数据库
    init_db()
    
    # 计算需要获取的日期（最近3个交易日）
    today = datetime.now()
    dates_to_fetch = []
    
    # 获取最近3个工作日
    for i in range(1, 4):
        check_date = today - timedelta(days=i)
        # 简单判断是否为工作日（周一=0, 周日=6）
        if check_date.weekday() < 5:  # 周一到周五
            dates_to_fetch.append(check_date)
    
    if not dates_to_fetch:
        print("[INFO] 没有需要获取的工作日数据")
        return
    
    print(f"[INFO] 需要获取 {len(dates_to_fetch)} 个交易日的数据")
    
    success_count = 0
    
    for target_date in dates_to_fetch:
        date_str = target_date.strftime("%Y-%m-%d")
        
        # 检查是否已存在该日期的数据
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM sse_pe WHERE date = ?", (date_str,))
        if c.fetchone()[0] > 0:
            print(f"[INFO] {date_str} 数据已存在，跳过")
            conn.close()
            continue
        conn.close()
        
        # 获取数据
        pe_data = get_pe_data_from_api(target_date)
        
        if pe_data:
            save_to_db(date_str, pe_data)
            log_crawl(date_str, True)
            success_count += 1
            print(f"[INFO] {date_str} 数据获取成功")
        else:
            log_crawl(date_str, False, "获取数据失败")
            print(f"[WARN] {date_str}: 无数据")
        
        # 短暂延迟，避免请求过快
        time.sleep(2)
    
    print(f"\n=== 完成 ===\n成功获取 {success_count}/{len(dates_to_fetch)} 个交易日的数据")
    
    # 更新JSON文件
    if success_count > 0:
        update_json()

def main():
    """主函数"""
    try:
        get_latest_pe_data()
    except KeyboardInterrupt:
        print("\n[INFO] 用户中断")
    except Exception as e:
        print(f"[ERROR] 主程序异常: {e}")
        raise

if __name__ == "__main__":
    main()