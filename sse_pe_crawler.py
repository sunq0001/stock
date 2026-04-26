"""
上证交易所市盈率数据爬虫（修正版） - 带数据库插入功能
修正问题：
1. 新API参数名应为大写的 SEARCH_DATE，而不是小写的 searchDate
2. 可以获取2022年3月22日之后的历史数据
3. 添加数据库插入功能，确保数据能存入SQLite数据库
"""
import urllib.request
import re
import json
import time
import datetime
import pandas as pd
import sys
import os
import sqlite3
from pathlib import Path

# 配置
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Referer': 'https://www.sse.com.cn/market/stockdata/overview/day/',
}

SLEEP = 1.2  # 请求间隔

# 数据库配置
DB_PATH = '/var/www/stock/data/sse_pe_data.db'  # Docker容器内的路径

# ============================================================
# 数据库函数
# ============================================================
def connect_db():
    """连接到SQLite数据库"""
    # 确保数据库目录存在
    db_dir = os.path.dirname(DB_PATH)
    if db_dir:
        os.makedirs(db_dir, exist_ok=True)
    
    conn = sqlite3.connect(DB_PATH)
    return conn

def init_db():
    """初始化数据库表（如果不存在）"""
    conn = connect_db()
    cursor = conn.cursor()
    
    # 创建sse_pe表（如果不存在）
    cursor.execute('''
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
    
    # 创建爬虫日志表（如果不存在）
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS crawl_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT,
            success INTEGER,
            message TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()
    print(f"数据库初始化完成: {DB_PATH}")

def insert_pe_data(date, pe, source='sse_crawler_fixed'):
    """
    插入或更新市盈率数据到数据库
    只插入主板A的PE数据
    """
    if pe == '-' or pe == '':
        print(f"  [{date}] PE值为空，跳过插入")
        return False
    
    try:
        pe_value = float(pe)
    except (ValueError, TypeError):
        print(f"  [{date}] PE值无效: {pe}，跳过插入")
        return False
    
    conn = connect_db()
    cursor = conn.cursor()
    
    try:
        # 使用INSERT OR REPLACE确保数据更新
        cursor.execute('''
            INSERT OR REPLACE INTO sse_pe 
            (date, pe, turnover, volume, amount, source, created_at)
            VALUES (?, ?, NULL, NULL, NULL, ?, CURRENT_TIMESTAMP)
        ''', (date, pe_value, source))
        
        conn.commit()
        print(f"  [{date}] 数据插入成功: PE={pe_value}, source={source}")
        return True
    except Exception as e:
        print(f"  [{date}] 数据库插入失败: {e}")
        return False
    finally:
        conn.close()

def log_crawl(date_str, success, message=''):
    """记录爬虫日志"""
    conn = connect_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            INSERT INTO crawl_log (date, success, message, created_at)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP)
        ''', (date_str, 1 if success else 0, message))
        
        conn.commit()
    except Exception as e:
        print(f"日志记录失败: {e}")
    finally:
        conn.close()

# ============================================================
# 工具函数
# ============================================================
def fetch_jsonp(url, timeout=15):
    """获取JSONP数据"""
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        raw = resp.read().decode('utf-8', errors='ignore')
    
    # 提取JSON部分
    m = re.search(r'\w+\((.+)\)\s*$', raw, re.DOTALL)
    if not m:
        raise ValueError(f"无法解析 JSONP: {raw[:300]}")
    
    return json.loads(m.group(1))

# ============================================================
# A. 历史接口（2005~2022-03-21）
# ============================================================
TYPE_MAP = {'1': ('01', '主板A'), '2': ('02', '主板B'), '3': ('03', '科创板')}

def fetch_by_history_api(date_str):
    """
    返回该日期的市盈率记录，或空列表（非交易日 / 无数据）
    date_str: YYYY-MM-DD
    
    注意：此接口在2022-03-21之后返回空PE数据
    """
    ts = int(time.time() * 1000)
    url = (
        f"https://query.sse.com.cn/marketdata/tradedata/"
        f"queryTradingByProdTypeData.do"
        f"?searchDate={date_str}&prodType=gp&jsonCallBack=cb&_={ts}"
    )
    
    try:
        data = fetch_jsonp(url)
        result = data.get('result') or []
        rows = []
        
        for item in result:
            ptype = str(item.get('productType', ''))
            if ptype not in TYPE_MAP:
                continue
            
            pe = item.get('profitRate', '')
            if not pe:  # 非交易日或数据为空
                continue
            
            code, name = TYPE_MAP[ptype]
            rows.append({
                'date': item.get('searchDate', date_str),
                'product_code': code,
                'product_name': name,
                'pe_ratio': pe,
            })
        
        return rows
    except Exception as e:
        print(f"历史API调用失败 {date_str}: {e}")
        return []

# ============================================================
# B. 新接口（2022-03-22 至今）
# ============================================================
PRODUCT_CODE_MAP = {
    '01': '主板A', '02': '主板B', '03': '科创板', '11': '股票回购', '17': '全市场合计'
}

def fetch_by_new_api(date_str):
    """
    使用新接口获取指定日期的数据
    关键：参数名必须为大写 SEARCH_DATE
    date_str: YYYY-MM-DD
    """
    ts = int(time.time() * 1000)
    url = (
        f"https://query.sse.com.cn/commonQuery.do"
        f"?sqlId=COMMON_SSE_SJ_GPSJ_CJGK_MRGK_C"
        f"&PRODUCT_CODE=01%2C02%2C03%2C11%2C17"
        f"&type=inParams"
        f"&SEARCH_DATE={date_str.replace('-', '')}"  # 注意：日期格式为YYYYMMDD
        f"&jsonCallBack=cb&_={ts}"
    )
    
    try:
        data = fetch_jsonp(url)
        result = data.get('result') or []
        rows = []
        
        for item in result:
            code = item.get('PRODUCT_CODE', '')
            if code not in PRODUCT_CODE_MAP:
                continue
            
            pe = item.get('AVG_PE_RATE', '-')
            trade_date = item.get('TRADE_DATE', '')
            
            # 格式化日期
            if len(trade_date) == 8:
                trade_date = f"{trade_date[:4]}-{trade_date[4:6]}-{trade_date[6:]}"
            
            rows.append({
                'date': trade_date,
                'product_code': code,
                'product_name': PRODUCT_CODE_MAP[code],
                'pe_ratio': pe,
            })
        
        return rows
    except Exception as e:
        print(f"新API调用失败 {date_str}: {e}")
        return []

# ============================================================
# 智能数据获取函数
# ============================================================
def fetch_pe_data(date_str):
    """
    智能获取指定日期的市盈率数据
    自动选择正确的API
    """
    # 解析日期
    try:
        date_obj = datetime.date.fromisoformat(date_str)
        cutoff_date = datetime.date(2022, 3, 21)
        
        if date_obj <= cutoff_date:
            # 使用历史API
            return fetch_by_history_api(date_str)
        else:
            # 使用新API
            return fetch_by_new_api(date_str)
    except Exception as e:
        print(f"日期解析失败 {date_str}: {e}")
        return []

# ============================================================
# 工作日生成器
# ============================================================
def gen_workdays(start, end):
    """生成工作日日期列表"""
    d = datetime.date.fromisoformat(start)
    e = datetime.date.fromisoformat(end)
    
    while d <= e:
        if d.weekday() < 5:  # 周一至周五
            yield d.isoformat()
        d += datetime.timedelta(days=1)

# ============================================================
# 批量爬取数据（带数据库插入）
# ============================================================
def crawl_date_range(start_date, end_date, output_file=None, insert_to_db=True):
    """
    批量爬取日期范围的数据
    insert_to_db: 是否将数据插入数据库
    """
    dates = list(gen_workdays(start_date, end_date))
    total = len(dates)
    
    print(f"准备爬取 {start_date} ~ {end_date}，共 {total} 个工作日")
    
    all_rows = []
    success_count = 0
    db_success_count = 0
    
    for i, date_str in enumerate(dates):
        try:
            print(f"[{i+1}/{total}] {date_str}: ", end='')
            
            rows = fetch_pe_data(date_str)
            
            if rows:
                all_rows.extend(rows)
                
                # 提取主板A的PE值
                pe_a = next((r['pe_ratio'] for r in rows if r['product_code'] == '01'), '-')
                pe_b = next((r['pe_ratio'] for r in rows if r['product_code'] == '02'), '-')
                
                print(f"成功 | 主板A={pe_a}, 主板B={pe_b} | {len(rows)} 条")
                success_count += 1
                
                # 插入数据库（只插入主板A数据）
                if insert_to_db and pe_a != '-':
                    if insert_pe_data(date_str, pe_a, source='sse_crawler_fixed'):
                        db_success_count += 1
                    else:
                        print(f"  [{date_str}] 数据库插入失败")
                
                # 记录成功日志
                log_crawl(date_str, True, f"主板A={pe_a}, 主板B={pe_b}")
            else:
                print("无数据")
                # 记录无数据日志
                log_crawl(date_str, False, "无数据")
            
            # 请求间隔
            time.sleep(SLEEP)
            
            # 每20个日期显示进度
            if (i + 1) % 20 == 0:
                print(f"  进度: {i+1}/{total} ({((i+1)/total*100):.1f}%)")
                
        except Exception as e:
            print(f"错误: {e}")
            log_crawl(date_str, False, str(e))
    
    print(f"\n爬取完成: 成功 {success_count}/{total} 个交易日，共 {len(all_rows)} 条记录")
    if insert_to_db:
        print(f"数据库插入: 成功 {db_success_count}/{success_count} 条记录")
    
    # 保存数据到Excel（可选）
    if all_rows and output_file:
        df = pd.DataFrame(all_rows)
        df = df.sort_values(['date', 'product_code']).drop_duplicates()
        df.to_excel(output_file, index=False)
        print(f"数据已保存到: {output_file}")
        
        return df
    elif all_rows:
        df = pd.DataFrame(all_rows)
        df = df.sort_values(['date', 'product_code']).drop_duplicates()
        return df
    else:
        print("未获取到任何数据")
        return pd.DataFrame()

# ============================================================
# 日常更新函数（用于Cron任务）
# ============================================================
def daily_update(days_back=5):
    """
    日常数据更新，用于Cron任务
    默认获取最近5个工作日的数据，防止遗漏
    """
    print("=" * 60)
    print("上证市盈率数据日常更新")
    print("=" * 60)
    
    # 初始化数据库
    init_db()
    
    # 计算日期范围
    today = datetime.date.today()
    start_date = today
    
    # 向前回溯，直到找到工作日
    for i in range(days_back * 2):  # 最多回溯2倍天数，确保找到足够的工作日
        check_date = today - datetime.timedelta(days=i)
        if check_date.weekday() < 5:  # 周一至周五
            start_date = check_date
            break
    
    end_date = today
    
    print(f"更新日期范围: {start_date.isoformat()} 至 {end_date.isoformat()}")
    
    # 爬取数据并插入数据库
    df = crawl_date_range(
        start_date=start_date.isoformat(),
        end_date=end_date.isoformat(),
        output_file=None,  # 不保存Excel文件
        insert_to_db=True
    )
    
    # 检查最新数据
    if not df.empty:
        # 获取主板A的最新数据
        df_a = df[df['product_code'] == '01']
        if not df_a.empty:
            latest = df_a.iloc[-1]
            print(f"\n最新主板A数据:")
            print(f"  日期: {latest['date']}")
            print(f"  PE值: {latest['pe_ratio']}")
    
    print("\n日常更新完成")
    print("=" * 60)

# ============================================================
# 测试特定日期
# ============================================================
def test_specific_dates():
    """测试关键日期"""
    test_dates = [
        '2022-03-21',  # 历史API最后一天
        '2022-03-22',  # 新API第一天
        '2022-03-25',  # 用户提到的日期
        '2022-12-30',  # 年末
        '2023-06-30',  # 年中
        '2024-12-31',  # 年末
        '2025-06-30',  # 年中
        datetime.date.today().isoformat(),  # 今天
    ]
    
    print("测试特定日期:")
    print("=" * 60)
    
    for date_str in test_dates:
        rows = fetch_pe_data(date_str)
        
        if rows:
            pe_a = next((r['pe_ratio'] for r in rows if r['product_code'] == '01'), '-')
            pe_b = next((r['pe_ratio'] for r in rows if r['product_code'] == '02'), '-')
            print(f"{date_str}: 主板A={pe_a}, 主板B={pe_b} | {len(rows)} 条记录")
        else:
            print(f"{date_str}: 无数据")

# ============================================================
# 主函数
# ============================================================
def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='上证大盘市盈率数据爬虫（带数据库插入）')
    parser.add_argument('--start', default='2022-01-01', help='起始日期（YYYY-MM-DD）')
    parser.add_argument('--end', default=None, help='结束日期（YYYY-MM-DD），默认今日')
    parser.add_argument('--output', default='sse_pe_complete.xlsx', help='输出Excel文件路径')
    parser.add_argument('--sleep', type=float, default=1.2, help='请求间隔秒数')
    parser.add_argument('--test', action='store_true', help='测试模式，只测试特定日期')
    parser.add_argument('--daily', action='store_true', help='日常更新模式，用于Cron任务')
    parser.add_argument('--init-db', action='store_true', help='初始化数据库')
    
    args = parser.parse_args()
    
    if args.init_db:
        init_db()
        return
    
    if args.daily:
        daily_update()
        return
    
    if args.end is None:
        args.end = datetime.date.today().isoformat()
    
    global SLEEP
    SLEEP = args.sleep
    
    print("=" * 60)
    print("上证交易所大盘市盈率数据爬虫（带数据库插入）")
    print(f"日期范围: {args.start} 至 {args.end}")
    print("=" * 60)
    
    if args.test:
        test_specific_dates()
        return
    
    # 初始化数据库
    init_db()
    
    # 爬取数据
    df = crawl_date_range(args.start, args.end, args.output, insert_to_db=True)
    
    if not df.empty:
        print(f"\n数据统计:")
        print(f"  总记录数: {len(df)}")
        print(f"  日期范围: {df['date'].min()} 至 {df['date'].max()}")
        print(f"  交易日数: {df['date'].nunique()}")
        print(f"  产品类型: {df['product_name'].unique().tolist()}")
        
        # 显示部分数据
        print(f"\n前10行数据:")
        print(df.head(10))
        
        # 检查数据完整性
        dates = df['date'].unique()
        print(f"\n数据完整性检查:")
        print(f"  共爬取 {len(dates)} 个交易日")
        
        # 检查每个产品在每个交易日是否有数据
        for product in ['主板A', '主板B', '科创板']:
            product_dates = df[df['product_name'] == product]['date'].nunique()
            print(f"  {product}: {product_dates} 个交易日有数据")
    
    print("\n" + "=" * 60)
    print("重要说明:")
    print("1. 历史API (queryTradingByProdTypeData.do) 适用于2005-01-01 ~ 2022-03-21")
    print("2. 新API (commonQuery.do) 适用于2022-03-22 至今")
    print("3. 新API参数名必须为大写 SEARCH_DATE")
    print("4. 日期格式为 YYYYMMDD (无分隔符)")
    print("=" * 60)

if __name__ == '__main__':
    main()