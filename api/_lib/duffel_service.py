import requests
from normalizer import normalize_offers
from codeshare_service import get_codeshare_offers
from config import DUFFEL_ACCESS_TOKEN

def search_flights(origin, destination, departure_date, passengers, cabin_class):
    response = requests.post(
        "https://api.duffel.com/air/offer_requests?return_offers=true",
        headers={
            "Authorization": f"Bearer {DUFFEL_ACCESS_TOKEN}",
            "Content-Type": "application/json",
            "Duffel-Version": "v2",
            "Accept": "application/json"
        },
        json={
            "data":{
                "slices":[
                    {
                        "origin": origin,
                        "destination": destination,
                        "departure_date": departure_date
                    }
                ],
                "passengers": [{"type": p} for p in passengers],
                "cabin_class": cabin_class,
            }
        }
    )
    return response.json()