#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import sys

os.environ['DATA_SOURCE'] = 'remote_api'
os.environ['REMOTE_API_URL'] = 'http://101.43.3.247:8082/api/market/pe'
os.environ['PORT'] = '18082'

print("=== Local Dev Server ===")
print("URL: http://127.0.0.1:18082/")
print("")

import pe_data_service_extended
pe_data_service_extended.app.run(host='127.0.0.1', port=18082, debug=False, use_reloader=False)
