import { test } from 'node:test';
import assert from 'node:assert/strict';
import { fetchRealPrices, normalizeSearch, skyscannerUrl } from './realPrices.js';

const search = { origin: 'KIX', destination: 'TPE', departureDate: '2026-12-03' };

const respond = (status, body) => async () => ({
    status,
    ok: status >= 200 && status < 300,
    json: async () => {
        if (body instanceof Error) throw body;
        return body;
    },
});

test('normalizeSearch: uppercases and trims codes', () => {
    assert.deepEqual(normalizeSearch(' kix ', 'tpe', '2026-12-03'), search);
});

test('normalizeSearch: null when a code or the date is unusable', () => {
    for (const args of [['', 'TPE', '2026-12-03'], ['KIX', 'TAIPEI', '2026-12-03'],
        ['KIX', 'TPE', ''], ['KIX', 'TPE', '2026/12/03'], [null, undefined, null]]) {
        assert.equal(normalizeSearch(...args), null, JSON.stringify(args));
    }
});

test('skyscannerUrl: lowercase codes and yymmdd', () => {
    assert.equal(
        skyscannerUrl(search),
        'https://www.skyscanner.jp/transport/flights/kix/tpe/261203/?adultsv2=1&cabinclass=economy',
    );
});

test('fetchRealPrices: sends uppercase params to /api/real-prices', async () => {
    let requested;
    await fetchRealPrices(search, { fetchImpl: async (url) => { requested = url; return respond(200, { found: false })(); } });
    assert.equal(requested, '/api/real-prices?origin=KIX&destination=TPE&departureDate=2026-12-03');
});

test('fetchRealPrices: found', async () => {
    const body = { found: true, flight_date: '2026-12-03', captured_on: '2026-10-19', source: 's', entries: [], summary: {} };
    const result = await fetchRealPrices(search, { fetchImpl: respond(200, body) });
    assert.equal(result.status, 'found');
    assert.equal(result.data, body);
});

test('fetchRealPrices: found:false is notFound', async () => {
    const result = await fetchRealPrices(search, { fetchImpl: respond(200, { found: false }) });
    assert.deepEqual(result, { status: 'notFound' });
});

test('fetchRealPrices: 400 hides the panel', async () => {
    const result = await fetchRealPrices(search, { fetchImpl: respond(400, { error: 'x' }) });
    assert.deepEqual(result, { status: 'hidden' });
});

test('fetchRealPrices: other non-200 responses are no data', async () => {
    for (const status of [404, 500, 502, 204]) {
        const result = await fetchRealPrices(search, { fetchImpl: respond(status, {}) });
        assert.deepEqual(result, { status: 'noData' }, String(status));
    }
});

test('fetchRealPrices: network error is no data, never throws', async () => {
    const result = await fetchRealPrices(search, { fetchImpl: async () => { throw new TypeError('Failed to fetch'); } });
    assert.deepEqual(result, { status: 'noData' });
});

test('fetchRealPrices: malformed bodies are no data', async () => {
    for (const body of [new SyntaxError('bad json'), null, {}, { found: true }, { found: true, entries: 'x' }]) {
        const result = await fetchRealPrices(search, { fetchImpl: respond(200, body) });
        assert.deepEqual(result, { status: 'noData' }, String(body));
    }
});
