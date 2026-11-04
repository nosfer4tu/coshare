from normalizer import normalize_offers

TICKETING_CARRIERS = {"HR"}

def filter_codeshare_offers(normalized_offers):
    return [
        offer for offer in normalized_offers
        if offer.get("is Codeshare") and offer.get("Owner Airline IATA") not in TICKETING_CARRIERS
    ]

def get_codeshare_offers(raw_response):
    return filter_codeshare_offers(normalize_offers(raw_response))
