// Pure helpers for the "実測価格との比較" panel (GET /api/real-prices). No React, no DOM.

const ISO_DATE = /^\d{4}-\d{2}-\d{2}$/;
const AIRPORT_CODE = /^[A-Z0-9]{3}$/;

export const NO_DATA = { status: 'noData' };
export const HIDDEN = { status: 'hidden' };

// Normalise the committed search params. Returns null when they cannot form a valid
// request (the panel is then hidden and no request is made).
export function normalizeSearch(origin, destination, departureDate) {
    const from = String(origin ?? '').trim().toUpperCase();
    const to = String(destination ?? '').trim().toUpperCase();
    const date = String(departureDate ?? '').trim();
    if (!AIRPORT_CODE.test(from) || !AIRPORT_CODE.test(to) || !ISO_DATE.test(date)) return null;
    return { origin: from, destination: to, departureDate: date };
}

// https://www.skyscanner.jp/transport/flights/kix/tpe/261203/?adultsv2=1&cabinclass=economy
export function skyscannerUrl({ origin, destination, departureDate }) {
    const yymmdd = departureDate.slice(2).replaceAll('-', '');
    return `https://www.skyscanner.jp/transport/flights/${origin.toLowerCase()}/${destination.toLowerCase()}/${yymmdd}/?adultsv2=1&cabinclass=economy`;
}

export function formatYen(value) {
    return Number(value).toLocaleString('ja-JP', { style: 'currency', currency: 'JPY' });
}

// Whether the panel renders anything for this hook result (nothing while loading or on 400).
export function isPanelVisible(state, search) {
    return Boolean(search) && state.status !== 'hidden' && state.status !== 'loading';
}

function isFoundBody(body) {
    return Boolean(body) && body.found === true && Array.isArray(body.entries);
}

// Result of GET /api/real-prices as a panel state. Never throws:
//   { status: 'found', data } | { status: 'notFound' } | { status: 'noData' } | { status: 'hidden' }
// 400 hides the panel; any other non-200 response, a network error or a malformed body
// is "no data" (the panel shows the muted line, never an error banner).
export async function fetchRealPrices(search, { fetchImpl = fetch, signal } = {}) {
    const params = new URLSearchParams({
        origin: search.origin,
        destination: search.destination,
        departureDate: search.departureDate,
    });
    try {
        const response = await fetchImpl('/api/real-prices?' + params.toString(), { signal });
        if (response.status === 400) return HIDDEN;
        if (response.status !== 200) return NO_DATA;
        const body = await response.json();
        if (isFoundBody(body)) return { status: 'found', data: body };
        if (body && body.found === false) return { status: 'notFound' };
        return NO_DATA;
    } catch {
        return NO_DATA;
    }
}
