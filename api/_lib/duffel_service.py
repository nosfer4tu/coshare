import os
import requests
import json
from pathlib import Path
from dotenv import load_dotenv
from normalizer import normalize_offers
from codeshare_service import get_codeshare_offers

env_path = Path(__file__).parent.parent.parent / '.env.local'
load_dotenv(dotenv_path=env_path)

duffel_access_token = os.getenv("DUFFEL_ACCESS_TOKEN")

def search_flights(origin, destination, departure_date):
    response = requests.post(
    "https://api.duffel.com/air/offer_requests?return_offers=true",
    headers={
        "Authorization": f"Bearer {duffel_access_token}",
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
            "passengers":[{"type": "adult"}],
            "cabin_class": "business",
        }
    }
)
    return response.json()