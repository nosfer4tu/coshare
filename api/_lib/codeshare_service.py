from normalizer import normalize_offers

TICKETING_CARRIERS = {"HR"}


def _is_codeshare_offer(offer):
    return bool(offer.get("is Codeshare")) and offer.get("Owner Airline IATA") not in TICKETING_CARRIERS


def _pair_key(offer):
    """The key the frontend's groupOffers pairs on, or None when the offer cannot be paired:
    connecting offers (their key describes only the last leg) and rows without the key fields."""
    if (offer.get("Segment Count") or 1) > 1:
        return None
    if offer.get("Departure Time") is None or offer.get("Operating IATA") is None:
        return None
    return (offer.get("Departure Airport"), offer.get("Arrival Airport"),
            offer["Departure Time"], offer["Operating IATA"])


def filter_codeshare_offers(normalized_offers):
    # Keep every offer that is itself a codeshare offer, plus the other (non-HR) offers of any
    # group that contains one, so the operating carrier's own-code offer stays next to the
    # codeshare offer it is compared with.
    anchored = {key for offer in normalized_offers
                if _is_codeshare_offer(offer) and (key := _pair_key(offer)) is not None}
    return [
        offer for offer in normalized_offers
        if _is_codeshare_offer(offer)
        or (offer.get("Owner Airline IATA") not in TICKETING_CARRIERS and _pair_key(offer) in anchored)
    ]


def get_codeshare_offers(raw_response):
    return filter_codeshare_offers(normalize_offers(raw_response))
