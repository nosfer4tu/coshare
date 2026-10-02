# FlightLabs International Verification Candidates

Route: NRT -> LAX, date: 2026-11-26
Filter: flightNumber present, single real-airline marketingCarrier (no OTA/broker names, no comma-joined multi-carrier strings), operatingCarrier == marketingCarrier (non-codeshare only). Same filter as flightlabs_verification_candidates.py (NRT->OKA).
15 raw offers -> 14 passed the filter -> 5 shown below.

**WARNING: flightNumber looks like a placeholder index, not a real flight number** on this route - 5/5 candidates have a bare 1-2 digit value (e.g. "1") instead of an airline code + digits (e.g. "ZG001"). These cannot be looked up by flight number on the airline's site - verify by carrier + route + departure time/date instead.

A ZIPAIR offer is among the top 5 cheapest candidates below.

| Flight # | Marketing Carrier | Departure | Arrival | Price (orig.) | Price (JPY) |
|---|---|---|---|---|---|
| 1 | ZIPAIR | 2026-11-26T14:45:00 | 2026-11-27T07:30:00 | 482 USD | ¥74,710 |
| 1 | American Airlines | 2026-11-26T17:05:00 | 2026-11-27T09:40:00 | 504 USD | ¥78,120 |
| 1 | China Airlines | 2026-11-26T19:30:00 | 2026-11-27T07:25:00 | 792 USD | ¥122,760 |
| 1 | China Airlines | 2026-11-26T17:30:00 | 2026-11-27T07:25:00 | 792 USD | ¥122,760 |
| 1 | Air Canada | 2026-11-26T18:15:00 | 2026-11-27T14:16:00 | 818 USD | ¥126,790 |
