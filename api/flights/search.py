import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '_lib'))
from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import json
from db import get_cached_search, save_search_cache, save_price_history
from duffel_service import search_flights 
from normalizer import normalize_offers
from codeshare_service import get_codeshare_offers

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
        # logic here
        cached = get_cached_search(f"{origin}-{destination}", departure_date, cabin_class, passengers)
        if cached:
            result = json.loads(cached['result_json'])
        else:
            duffel_response = search_flights(origin, destination, departure_date, passengers, cabin_class)
            codeshare_response = get_codeshare_offers(duffel_response)
            normalized_duffel = normalize_offers(duffel_response)
            result = normalized_duffel + codeshare_response
            save_search_cache(f"{origin}-{destination}", departure_date, passengers, json.dumps(result), cabin_class)
            for offer in result:
                if 'price_jpy' in offer and 'operating_airline' in offer and 'marketing_airline' in offer:
                    save_price_history(f"{origin}-{destination}", departure_date, offer['price_jpy'], offer['operating_airline'], offer['marketing_airline'])
        # return response
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps({"data": result}).encode())
        