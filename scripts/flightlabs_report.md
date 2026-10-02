# FlightLabs API Exploratory Test Report

## 1. Schema completeness: third-party issuer fields
**No** field resembling a third-party issuer/seller (seller, issuer, owner, validatingCarrier, etc.) was found in the response. FlightLabs appears to expose only marketingCarrier / operatingCarrier — no Hahn-Air-style ticketing-broker signal.

## 2. Price accuracy vs. ground truth (JAL/LATAM, NRT->GRU)
- Ground truth (book-i.jal.co.jp, hand-verified): ¥538,260
- **No offer with `marketingCarrier` containing "Japan Airlines" AND "LATAM" together was found** — FlightLabs did not return the specific JAL-issued/LATAM-operated combination the ground truth price is for. Nearest comparables below (not the same itinerary; treat the % diff as directional only):
  - Cheapest offer mentioning Japan Airlines: $1,163 USD -> ¥180,265 (marketingCarrier="Japan Airlines, Qatar Airways", flightNumber=None) — diff vs ground truth: ¥-357,995 (-66.5%)
  - Cheapest offer mentioning LATAM: $1,066 USD -> ¥165,230 (marketingCarrier="Cathay Pacific, LATAM Airlines", flightNumber=None) — diff vs ground truth: ¥-373,030 (-69.3%)

## 3. LCC coverage (domestic HND->CTS)
- Carrier names seen in response: ['ANA', 'Expedia', 'Japan Airlines']
- Peach: not found
- Jetstar Japan: not found
- ZIPAIR: not found
- Spring Airlines Japan: not found
- Skymark: not found
- **Data quality flag**: non-airline values appearing in `marketingCarrier`/`operatingCarrier`: ['Expedia'] (e.g. an OTA name where flightNumber is `null` — schema is not reliably airline-only).

## 4. NRT->LAX (NRT->LAX, 2026-11-26)
- Offers returned: 15
- Unique marketingCarrier values: ['ANA', 'Air Canada', 'American Airlines', 'China Airlines', 'EVA Air', 'Japan Airlines', 'Singapore Airlines', 'United Airlines', 'WestJet', 'ZIPAIR']
- Peach: not found
- Jetstar Japan: not found
- ZIPAIR: FOUND
- Spring Airlines Japan: not found
- Skymark: not found
- Cheapest: ¥65,410 | Most expensive: ¥339,605

## 5. KIX->ICN (Peach route) (KIX->ICN, 2026-11-26)
- Offers returned: 18
- Unique marketingCarrier values: ['Air Busan', 'Asiana Airlines', 'Eastar Jet', 'Hahn Air Systems', 'Jeju Air', 'Peach', "T'way Air"]
- Peach: FOUND
- Jetstar Japan: not found
- ZIPAIR: not found
- Spring Airlines Japan: not found
- Skymark: not found
- Cheapest: ¥12,245 | Most expensive: ¥22,010

## 6. NRT->OKA (Peach/Jetstar Japan/Skymark route) (NRT->OKA, 2026-11-26)
- Offers returned: 22
- Unique marketingCarrier values: ['ANA', 'FlightHub', 'Japan Transocean Air', 'Jetstar Japan', 'Peach']
- Peach: FOUND
- Jetstar Japan: FOUND
- ZIPAIR: not found
- Spring Airlines Japan: not found
- Skymark: not found
- Cheapest: ¥8,060 | Most expensive: ¥23,715

## Overall LCC Coverage Verdict
**Evidence of Japanese LCC coverage found** — FlightLabs does return these carriers on some routes, so coverage is not zero, but it's inconsistent:
- NRT->GRU (international, long-haul): (none found)
- HND->CTS (domestic): (none found)
- NRT->LAX (international, long-haul, but ZIPAIR operates it): ZIPAIR
- KIX->ICN (Peach route): Peach
- NRT->OKA (Peach/Jetstar Japan/Skymark route): Peach, Jetstar Japan

HND->CTS returned **zero** of the five target LCCs despite ANA/JAL both flying that route and Skymark, ADO, and AIRDO commonly serving Tokyo-Sapporo in reality — so the HND->CTS gap is real and route-specific, not evidence that FlightLabs lacks LCC data entirely. KIX->ICN and NRT->OKA both surfaced Peach correctly, and NRT->LAX surfaced ZIPAIR correctly, so LCC data does exist in FlightLabs for at least Peach and ZIPAIR — Jetstar Japan appeared once (NRT->OKA), Spring Airlines Japan and Skymark appeared on **none** of the 5 routes tested.

## Summary
- NRT->GRU offers returned: 31
- HND->CTS offers returned: 16
- NRT->LAX offers returned: 15
- KIX->ICN offers returned: 18
- NRT->OKA offers returned: 22
- Full raw responses dumped to `scripts/flightlabs_raw_dump.json` for manual inspection.