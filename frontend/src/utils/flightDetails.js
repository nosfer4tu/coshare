// Expandable details are shown for direct offers only. "Segment Count" is absent on
// search_cache rows written before it existed, so those offers (and connecting ones)
// simply get no toggle.
export function hasDetails(offer) {
    return offer["Segment Count"] === 1;
}

// Duffel flight numbers are bare strings ("0157"); prefix the carrier code.
// Returns null when the number is absent so the row is omitted.
export function formatFlightNumber(iata, number, name) {
    if (!number) return null;
    const designator = iata ? `${iata} ${number}` : number;
    return name ? `${designator}（${name}）` : designator;
}

// "KIX 2026/12/16 8:25:00" — either half may be missing.
export function formatPoint(airport, isoTime) {
    const time = isoTime ? new Date(isoTime).toLocaleString('ja-JP') : null;
    return [airport, time].filter(Boolean).join(' ') || null;
}

// The departure to SHOW. "Departure Time" holds the last leg's departure on a connection, so
// it is only the fallback (older search_cache rows have no "First Departure Time"). Never use
// this for grouping/pairing or verified-check matching; those keep "Departure Time".
export function displayDeparture(offer) {
    return offer["First Departure Time"] ?? offer["Departure Time"];
}

// "乗り継ぎ1回" for a 2-segment offer; null for direct offers and for older cache rows
// without "Segment Count". When set, the last leg's operator does not describe the trip.
export function connectionLabel(offer) {
    const count = offer["Segment Count"];
    return count > 1 ? `乗り継ぎ${count - 1}回` : null;
}
