#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
neoData查询脚本 - Docker容器内使用
"""
import os
import sys
import json
import requests

def load_token():
    """从文件加载token"""
    # Docker容器内路径
    token_file_docker = '/app/neodata_token.txt'
    # 本地运行时的路径（项目根目录）
    token_file_local = os.path.join(os.path.dirname(__file__), 'neodata_token.txt')
    
    # 优先尝试本地路径
    for token_file in [token_file_local, token_file_docker]:
        if os.path.exists(token_file):
            with open(token_file, 'r') as f:
                content = f.read().strip()
                if content and not content.startswith('#'):
                    return content
    
    # 也尝试从环境变量读取
    token = os.environ.get('NEODATA_TOKEN')
    if token:
        return token
    
    return None

def query_neodata(query_text, data_type="all"):
    """查询neoData API"""
    token = load_token()
    if not token:
        print("[ERROR] 未找到neoData token")
        return None
    
    url = "https://copilot.tencent.com/agenttool/v1/neodata"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }
    
    payload = {
        "query": query_text,
        "channel": "neodata",
        "sub_channel": "workbuddy",
        "data_type": data_type
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"[ERROR] neoData API 返回错误: {response.status_code}")
            if response.status_code in [401, 403]:
                print("Token可能已过期，需要重新获取")
            return None
    except Exception as e:
        print(f"[ERROR] 请求neoData API失败: {e}")
        return None

def main():
    """主函数，处理命令行参数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='neoData查询工具')
    parser.add_argument('--query', help='查询内容', required=True)
    parser.add_argument('--data-type', choices=['all', 'api', 'doc'], default='all', 
                       help='数据类型: all=API+文章, api=仅结构化数据, doc=仅文章')
    
    args = parser.parse_args()
    
    result = query_neodata(args.query, args.data_type)
    if result:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print("查询失败")

if __name__ == '__main__':
    main()