#!/usr/bin/env python3
"""Deploy extended service to server"""
import paramiko
import os
import sys

sys.stdout.reconfigure(encoding='utf-8')

HOST = '101.43.3.247'
USER = 'root'
PASSWORD = 'Sandisk88!'
REMOTE_PATH = '/var/www/stock/'
LOCAL_PATH = 'c:/Users/mss/WorkBuddy/20260414224936/stock-project-local/'

def deploy():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASSWORD, timeout=30)
    sftp = client.open_sftp()
    
    files = ['neodata_query.py', 'pe_data_service_extended.py']
    
    for f in files:
        local_file = os.path.join(LOCAL_PATH, f)
        remote_file = os.path.join(REMOTE_PATH, f)
        print(f'Upload {f}...')
        sftp.put(local_file, remote_file)
        print(f'  OK: {remote_file}')
    
    stdin, stdout, stderr = client.exec_command(f'ls -la {REMOTE_PATH}*.py')
    print('\nServer files:')
    print(stdout.read().decode())
    
    sftp.close()
    client.close()
    print('\nDone!')

if __name__ == '__main__':
    deploy()
