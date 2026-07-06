## This module contains functions to normalize the raw response from the Duffel API into a more structured format.
def normalize_offers(raw_response):
    results = []
    for offers in raw_response.get("data", {}).get("offers",[]):
        offer_dict = {}
        offer_dict["Offer ID"] = offers['id']
        offer_dict["Total Amount"] = offers['total_amount']
        offer_dict["Currency"] = offers['total_currency']
        if offer_dict["Currency"] == "USD":
            offer_dict["Total Amount"] = round(float(offers['total_amount']) * 155)
            offer_dict["Currency"] = "JPY"
        offer_dict["Owner Airline"] = offers['owner']['name']
        offer_dict["Owner Airline IATA"] = offers['owner']['iata_code']
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
        results.append(offer_dict)
    return results