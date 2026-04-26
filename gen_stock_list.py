#!/usr/bin/env python3
"""生成A股股票列表JSON（含拼音索引），供搜索功能使用"""
import akshare as ak
from pypinyin import pinyin, Style
import json, re, os

print('Fetching stock list (this takes ~30s)...')
df = ak.stock_zh_a_spot()

stocks = []
for _, row in df.iterrows():
    code = str(row['代码']).strip()
    name = str(row['名称']).strip()
    m = re.search(r'(\d{6})', code)
    if not m:
        continue
    code6 = m.group(1)
    py_full = ''.join([p[0] for p in pinyin(name, style=Style.NORMAL)])
    py_abbr = ''.join([p[0][0] for p in pinyin(name, style=Style.NORMAL)])
    stocks.append({
        'c': code6,
        'n': name,
        'p': py_full.lower(),
        'a': py_abbr.lower()
    })

print(f'Total: {len(stocks)} stocks')

# 验证几个
for s in stocks:
    if any(k in s['n'] for k in ['茅台', '中国平安', '中国银行', '格力', '隆基']):
        print(f"  {s['c']} {s['n']} py={s['p']} abbr={s['a']}")

out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'stock_list.json')
with open(out_path, 'w', encoding='utf-8') as f:
    json.dump(stocks, f, ensure_ascii=False, separators=(',', ':'))
print(f'Saved to {out_path} ({os.path.getsize(out_path)} bytes)')
