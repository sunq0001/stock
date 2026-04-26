"""后台启动 pe_data_service，使用 PORT=18082"""
import subprocess, sys, os, time

env = os.environ.copy()
env['PORT'] = '18082'

proc = subprocess.Popen(
    [sys.executable, 'pe_data_service.py'],
    cwd=r'C:\Users\mss\WorkBuddy\20260414224936\stock-project-local',
    env=env,
    creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,
)
print(f'Service started, PID={proc.pid}')
time.sleep(4)

# 验证接口
import urllib.request, json
try:
    with urllib.request.urlopen('http://127.0.0.1:18082/api/market/pe', timeout=5) as r:
        data = json.loads(r.read())
        print(f'/api/market/pe OK, dates={len(data.get("dates",[]))}')
except Exception as e:
    print(f'/api/market/pe ERROR: {e}')

try:
    with urllib.request.urlopen('http://127.0.0.1:18082/api/search?q=maotai', timeout=5) as r:
        data = json.loads(r.read())
        print(f'/api/search OK: {data[:2]}')
except Exception as e:
    print(f'/api/search ERROR: {e}')
