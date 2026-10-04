## This module contains functions to normalize the raw response from the Duffel API into a more structured format.

# Duffel test-mode returns this synthetic carrier alongside real airline data; exclude it everywhere.
EXCLUDED_TEST_CARRIERS = {"ZZ"}

def normalize_offers(raw_response):
    results = []
    for offers in raw_response.get("data", {}).get("offers",[]):
        first_segment = (offers.get("slices") or [{}])[0].get("segments") or [{}]
        display_carrier = first_segment[0].get("marketing_carrier") or {}
        if display_carrier.get("iata_code") in EXCLUDED_TEST_CARRIERS:
            continue
        offer_dict = {}
        offer_dict["Offer ID"] = offers['id']
        offer_dict["Total Amount"] = offers['total_amount']
        offer_dict["Currency"] = offers['total_currency']
        if offer_dict["Currency"] == "USD":
            offer_dict["Total Amount"] = round(float(offers['total_amount']) * 155)
            offer_dict["Currency"] = "JPY"
        offer_dict["Owner Airline"] = display_carrier.get("name") or offers['owner']['name']
        offer_dict["Owner Airline IATA"] = display_carrier.get("iata_code") or offers['owner']['iata_code']
        # Additive detail keys, all from slices[0].segments[0] (same segment as the display carrier).
        # Set before the loop below, which only overwrites the keys it assigns itself.
        offer_dict["Marketing Flight Number"] = first_segment[0].get("marketing_carrier_flight_number")
        offer_dict["Operating Flight Number"] = first_segment[0].get("operating_carrier_flight_number")
        offer_dict["Departure Airport"] = (first_segment[0].get("origin") or {}).get("iata_code")
        offer_dict["Arrival Airport"] = (first_segment[0].get("destination") or {}).get("iata_code")
        offer_dict["Segment Count"] = len((offers.get("slices") or [{}])[0].get("segments") or [])
        for flight_slice in offers.get("slices",[]):
            for segment in flight_slice.get("segments", []):
                operating_carrier = segment.get("operating_carrier", {})
                offer_dict["Operating Carrier"] = operating_carrier.get('name')
                offer_dict["Operating IATA"] = operating_carrier.get('iata_code')
                marketing_carrier = segment.get("marketing_carrier", {})
                offer_dict["Marketing Carrier"] = marketing_carrier.get('name')
                offer_dict["Marketing IATA"] = marketing_carrier.get('iata_code')
                offer_dict["Departure Time"] = segment.get('departing_at')
                offer_dict["Arrival Time"] = segment.get('arriving_at')
                offer_dict["is Codeshare"] = False
                if operating_carrier.get("iata_code") != marketing_carrier.get("iata_code") or offers['owner']['iata_code'] != segment.get("operating_carrier", {}).get("iata_code"):
                    offer_dict["is Codeshare"] = True
                # Badge flag: sold under a different code than the one operating. Unlike
                # 'is Codeshare' it ignores offer.owner (the ticketing entity).
                offer_dict["is Marketing Codeshare"] = marketing_carrier.get("iata_code") != operating_carrier.get("iata_code")
        results.append(offer_dict)
    return results