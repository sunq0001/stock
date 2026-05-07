#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

"""
Deploy script - uses paramiko to sync files to server
"""
import os
import paramiko
from pathlib import Path

SERVER = "101.43.3.247"
USER = "root"
PASSWORD = "Sandisk88!"
PORT = 22
REMOTE_DIR = "/var/www/stock"

EXCLUDES = [
    '.git', '__pycache__', 'venv', '.venv', 'ansible',
    'docker-compose.local.yml', 'deploy.py', 'deploy.sh',
    '.DS_Store', '.gitignore', 'start_log.txt',
    'neodata_token.txt', '*.local.yml', 'venv*'
]

def is_excluded(name):
    for ex in EXCLUDES:
        if ex.startswith('*.'):
            if name.endswith(ex[1:]): return True
        elif name == ex: return True
    return False

def main():
    print("=" * 50)
    print("Connecting to server...")
    
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        client.connect(SERVER, port=PORT, username=USER, password=PASSWORD, timeout=30, banner_timeout=30)
        print("[OK] Connected: {}@{}".format(USER, SERVER))
    except Exception as e:
        print("[FAIL] Connection failed: {}".format(e))
        sys.exit(1)
    
    print("\nSyncing files...")
    sftp = client.open_sftp()
    local_dir = Path(__file__).parent.resolve()
    
    uploaded = 0
    skipped = 0
    
    for root, dirs, files in os.walk(local_dir):
        dirs[:] = [d for d in dirs if not is_excluded(d)]
        
        for filename in files:
            if is_excluded(filename):
                skipped += 1
                continue
            
            local_path = Path(root) / filename
            rel_path = str(local_path.relative_to(local_dir))
            remote_path = "{}/{}".format(REMOTE_DIR, rel_path)
            
            remote_dir = os.path.dirname(remote_path)
            try:
                sftp.stat(remote_dir)
            except:
                try:
                    sftp.mkdir(remote_dir, 0o755)
                except:
                    pass
            
            try:
                sftp.put(str(local_path), remote_path)
                uploaded += 1
                if uploaded <= 20:
                    print("  Upload: {}".format(rel_path))
            except Exception as e:
                print("  FAIL: {} - {}".format(rel_path, e))
    
    print("\nUploaded: {} files, Skipped: {}".format(uploaded, skipped))
    
    print("\nRestarting Docker service...")
    stdin, stdout, stderr = client.exec_command(
        'cd {} && docker-compose -f docker-compose.production.yml down 2>/dev/null; '
        'docker-compose -f docker-compose.production.yml up -d --build'.format(REMOTE_DIR)
    )
    output = stdout.read().decode('utf-8', errors='ignore')
    error = stderr.read().decode('utf-8', errors='ignore')
    
    if output: print(output)
    if error and 'error' not in error.lower(): print(error)
    
    print("\nChecking health...")
    stdin, stdout, stderr = client.exec_command(
        'curl -s http://localhost:8080/api/health || echo "Health check failed"'
    )
    result = stdout.read().decode('utf-8', errors='ignore')
    print(result if result else "Cannot get status")
    
    sftp.close()
    client.close()
    
    print("\n" + "=" * 50)
    print("Deployment complete!")
    print("Visit: http://{}:8080/".format(SERVER))
    print("=" * 50)

if __name__ == "__main__":
    main()
