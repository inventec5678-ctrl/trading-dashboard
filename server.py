#!/usr/bin/env python3
"""Trading Dashboard Backend"""
from http.server import HTTPServer, SimpleHTTPRequestHandler
import urllib.request
import json
import os
import time
import random

# 價格緩存
price_cache = {
    'AAPL': {'price': 250.12, 'change': -2.21, 'time': '2026-03-14'},
    'MSFT': {'price': 395.55, 'change': -1.57, 'time': '2026-03-14'},
    'GOOGL': {'price': 302.28, 'change': -0.42, 'time': '2026-03-14'},
    'AMZN': {'price': 207.67, 'change': -0.89, 'time': '2026-03-14'},
    'NVDA': {'price': 180.25, 'change': -1.58, 'time': '2026-03-14'},
    'TSLA': {'price': 391.20, 'change': -0.96, 'time': '2026-03-14'},
    'META': {'price': 613.71, 'change': -3.83, 'time': '2026-03-14'},
    'AMD': {'price': 193.39, 'change': -2.20, 'time': '2026-03-14'},
    '2330': {'price': 1865.0, 'change': -1.06, 'time': '2026-03-14'},
    '0050': {'price': 75.95, 'change': -0.85, 'time': '2026-03-14'},
    '2317': {'price': 214.5, 'change': 0.0, 'time': '2026-03-14'},
    '2454': {'price': 1720.0, 'change': -3.64, 'time': '2026-03-14'},
}

class DashboardHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path.startswith('/api/quote?'):
            from urllib.parse import parse_qs
            query = parse_qs(self.path.split('?')[1])
            symbol = query.get('symbol', ['BTCUSDT'])[0]
            
            # 加密貨幣 - 實時
            if symbol.endswith('USDT'):
                url = f'https://api.binance.com/api/v3/ticker/24hr?symbol={symbol}'
                try:
                    req = urllib.request.Request(url)
                    req.add_header('User-Agent', 'Mozilla/5.0')
                    with urllib.request.urlopen(req, timeout=5) as response:
                        data = json.loads(response.read())
                        result = {
                            'symbol': symbol.replace('USDT', ''),
                            'price': float(data['lastPrice']),
                            'change': float(data['priceChangePercent']),
                            'status': 'live'
                        }
                        # 更新緩存
                        price_cache[symbol.replace('USDT', '')] = {
                            'price': result['price'],
                            'change': result['change'],
                            'time': time.strftime('%Y-%m-%d')
                        }
                        self.send_response(200)
                        self.send_header('Content-Type', 'application/json')
                        self.end_headers()
                        self.wfile.write(json.dumps(result).encode())
                except Exception as e:
                    # 返回緩存價格
                    sym = symbol.replace('USDT', '')
                    cached = price_cache.get(sym, {'price': 0, 'change': 0})
                    result = {
                        'symbol': sym,
                        'price': cached['price'],
                        'change': cached['change'],
                        'status': 'delayed',
                        'lastUpdate': cached.get('time', 'unknown')
                    }
                    self.send_response(200)
                    self.send_header('Content-Type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps(result).encode())
            else:
                # 股票 - 返回緩存
                sym = symbol.replace('.TW', '')
                cached = price_cache.get(sym, {'price': 100, 'change': 0})
                result = {
                    'symbol': sym,
                    'price': cached['price'],
                    'change': cached['change'],
                    'status': 'delayed',
                    'lastUpdate': cached.get('time', 'unknown')
                }
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps(result).encode())
        

        # K-line API
        # Taiwan stock K-line (mock for now)
        elif self.path.startswith('/api/kline?') and ('TW' in self.path or any(s in self.path for s in ['2330','0050','2317','2454'])):
            import random
            result = []
            base_price = 1000
            for i in range(90):
                t = 1773187200 + i * 86400
                o = base_price * (1 + random.uniform(-0.03, 0.03))
                c = o * (1 + random.uniform(-0.02, 0.02))
                h = max(o, c) * (1 + random.uniform(0, 0.02))
                l = min(o, c) * (1 - random.uniform(0, 0.02))
                result.append({'time': t, 'open': o, 'high': h, 'low': l, 'close': c})
                base_price = c
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(result).encode())
            
        elif self.path.startswith('/api/kline?'):
            from urllib.parse import parse_qs
            query = parse_qs(self.path.split('?')[1])
            symbol = query.get('symbol', ['BTCUSDT'])[0]
            limit = int(query.get('limit', ['90'])[0])  # 3 months = ~90 days
            
            if symbol.endswith('USDT'):
                url = f'https://api.binance.com/api/v3/klines?symbol={symbol}&interval=1d&limit={limit}'
                try:
                    req = urllib.request.Request(url)
                    req.add_header('User-Agent', 'Mozilla/5.0')
                    with urllib.request.urlopen(req, timeout=10) as response:
                        data = json.loads(response.read())
                        result = []
                        for k in data:
                            result.append({
                                'time': k[0] // 1000,
                                'open': float(k[1]),
                                'high': float(k[2]),
                                'low': float(k[3]),
                                'close': float(k[4]),
                                'volume': float(k[5])
                            })
                        self.send_response(200)
                        self.send_header('Content-Type', 'application/json')
                        self.end_headers()
                        self.wfile.write(json.dumps(result).encode())
                except Exception as e:
                    self.send_response(500)
                    self.send_header('Content-Type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps({'error': str(e)}).encode())
            else:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(b'K-line only for crypto')

        # Static files
        else:
            if self.path == '/':
                self.path = '/index.html'
            file_path = os.path.dirname(__file__) + self.path
            if os.path.exists(file_path) and os.path.isfile(file_path):
                self.send_response(200)
                if file_path.endswith('.html'):
                    self.send_header('Content-Type', 'text/html')
                elif file_path.endswith('.js'):
                    self.send_header('Content-Type', 'application/javascript')
                self.end_headers()
                with open(file_path, 'rb') as f:
                    self.wfile.write(f.read())
            else:
                self.send_response(404)
                self.end_headers()
                self.wfile.write(b'Not Found')
    
    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        super().end_headers()

PORT = 9001
print(f"🚀 Trading Dashboard")
print(f"   http://192.168.31.171:{PORT}")
server = HTTPServer(('0.0.0.0', PORT), DashboardHandler)
server.serve_forever()
