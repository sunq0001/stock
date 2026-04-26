#!/bin/bash
pkill -f "http.server 8080" 2>/dev/null
cd /var/www/stock
nohup /usr/bin/python3 -m http.server 8080 > /var/www/stock/server.log 2>&1 &
echo "Server started, PID=$!"

