// Renders the panel to static HTML. Vite's SSR loader compiles the JSX and ignores the CSS
// import, so no DOM or extra test dependency is needed.
import { test, before, after } from 'node:test';
import assert from 'node:assert/strict';
import { createServer } from 'vite';
import { createElement } from 'react';
import { renderToStaticMarkup } from 'react-dom/server';

const search = { origin: 'KIX', destination: 'TPE', departureDate: '2026-12-03' };

const lcc = {
    kind: 'lcc', airline: 'Jetstar Japan', dep: '23:10', arr: '01:30', arr_next_day: true,
    stops: 0, price_jpy: 20718, seller: '最安の予約サイト',
};
const cheapFull = {
    kind: 'full_service', airline: 'China Airlines', flight_number: 'CI157', dep: '12:45', arr: '15:00',
    stops: 0, price_jpy: 36849, seller: 'Kiwi.com', airline_site_price_jpy: 36850,
};
const br = {
    kind: 'full_service', airline: 'EVA Air', flight_number: 'BR131', dep: '12:55', arr: '15:05',
    stops: 0, price_jpy: 40828, seller: 'HIS',
};
const nh = {
    kind: 'full_service', airline: 'ANA', flight_number: 'NH5811', dep: '12:55', arr: '15:05',
    stops: 0, price_jpy: 195727, seller: 'Expedia', note: '販売元は1社のみ',
};
const found = {
    status: 'found',
    data: {
        found: true, flight_date: '2026-12-03', captured_on: '2026-10-19', source: 'Skyscanner(手動確認)',
        entries: [lcc, cheapFull, br, nh],
        summary: {
            cheapest_lcc: lcc,
            cheapest_full_service: cheapFull,
            codeshare_pairs: [{
                cheaper: { airline: 'EVA Air', flight_number: 'BR131', price_jpy: 40828, seller: 'HIS' },
                pricier: { airline: 'ANA', flight_number: 'NH5811', price_jpy: 195727, seller: 'Expedia' },
                gap_jpy: 154899,
            }],
        },
    },
};

let server;
let render;

before(async () => {
    server = await createServer({
        server: { middlewareMode: true },
        appType: 'custom',
        logLevel: 'silent',
    });
    const mod = await server.ssrLoadModule('/src/components/results/RealPricesPanel.jsx');
    render = (props) => renderToStaticMarkup(createElement(mod.default, props));
});

after(async () => {
    await server.close();
});

test('found: header with check date, source and the disclaimer', () => {
    const html = render({ state: found, search });
    assert.match(html, /実測価格との比較/);
    assert.match(html, /手動で確認した実際の価格\(確認日 <span[^>]*>2026-10-19<\/span>\)。現在の価格とは異なる場合があります/);
    assert.ok(html.includes('Skyscanner(手動確認)'));
});

test('found: cheapest LCC and cheapest full-service lines', () => {
    const html = render({ state: found, search });
    assert.match(html, /最安LCC/);
    assert.match(html, /Jetstar Japan/);
    assert.match(html, /￥20,718|¥20,718/);
    assert.match(html, /最安フルサービス/);
    assert.match(html, /CI157/);
    assert.match(html, /￥36,849|¥36,849/);
});

test('found: codeshare pair shows both prices, both sellers and the gap', () => {
    const html = render({ state: found, search });
    assert.match(html, /BR131/);
    assert.match(html, /NH5811/);
    assert.match(html, /HIS/);
    assert.match(html, /Expedia/);
    assert.match(html, /差額 <span[^>]*>(￥|¥)154,899<\/span>/);
});

test('found: all entries in an expandable table, LCC badge only on LCC rows', () => {
    const html = render({ state: found, search });
    assert.match(html, /<details/);
    assert.match(html, /全4件の価格を見る/);
    assert.equal((html.match(/<tr>/g) ?? []).length, 5); // 1 header row + 4 entries
    assert.equal((html.match(/real-prices__badge/g) ?? []).length, 1);
    assert.match(html, /LCC<\/span>/);
    assert.match(html, /\(翌日\)/);
    assert.match(html, /販売元は1社のみ/);
});

test('found: does not show the not-found line or a Skyscanner link', () => {
    const html = render({ state: found, search });
    assert.doesNotMatch(html, /実測データはまだありません/);
    assert.doesNotMatch(html, /skyscanner/);
});

test('found: tolerates a missing summary without throwing', () => {
    const html = render({ state: { status: 'found', data: { ...found.data, summary: undefined } }, search });
    assert.match(html, /実測価格との比較/);
    assert.doesNotMatch(html, /最安LCC/);
});

test('notFound: one muted line plus a Skyscanner link for the same route and date', () => {
    const html = render({ state: { status: 'notFound' }, search });
    assert.match(html, /この路線・日付の実測データはまだありません/);
    assert.match(
        html,
        /href="https:\/\/www\.skyscanner\.jp\/transport\/flights\/kix\/tpe\/261203\/\?adultsv2=1&amp;cabinclass=economy"/,
    );
    assert.match(html, /target="_blank"/);
    assert.match(html, /rel="noopener noreferrer"/);
    assert.doesNotMatch(html, /<details/);
});

test('error / no data: same muted line as notFound, no error banner', () => {
    const html = render({ state: { status: 'noData' }, search });
    assert.match(html, /この路線・日付の実測データはまだありません/);
    assert.match(html, /skyscanner\.jp/);
    assert.doesNotMatch(html, /エラー|status-message--error/);
});

test('hidden (400), loading and missing search render nothing', () => {
    assert.equal(render({ state: { status: 'hidden' }, search }), '');
    assert.equal(render({ state: { status: 'loading' }, search }), '');
    assert.equal(render({ state: { status: 'noData' }, search: null }), '');
});

// NRT-BOM 2027-02-22: no LCC at all (summary.cheapest_lcc is null) and exactly one pair.
const nrtSearch = { origin: 'NRT', destination: 'BOM', departureDate: '2027-02-22' };
const nhOfficial = {
    kind: 'full_service', airline: 'ANA', marketing_code: 'NH', flight_number: 'NH829', dep: '11:15', arr: '18:35',
    stops: 0, price_jpy: 299970, seller: 'ANA公式サイト', airline_site_price_jpy: 299970, same_flight_as: 'AI8001',
    note: 'スクレイパーの最安値は¥103,336(Kiwi.com)で、公式価格より30%以上低い外れ値のため公式価格を掲載',
};
const aiOfficial = {
    kind: 'full_service', airline: 'Air India', marketing_code: 'AI', flight_number: 'AI8001', operating_code: 'NH',
    dep: '11:15', arr: '18:35', stops: 0, price_jpy: 216870, seller: 'Air India公式サイト',
    airline_site_price_jpy: 216870,
};
const nrtBom = {
    status: 'found',
    data: {
        found: true, flight_date: '2027-02-22', captured_on: '2026-11-23',
        source: 'Skyscanner(スクレイパーAPI・一部手動確認)',
        entries: [aiOfficial, nhOfficial],
        summary: {
            cheapest_lcc: null,
            cheapest_full_service: aiOfficial,
            codeshare_pairs: [{
                cheaper: { airline: 'Air India', flight_number: 'AI8001', price_jpy: 216870, seller: 'Air India公式サイト' },
                pricier: { airline: 'ANA', flight_number: 'NH829', price_jpy: 299970, seller: 'ANA公式サイト' },
                gap_jpy: 83100,
            }],
        },
    },
};

test('found: says the panel covers nonstop flights only', () => {
    assert.match(render({ state: found, search }), /直行便のみ/);
    assert.match(render({ state: nrtBom, search: nrtSearch }), /直行便のみ/);
});

test('found without LCC entries (null cheapest_lcc): no LCC line, no crash, full-service line stays', () => {
    const html = render({ state: nrtBom, search: nrtSearch });
    assert.doesNotMatch(html, /最安LCC/);
    assert.doesNotMatch(html, /real-prices__badge/);
    assert.match(html, /最安フルサービス/);
    assert.match(html, /AI8001/);
    assert.match(html, /Air India公式サイト/);
});

test('found without LCC entries: summary lines render when both cheapest entries are null', () => {
    const noLines = { ...nrtBom, data: { ...nrtBom.data, summary: { ...nrtBom.data.summary, cheapest_full_service: null } } };
    const html = render({ state: noLines, search: nrtSearch });
    assert.doesNotMatch(html, /最安LCC|最安フルサービス/);
    assert.match(html, /同じ便の価格差/);
});

test('NRT-BOM: exactly one pair with the gap, plus the official-price note and site column', () => {
    const html = render({ state: nrtBom, search: nrtSearch });
    assert.equal((html.match(/class="real-prices__pair"/g) ?? []).length, 1);
    assert.match(html, /差額 <span[^>]*>(￥|¥)83,100<\/span>/);
    assert.match(html, /全2件の価格を見る/);
    assert.match(html, /公式サイト/);
    assert.match(html, /外れ値のため公式価格を掲載/);
});

// KIX-TPE 2027-02-22: three pairs on one route, in the order the API returns them (gap descending).
const kixFeb = { origin: 'KIX', destination: 'TPE', departureDate: '2027-02-22' };
const side = (airline, flight_number, price_jpy, seller) => ({ airline, flight_number, price_jpy, seller });
const threePairs = {
    status: 'found',
    data: {
        found: true, flight_date: '2027-02-22', captured_on: '2026-11-23',
        source: 'Skyscanner(スクレイパーAPI・一部手動確認)',
        entries: [lcc, cheapFull],
        summary: {
            cheapest_lcc: lcc,
            cheapest_full_service: cheapFull,
            codeshare_pairs: [
                {
                    cheaper: side('EVA Air', 'BR131', 40688, 'Flightnetwork'),
                    pricier: side('ANA', 'NH5811', 196807, 'Kiwi.com'), gap_jpy: 156119,
                },
                {
                    cheaper: side('China Airlines', 'CI157', 39509, 'Kiwi.com'),
                    pricier: side('Japan Airlines', 'JL5103', 101590, 'TeaFlight'), gap_jpy: 62081,
                },
                {
                    cheaper: side('China Airlines', 'CI153', 39509, 'Kiwi.com'),
                    pricier: side('Japan Airlines', 'JL5105', 101590, 'TeaFlight'), gap_jpy: 62081,
                },
            ],
        },
    },
};

test('three pairs on one route: all render, in the order given, each with its own gap', () => {
    const html = render({ state: threePairs, search: kixFeb });
    assert.equal((html.match(/class="real-prices__pair"/g) ?? []).length, 3);
    const at = (text) => html.indexOf(text);
    const order = [at('NH5811'), at('JL5103'), at('JL5105')];
    assert.ok(order.every((i) => i > -1), 'every pricier flight is rendered');
    assert.deepEqual(order, [...order].sort((a, b) => a - b));
    assert.equal((html.match(/差額 <span[^>]*>(￥|¥)62,081<\/span>/g) ?? []).length, 2);
    assert.match(html, /差額 <span[^>]*>(￥|¥)156,119<\/span>/);
});

test('three pairs on one route: no duplicate React keys (each pair has distinct flight numbers)', () => {
    const keys = threePairs.data.summary.codeshare_pairs.map((p) => `${p.cheaper.flight_number}-${p.pricier.flight_number}`);
    assert.equal(new Set(keys).size, 3);
    const html = render({ state: threePairs, search: kixFeb });
    assert.match(html, /JL5103 Japan Airlines/);
    assert.match(html, /TeaFlight/);
});
