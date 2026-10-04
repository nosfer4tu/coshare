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
