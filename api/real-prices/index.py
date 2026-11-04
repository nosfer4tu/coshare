import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '_lib'))
from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import json
from real_prices import lookup_response

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        params = parse_qs(urlparse(self.path).query)
        origin = params.get('origin', [None])[0]
        destination = params.get('destination', [None])[0]
        departure_date = params.get('departureDate', [None])[0]

        status, body = lookup_response(origin, destination, departure_date)
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(body).encode())
