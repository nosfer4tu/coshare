import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '_lib'))
from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import json
from recommendation_service import get_recommendation

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        params = parse_qs(urlparse(self.path).query)
        destination = params.get('destination', [None])[0]
        travel_date = params.get('travel_date', [None])[0]
        
        if not destination or not travel_date:
            self.send_response(400)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"error": "destinationとtravel_dateは必須項目です。"}).encode())
            return
        
        activities = get_recommendation(destination, travel_date)
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps({"data": activities}).encode())