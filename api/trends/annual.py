import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '_lib'))
from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import json
from trend_service import get_annual_price_trend

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        params = parse_qs(urlparse(self.path).query)
        origin = params.get('origin', [None])[0]
        destination = params.get('destination', [None])[0]
        
        if not origin or not destination:
            self.send_response(400)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"error": "originとdestinationは必須項目です。"}).encode())
            return
        
        result = get_annual_price_trend(f"{origin}-{destination}")
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps({"data": result}).encode())