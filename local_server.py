from flask import Flask, request, Response
import sys
import os
import json

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

@app.route('/api/flights/search')
def flights_search():
    from duffel_service import search_flights
    from normalizer import normalize_offers
    from codeshare_service import get_codeshare_offers
    from db import get_cached_search, save_search_cache, save_price_history

    p = get_common_params()
    if not p['origin'] or not p['destination'] or not p['departure_date']:
        return Response(json.dumps({"error": "必須項目が不足しています"}), status=400, mimetype='application/json')

    cached = get_cached_search(f"{p['origin']}-{p['destination']}", p['departure_date'], p['cabin_class'], (",").join(p['passengers']))
    if cached:
        if isinstance(cached['result_json'], str):
            result = json.loads(cached['result_json'])
        else:
            result = cached['result_json']
    else:
        duffel_response = search_flights(p['origin'], p['destination'], p['departure_date'], p['passengers'], p['cabin_class'])
        # codeshare_response = get_codeshare_offers(duffel_response)
        normalized_duffel = normalize_offers(duffel_response)
        result = normalized_duffel 
        save_search_cache(f"{p['origin']}-{p['destination']}", p['departure_date'], ",".join(p['passengers']), json.dumps(result), p['cabin_class'])
        for offer in result:
            if offer['Currency'] == 'JPY':
                save_price_history(f"{p['origin']}-{p['destination']}", p['departure_date'], offer['Total Amount'], offer['Operating Carrier'], offer['Marketing Carrier'])

    return Response(json.dumps({"data": result}), status=200, mimetype='application/json')

@app.route('/api/codeshare/detect')
def codeshare_detect():
    from duffel_service import search_flights
    from normalizer import normalize_offers
    from codeshare_service import get_codeshare_offers
    from db import get_cached_search, save_search_cache, save_price_history

    p = get_common_params()
    if not p['origin'] or not p['destination'] or not p['departure_date']:
        return Response(json.dumps({"error": "必須項目が不足しています"}), status=400, mimetype='application/json')

    cached = get_cached_search(f"{p['origin']}-{p['destination']}", p['departure_date'], p['cabin_class'], (",").join(p['passengers']))
    if cached:
        if isinstance(cached['result_json'], str):
            result = json.loads(cached['result_json'])
        else:
            result = cached['result_json']
    else:
        duffel_response = search_flights(p['origin'], p['destination'], p['departure_date'], p['passengers'], p['cabin_class'])
        codeshare_response = get_codeshare_offers(duffel_response)
        normalized_duffel = normalize_offers(duffel_response)
        result = codeshare_response
        save_search_cache(f"{p['origin']}-{p['destination']}", p['departure_date'], ",".join(p['passengers']), json.dumps(result), p['cabin_class'])
        for offer in normalized_duffel:
            if offer['Currency'] == 'JPY':
                save_price_history(f"{p['origin']}-{p['destination']}", p['departure_date'], offer['Total Amount'], offer['Operating Carrier'], offer['Marketing Carrier'])

    return Response(json.dumps({"data": result}), status=200, mimetype='application/json')

@app.route('/api/trends/annual')
def trends_annual():
    from trend_service import get_annual_price_trend
    
    origin = request.args.get('origin')
    destination = request.args.get('destination')
    
    if not origin or not destination:
        return Response(json.dumps({"error": "originとdestinationは必須項目です"}), status=400, mimetype='application/json')
    
    result = get_annual_price_trend(f"{origin}-{destination}")
    return Response(json.dumps({"data": result}, default=str), status=200, mimetype='application/json')

if __name__ == '__main__':
    app.run(port=8000, debug=True)