from flask import Flask, request, Response
import sys
import os
import json
from datetime import date

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'api', '_lib'))

app = Flask(__name__)

def get_common_params():
    params = request.args
    return {
        'origin': params.get('origin'),
        'destination': params.get('destination'),
        'departure_date': params.get('departureDate'),
        'passengers': params.get('passengers', 'adult').split(','),
        'cabin_class': params.get('cabinClass', 'economy')
    }

def search_response(filter_offers=None):
    from search_service import get_normalized_offers

    p = get_common_params()
    if not p['origin'] or not p['destination'] or not p['departure_date']:
        return Response(json.dumps({"error": "必須項目が不足しています"}), status=400, mimetype='application/json')

    # The cache holds the full list; the mode filter runs here, on every request.
    offers = get_normalized_offers(p['origin'], p['destination'], p['departure_date'], p['passengers'], p['cabin_class'])
    if filter_offers:
        offers = filter_offers(offers)
    return Response(json.dumps({"data": offers}), status=200, mimetype='application/json')

@app.route('/api/flights/search')
def flights_search():
    return search_response()

@app.route('/api/codeshare/detect')
def codeshare_detect():
    from codeshare_service import filter_codeshare_offers

    return search_response(filter_codeshare_offers)

@app.route('/api/trends/annual')
def trends_annual():
    from trend_service import get_annual_price_trend
    
    origin = request.args.get('origin')
    destination = request.args.get('destination')
    
    if not origin or not destination:
        return Response(json.dumps({"error": "originとdestinationは必須項目です"}), status=400, mimetype='application/json')
    
    result = get_annual_price_trend(f"{origin}-{destination}")
    return Response(json.dumps({"data": result}, default=str), status=200, mimetype='application/json')

@app.route('/api/trends/recommend')
def trends_recommend():
    from trend_service import get_price_recommendation
    
    origin = request.args.get('origin')
    destination = request.args.get('destination')
    
    if not origin or not destination:
        return Response(json.dumps({"error": "必須項目が不足しています"}), status=400, mimetype='application/json')
    
    try:
        result = get_price_recommendation(f"{origin}-{destination}")
        return Response(json.dumps(result, default=str), status=200, mimetype='application/json')
    except Exception as e:
        return Response(json.dumps({"error": str(e)}), status=500, mimetype='application/json')

@app.route('/api/verified-checks')
def verified_checks():
    from db import get_verified_checks

    route = request.args.get('route')
    flight_date = request.args.get('flightDate')
    if flight_date:
        try:
            date.fromisoformat(flight_date)
        except ValueError:
            return Response(json.dumps({"error": "flightDateはYYYY-MM-DD形式で指定してください"}), status=400, mimetype='application/json')

    try:
        result = get_verified_checks(route, flight_date)
    except Exception:
        return Response(json.dumps({"error": "照合記録の取得に失敗しました"}), status=500, mimetype='application/json')
    return Response(json.dumps({"data": result}, default=str), status=200, mimetype='application/json')

@app.route('/api/real-prices')
def real_prices():
    from real_prices import lookup_response

    status, body = lookup_response(
        request.args.get('origin'),
        request.args.get('destination'),
        request.args.get('departureDate'),
    )
    return Response(json.dumps(body, ensure_ascii=False), status=status, mimetype='application/json')

@app.route('/api/places/suggestions')
def places_suggestions():
    import requests as req
    from config import DUFFEL_ACCESS_TOKEN
    
    query = request.args.get('query', '')
    if not query or len(query) < 2:
        return Response(json.dumps({"data": []}), status=200, mimetype='application/json')
    
    duffel_response = req.get(
        f"https://api.duffel.com/places/suggestions?query={query}",
        headers={
            "Authorization": f"Bearer {DUFFEL_ACCESS_TOKEN}",
            "Duffel-Version": "v2",
            "Accept": "application/json"
        }
    )
    return Response(duffel_response.text, status=duffel_response.status_code, mimetype='application/json')

if __name__ == '__main__':
    app.run(port=8000, debug=True)