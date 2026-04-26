# 开发注意事项

## 1. 优先使用国内镜像

安装Python包时，**优先使用国内镜像源**，避免下载超时：

```bash
# 清华镜像（推荐）
pip install xxx -i https://pypi.tuna.tsinghua.edu.cn/simple --trusted-host pypi.tuna.tsinghua.edu.cn

# 阿里云镜像
pip install xxx -i https://mirrors.aliyun.com/pypi/simple/ --trusted-host mirrors.aliyun.com

# 豆瓣镜像
pip install xxx -i https://pypi.doubanio.com/simple/ --trusted-host pypi.doubanio.com
```

常用包安装示例：
```bash
pip install ansible PyYAML paramiko docker -i https://pypi.tuna.tsinghua.edu.cn/simple --trusted-host pypi.tuna.tsinghua.edu.cn
```

## 2. 本地开发环境

### 启动本地服务
```bash
cd c:\Users\mss\WorkBuddy\20260414224936\stock-project-local
$env:DATA_SOURCE="remote_api"
$env:PORT="18082"
python pe_data_service.py
```

访问地址：
- 前端：http://localhost:18082/
- API：http://localhost:18082/api/market/pe

## 3. 服务器部署（Ansible）

### 安装Ansible
```bash
pip install ansible PyYAML paramiko docker -i https://pypi.tuna.tsinghua.edu.cn/simple --trusted-host pypi.tuna.tsinghua.edu.cn
```

### 一键部署到服务器
```bash
cd ansible
ansible-playbook deploy.yml
```

服务器信息：
- 地址：101.43.3.247
- 用户：root
- 密码：Sandisk88!

## 4. Docker Compose（备用方式）

如果不用Ansible，手动部署：
```bash
ssh root@101.43.3.247
cd /root/stock-project
git pull
docker-compose up -d --build
```
