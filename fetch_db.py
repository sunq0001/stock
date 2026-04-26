"""从云服务器下载 sse_pe_data.db 到本地"""
import paramiko, os

HOST = '101.43.3.247'
PORT = 22
USER = 'root'
PASS = 'Sandisk88!'
REMOTE = '/var/www/stock/data/sse_pe_data.db'
LOCAL  = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'sse_pe_data.db')

print(f'连接 {HOST}...')
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(HOST, port=PORT, username=USER, password=PASS, timeout=15)

sftp = ssh.open_sftp()
print(f'下载 {REMOTE} → {LOCAL}')
sftp.get(REMOTE, LOCAL)
sftp.close()
ssh.close()

size = os.path.getsize(LOCAL)
print(f'完成！文件大小: {size/1024:.1f} KB')
