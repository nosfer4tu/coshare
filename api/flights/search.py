import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '_lib'))
from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import json
from search_service import search_payload

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        params = parse_qs(urlparse(self.path).query)
        origin = params.get('origin', [None])[0]
        destination = params.get('destination', [None])[0]
        departure_date = params.get('departure_date', [None])[0]
        passengers_raw = params.get('passengers', ["adult"])[0]
        passengers = passengers_raw.split(',')
        cabin_class = params.get('cabin_class', ['economy'])[0]
        
        if not origin or not destination or not departure_date:
            self.send_response(400)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"error": "origin、destination、departure_dateは必須項目です。"}).encode())
            return   
        # The cache holds the full list; this route returns it unfiltered (or a saved demo snapshot).
        body = search_payload(origin, destination, departure_date, passengers, cabin_class)
        # return response
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(body).encode())
        
