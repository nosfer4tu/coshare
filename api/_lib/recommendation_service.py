from datetime import datetime
from config import GOOGLE_PLACES_API_KEY
from db import get_cached_destinations, save_destination_cache
import requests
AIRPORT_TO_CITY = {
    "CTS": "札幌", "HND": "東京", "NRT": "東京",
    "ITM": "大阪", "KIX": "大阪", "FUK": "福岡",
    "OKA": "那覇", "NGO": "名古屋", "HIJ": "広島",
    "SDJ": "仙台", "KOJ": "鹿児島", "KMJ": "熊本",
    "TAK": "高松", "MYJ": "松山", "KCZ": "高知"
}

def get_season(travel_date):
    if isinstance(travel_date, str):
        travel_date = datetime.strptime(travel_date, "%Y-%m-%d")
    season = None
    if travel_date.month in [12, 1, 2]:
        season = "冬"
    elif travel_date.month in [3, 4, 5]:
        season = "春"
    elif travel_date.month in [6, 7, 8]:
        season = "夏"
    elif travel_date.month in [9, 10, 11]:
        season = "秋"
    return season

def get_recommendation(destination, travel_date):
    season = get_season(travel_date)
    city = AIRPORT_TO_CITY.get(destination, destination)
    cached = get_cached_destinations(destination)
    if cached:
        return cached['activities_json']
    #call google places api here
    response = requests.get(
        "https://maps.googleapis.com/maps/api/place/textsearch/json",
        params={
            "query": f"{city}で{season}にできること",
            "key": GOOGLE_PLACES_API_KEY,
            "language": "ja"
        }
    )
    activities = response.json()
    #save into destination_cache
    save_destination_cache(destination, activities)
    
    return activities