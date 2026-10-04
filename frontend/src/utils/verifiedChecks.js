// Pure helpers for the verified_checks feature (manual ground-truth price checks).
// Check records use the table's snake_case column names, as returned by GET /api/verified-checks.

// The sandbox_source value that means "the price source behind the result cards".
// Cards are Duffel test-mode prices today. MUST be changed when another source is wired
// into the cards, otherwise badges would vouch for prices the check never looked at.
export const CARD_SANDBOX_SOURCE = 'duffel';

export const VERDICT_MATCH = 'match';

// Mirrors MATCH_TOLERANCE (0.05) in api/_lib/verified_checks.py; change both together.
export const MATCH_TOLERANCE_PERCENT = 5;

const normalizeCarrier = (name) => String(name ?? '').trim().toLowerCase();

// True when a check is about this card: same route, flight_date equal to the searched
// departure date, and the same carrier name (trimmed, case-insensitive, exact).
// Never matches on flight number: FlightLabs flight numbers are unreliable.
export function matchesCard(check, { route, flightDate, carrierName }) {
    const carrier = normalizeCarrier(carrierName);
    if (!check || !route || !flightDate || !carrier) return false;
    return check.route === route
        && check.flight_date === flightDate
        && normalizeCarrier(check.carrier_checked) === carrier;
}

// The check that may be shown as a badge on a card, or null.
// Among checks for this card from the card's own price source, only the most recent
// check_date counts, and it must have verdict 'match'. If that latest check is a mismatch
// (or not_comparable), no badge is shown even when an older check matched.
export function findBadgeCheck(checks, card) {
    const candidates = (checks ?? []).filter(
        (check) => matchesCard(check, card) && check.sandbox_source === CARD_SANDBOX_SOURCE
    );
    if (candidates.length === 0) return null;
    const latestDate = candidates.reduce((max, c) => (c.check_date > max ? c.check_date : max), '');
    const latest = candidates.filter((c) => c.check_date === latestDate);
    return latest.every((c) => c.verdict === VERDICT_MATCH) ? latest[0] : null;
}

const isPresentPrice = (value) => typeof value === 'number' && Number.isFinite(value) && value !== 0;

// round((sandbox - real) / real * 100): positive when the tool price is higher.
// null when either price is missing (null/undefined/0) so the page shows 「—」.
export function priceDifferencePercent(sandboxPrice, realPrice) {
    if (!isPresentPrice(sandboxPrice) || !isPresentPrice(realPrice)) return null;
    return Math.round(((sandboxPrice - realPrice) / realPrice) * 100);
}
