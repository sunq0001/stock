# Ansible自动化部署指南

## 安装Ansible

### Windows (通过pip)
```bash
pip install ansible
pip install PyYAML paramiko docker
```

### WSL / Linux / macOS
```bash
sudo apt update && sudo apt install ansible  # Ubuntu/Debian
# 或
brew install ansible  # macOS
```

## 快速部署

1. 进入ansible目录：
   ```bash
   cd ansible
   ```

2. 测试服务器连通性：
   ```bash
   ansible all -m ping
   ```

3. 一键部署：
   ```bash
   ansible-playbook deploy.yml
   ```

## 部署流程

1. 同步本地代码到服务器 `/root/stock-project/`
2. 构建Docker镜像
3. 使用docker-compose启动服务
4. 检查服务健康状态

## 部署后访问

- 服务器地址：http://101.43.3.247:8082/
- API接口：http://101.43.3.247:8082/api/market/pe

## 其他命令

```bash
# 查看服务器信息
ansible all -m setup

# 只同步代码（不重启服务）
ansible-playbook deploy.yml --tags sync

# 只重启服务
ansible-playbook deploy.yml --tags restart

# 查看服务日志
ansible all -m shell -a "cd /root/stock-project && docker-compose logs -f"
```
