from normalizer import normalize_offers

TICKETING_CARRIERS = {"HR"}

def get_codeshare_offers(raw_response):
    cleaned_offers = normalize_offers(raw_response)
    codeshare_offers = [
        offer for offer in cleaned_offers
        if offer.get("is Codeshare") and offer.get("Owner Airline IATA") not in TICKETING_CARRIERS
    ]
    return codeshare_offers