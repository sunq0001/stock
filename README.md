# 股票数据可视化项目

上证市场数据平台：爬虫采集 → InfluxDB 存储 → Flask API → ECharts 展示。

```bash
# 快速启动（先启动 InfluxDB）
docker compose -f docker-compose.local.yml up -d influxdb
$env:INFLUXDB_URL="http://localhost:18086"; $env:INFLUXDB_TOKEN="my-super-secret-token"
$env:INFLUXDB_ORG="stock"; $env:INFLUXDB_BUCKET="market_data"; $env:PORT="5000"
python pe_data_service_influxdb.py
# 浏览器打开 http://localhost:18082/
```

完整文档见 [`docs/`](docs/)。
