from normalizer import normalize_offers

def get_codeshare_offers(raw_response):
    cleaned_offers = normalize_offers(raw_response)
    codeshare_offers = [offer for offer in cleaned_offers if offer.get("is Codeshare")]
    return codeshare_offers