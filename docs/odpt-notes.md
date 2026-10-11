# ODPT research notes (2026-10-11)

Status: **JAL and ANA `FlightInformationDeparture` tested (one request each).** Facts below come from
those two responses or from pages read in this session. Nothing is from memory of the API, except where
a line says so. The API key is never written here; request URLs show `<REDACTED>`.

## Sources

- Dataset pages (URLs given by the owner; the JAL and ANA dataset descriptions on ckan.odpt.org were read on 2026-10-11; the API responses were tested separately):
  - JAL: https://ckan.odpt.org/dataset/a_flight_departure_info-jal
  - ANA: https://ckan.odpt.org/dataset/a_flight_departure_info-ana
- **JAL note (confirmed on 2026-10-11 in the JAL dataset descriptions; see the next bullet): codeshare information may be
  missing from the JAL data.** The JAL response matches this: it has no codeshare field and no mention of
  codeshare in any text (see Findings).
- 2026-10-11: the JAL departure and arrival dataset descriptions at https://ckan.odpt.org/dataset/a_flight_departure_info-jal
  and https://ckan.odpt.org/en/dataset/a_flight_arrival_info-jal state that information on codeshare
  flights operated by other airlines may differ from what is disclosed or may not be published.

## Verified earlier (pages read, 2026-10-11)

- ODPT = 公共交通オープンデータ協議会 (Public Transportation Open Data Council). Its Open Data Center
  has run since 2019-05-31. Source: https://www.odpt.org/
- Developer site: https://developer.odpt.org. Per odpt.org, using the data requires free user
  registration there, and the API specifications are listed on that site.
- Data catalog (CKAN): https://ckan.odpt.org. It lists 370 datasets (19 pages of 20). Page 1 holds only
  bus, tram and ferry data. The catalog's own licence list includes 公共交通オープンデータ基本ライセンス
  and 公共交通オープンデータチャレンジ限定ライセンス.
- Public CKAN pages did not need a login.

## Test requests (2026-10-11, about 18:25 JST)

```
GET https://api.odpt.org/api/v4/odpt:FlightInformationDeparture?odpt:operator=odpt.Operator:JAL&acl:consumerKey=<REDACTED>
GET https://api.odpt.org/api/v4/odpt:FlightInformationDeparture?odpt:operator=odpt.Operator:ANA&acl:consumerKey=<REDACTED>
```

| | JAL | ANA |
|---|---|---|
| HTTP status | 200 | 200 |
| Records (JSON array) | 892 | 1144 |
| Body size | 660,378 bytes | 782,389 bytes |

- Both requests were made with Python `urllib`, key read in memory from `.env.local`.
- Python 3.11.3 (python.org build) first failed the TLS handshake on both
  (`CERTIFICATE_VERIFY_FAILED: self signed certificate in certificate chain`). No HTTP request was sent, so the
  key was not transmitted. The retry used the macOS CA bundle `/etc/ssl/cert.pem` with verification on and
  succeeded. The cause of the first failure was not investigated. Do not disable verification to work around it.

## Findings

### Fields of one record

`@id`, `@type`, `@context`, `dc:date`, `dct:valid`, `owl:sameAs`, `odpt:airline`, `odpt:operator`,
`odpt:aircraftType`, `odpt:flightNumber` (an array), `odpt:flightStatus`, `odpt:departureGate`,
`odpt:departureAirport`, `odpt:destinationAirport`, `odpt:actualDepartureTime`,
`odpt:scheduledDepartureTime`, `odpt:estimatedDepartureTime`, `odpt:departureAirportTerminal`,
`odpt:flightInformationText` (`{en, ja}`), `odpt:flightInformationSummary` (`{en, ja}`).

Always present in both datasets: `@id`, `@type`, `@context`, `dc:date`, `dct:valid`, `owl:sameAs`,
`odpt:airline`, `odpt:operator`, `odpt:flightNumber`, `odpt:departureAirport`,
`odpt:destinationAirport`, `odpt:scheduledDepartureTime`. The rest are optional per record (for example
`odpt:aircraftType` is missing on 132 of 1144 ANA records, and ANA has `odpt:departureGate` on only 368 of 1144).

There is no price, no fare, no arrival time, no date on any time field (`"HH:MM"` only) and no codeshare field.

### Scope of the data

- It is a live departure board: all `dc:date` values are 2026-10-11 between 18:24 and 18:28 JST, and
  `dct:valid` is 7 to 11 minutes after `dc:date`. Scheduled times run 00:05 to 22:00 (JAL) and 00:05 to
  23:55 (ANA), so it covers today's departures only, not future dates.
- `odpt:flightStatus` values seen: `Departed`, `InAir`, `EstimatedDeparture`, `LeftGate`, `Cancelled`, or absent.

### International flights

**Yes, in both.** Airport codes are IATA only; there is no country field, so "international" below is
judged from the codes (my knowledge, not the data).

- JAL: 56 distinct departure airports, all Japanese. Destinations include 36 foreign airports:
  TPE BKK HNL LAX SIN SFO HKG PVG GMP JFK ORD PEK DEL LHR MNL SGN TSA ICN DFW DLC CDG HEL SYD SHA CAN
  BOS YVR SAN SEA FRA KUL CGK HAN BLR MEL GUM.
- ANA: 88 distinct departure airports: 51 Japanese and 37 foreign. Foreign airports appear as
  **departure** airports too (outbound legs from abroad, for example `NH204` FRA to HND):
  YVR FRA ARN BKK BOM CAN CDG CGK DEL DLC GMP HAN HKG HNL IAD IAH JFK KUL LAX LHR MEX MNL MUC MXP ORD PEK
  PVG SEA SFO SGN SHA SIN TSA SYD SZX TAO VIE.
- Busiest departure airports: JAL HND 229, ITM 88, OKA 60, FUK 49, CTS 43; ANA HND 314, ITM 96, CTS 84,
  FUK 80, OKA 58.

### More than one flight number per record?

**No.** `odpt:flightNumber` is an array, but every record in both datasets has exactly one entry
(JAL 892 of 892, ANA 1144 of 1144). No record lists a codeshare partner's flight number.

### A flight operated by another airline?

- **ANA: no.** All 1144 records have `odpt:airline` = `odpt:operator` = `odpt.Operator:ANA` and every flight
  number starts with `NH`.
- **JAL: yes, in the sense of another airline code.** 109 of 892 records have `odpt:airline` different from
  `odpt:operator` (which is always `odpt.Operator:JAL`):

  | `odpt:airline` | Records | Flight number prefix |
  |---|---|---|
  | `odpt.Operator:JAL` | 783 | JL |
  | `odpt.Operator:JTA` | 66 | NU |
  | `odpt.Operator:RAC` | 36 | NU |
  | `odpt.Operator:TZP` | 7 | ZG |

  The data holds only these codes, no airline names. It does **not** say whether such a flight is a codeshare
  or has a JL number as well. Treat them as "listed under JAL, operated by another carrier code".
- No record in either dataset contains 共同運航, コードシェア, "codeshare" or "operated by".
  (JAL has the word 運航 in 30 records, all in the text 「JAL Jubilee Expressで運航いたします」.)
- So neither dataset can tell us which flights are codeshares. This confirms the owner's JAL note and
  extends it to ANA.

### Airport and other codes

- Airports: `odpt.Airport:HND`; terminals: `odpt.AirportTerminal:HND.Terminal3`; statuses:
  `odpt.FlightStatus:Departed`; operators: `odpt.Operator:JAL`. `owl:sameAs` is
  `odpt.FlightInformationDeparture:<operator>.<departure airport>.<flight number>`.
- `@context` differs by operator: JAL `context_odpt_FlightInformationDeparture.jsonld`, ANA `context_odpt.jsonld`.

## Redacted samples (5 records in total; all values as returned, no key in them)

Chosen to show an international flight, another carrier code under JAL, a delay with text, an ANA
flight departing Japan and one departing abroad. "Five records at most" was read as five in total.

### JAL

```json
{
  "@id": "urn:uuid:257e3cab-1b3d-4d56-b7a6-96b1537649de",
  "@type": "odpt:FlightInformationDeparture",
  "dc:date": "2026-10-11T18:26:15+09:00",
  "@context": "http://vocab.odpt.org/context_odpt_FlightInformationDeparture.jsonld",
  "dct:valid": "2026-10-11T18:33:15+09:00",
  "owl:sameAs": "odpt.FlightInformationDeparture:JAL.HND.JL002",
  "odpt:airline": "odpt.Operator:JAL",
  "odpt:operator": "odpt.Operator:JAL",
  "odpt:aircraftType": "77W",
  "odpt:flightNumber": ["JL002"],
  "odpt:flightStatus": "odpt.FlightStatus:InAir",
  "odpt:departureGate": "113",
  "odpt:departureAirport": "odpt.Airport:HND",
  "odpt:destinationAirport": "odpt.Airport:SFO",
  "odpt:actualDepartureTime": "16:18",
  "odpt:scheduledDepartureTime": "16:20",
  "odpt:departureAirportTerminal": "odpt.AirportTerminal:HND.Terminal3"
}
```

```json
{
  "@id": "urn:uuid:c756d092-00d9-4646-b04e-5dd58460b428",
  "@type": "odpt:FlightInformationDeparture",
  "dc:date": "2026-10-11T18:26:15+09:00",
  "@context": "http://vocab.odpt.org/context_odpt_FlightInformationDeparture.jsonld",
  "dct:valid": "2026-10-11T18:33:15+09:00",
  "owl:sameAs": "odpt.FlightInformationDeparture:JAL.HND.JL119",
  "odpt:airline": "odpt.Operator:JAL",
  "odpt:operator": "odpt.Operator:JAL",
  "odpt:aircraftType": "788",
  "odpt:flightNumber": ["JL119"],
  "odpt:flightStatus": "odpt.FlightStatus:Departed",
  "odpt:departureGate": "14",
  "odpt:departureAirport": "odpt.Airport:HND",
  "odpt:destinationAirport": "odpt.Airport:ITM",
  "odpt:actualDepartureTime": "13:33",
  "odpt:flightInformationText": {
    "en": "due to late arrival of aircraft.",
    "ja": "使用する飛行機の到着遅れのため出発に遅延が生じています。"
  },
  "odpt:scheduledDepartureTime": "13:30",
  "odpt:departureAirportTerminal": "odpt.AirportTerminal:HND.Terminal1",
  "odpt:flightInformationSummary": { "en": "Delayed", "ja": "出発遅延" }
}
```

```json
{
  "@id": "urn:uuid:87287791-e374-45b4-a424-ccad445621e9",
  "@type": "odpt:FlightInformationDeparture",
  "dc:date": "2026-10-11T18:26:20+09:00",
  "@context": "http://vocab.odpt.org/context_odpt_FlightInformationDeparture.jsonld",
  "dct:valid": "2026-10-11T18:33:20+09:00",
  "owl:sameAs": "odpt.FlightInformationDeparture:JAL.FUK.NU051",
  "odpt:airline": "odpt.Operator:JTA",
  "odpt:operator": "odpt.Operator:JAL",
  "odpt:aircraftType": "73H",
  "odpt:flightNumber": ["NU051"],
  "odpt:flightStatus": "odpt.FlightStatus:Departed",
  "odpt:departureGate": "6",
  "odpt:departureAirport": "odpt.Airport:FUK",
  "odpt:destinationAirport": "odpt.Airport:OKA",
  "odpt:actualDepartureTime": "07:13",
  "odpt:scheduledDepartureTime": "07:15",
  "odpt:departureAirportTerminal": "odpt.AirportTerminal:FUK.Domestic(Security:North)"
}
```

### ANA

```json
{
  "@id": "urn:uuid:0408c536-8f73-45e1-9b38-eb1abac27226",
  "@type": "odpt:FlightInformationDeparture",
  "dc:date": "2026-10-11T18:25:25+09:00",
  "@context": "http://vocab.odpt.org/context_odpt.jsonld",
  "dct:valid": "2026-10-11T18:36:25+09:00",
  "owl:sameAs": "odpt.FlightInformationDeparture:ANA.HND.NH849",
  "odpt:airline": "odpt.Operator:ANA",
  "odpt:operator": "odpt.Operator:ANA",
  "odpt:flightNumber": ["NH849"],
  "odpt:flightStatus": "odpt.FlightStatus:Departed",
  "odpt:departureAirport": "odpt.Airport:HND",
  "odpt:destinationAirport": "odpt.Airport:BKK",
  "odpt:actualDepartureTime": "23:59",
  "odpt:scheduledDepartureTime": "00:05",
  "odpt:departureAirportTerminal": "odpt.AirportTerminal:HND.Terminal2"
}
```

```json
{
  "@id": "urn:uuid:636f4aef-f1d4-48a8-a4e1-02eea9dbf077",
  "@type": "odpt:FlightInformationDeparture",
  "dc:date": "2026-10-11T18:24:38+09:00",
  "@context": "http://vocab.odpt.org/context_odpt.jsonld",
  "dct:valid": "2026-10-11T18:35:38+09:00",
  "owl:sameAs": "odpt.FlightInformationDeparture:ANA.FRA.NH204",
  "odpt:airline": "odpt.Operator:ANA",
  "odpt:operator": "odpt.Operator:ANA",
  "odpt:flightNumber": ["NH204"],
  "odpt:flightStatus": "odpt.FlightStatus:EstimatedDeparture",
  "odpt:departureAirport": "odpt.Airport:FRA",
  "odpt:destinationAirport": "odpt.Airport:HND",
  "odpt:estimatedDepartureTime": "12:10",
  "odpt:scheduledDepartureTime": "12:10"
}
```

Note on the first ANA sample: `scheduledDepartureTime` 00:05 and `actualDepartureTime` 23:59 are on different
calendar days, and the record has no date field, so the day cannot be read from the record.

## Still not verified

- Authentication rules beyond the `acl:consumerKey` parameter, rate limits, terms of use, attribution and
  licence for these two datasets. The JAL and ANA dataset descriptions on ckan.odpt.org were read on 2026-10-11. The
  developer site's pages (API specification, rate limits, terms of use) could not be read by the
  tool and remain unread.
- Whether an ODPT dataset exists that carries codeshare relationships, or other airlines' departures.
  Only catalog page 1 of 19 was read earlier.
- Whether the API can return anything other than today's board (no date parameter was tried; none was
  requested).
- The cause of the Python TLS failure (a self-signed certificate was reported in the chain).

## Product implication (observation, not a decision)

These two feeds describe today's departures only, carry no price and no codeshare marker, and give one
flight number per record. On their own they cannot detect a codeshare pair or a price gap for CoShare.jp.
Whether they could back a "status of this flight" display is a separate question, not covered here.
