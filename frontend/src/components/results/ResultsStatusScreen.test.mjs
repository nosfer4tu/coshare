// Empty and error screens with the real-prices panel, rendered to static HTML via Vite's SSR
// loader (see RealPricesPanel.test.mjs). The Link inside the status messages needs a router.
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
const found = {
    status: 'found',
    data: {
        found: true, flight_date: '2026-12-03', captured_on: '2026-10-19', source: 'Skyscanner(手動確認)',
        entries: [lcc], summary: { cheapest_lcc: lcc, cheapest_full_service: null, codeshare_pairs: [] },
    },
};

let server;
let renderScreen;
let renderEmptyScreen;
let renderPage;

before(async () => {
    server = await createServer({ server: { middlewareMode: true }, appType: 'custom', logLevel: 'silent' });
    const { default: ResultsStatusScreen, EmptyResultsScreen } = await server.ssrLoadModule('/src/components/results/ResultsStatusScreen.jsx');
    const { EmptyMessage, ErrorMessage } = await server.ssrLoadModule('/src/components/common/StatusMessage.jsx');
    const { default: ResultsPage } = await server.ssrLoadModule('/src/pages/ResultsPage.jsx');
    // Native import: the same instance Vite's SSR loader externalizes for the components.
    const { MemoryRouter } = await import('react-router-dom');

    renderScreen = (kind, realPrices) => renderToStaticMarkup(
        createElement(MemoryRouter, null,
            createElement(ResultsStatusScreen, { realPrices },
                kind === 'empty'
                    ? createElement(EmptyMessage)
                    : createElement(ErrorMessage, { message: 'Request failed: 500' }))));
    renderEmptyScreen = (realPrices) => renderToStaticMarkup(
        createElement(MemoryRouter, null, createElement(EmptyResultsScreen, { realPrices })));
    renderPage = (url) => renderToStaticMarkup(
        createElement(MemoryRouter, { initialEntries: [url] }, createElement(ResultsPage)));
});

after(async () => {
    await server.close();
});

test('empty screen: status message, then the panel with the data', () => {
    const html = renderScreen('empty', { state: found, search });
    assert.match(html, /status-message--empty/);
    assert.match(html, /結果が見つかりませんでした/);
    assert.match(html, /実測価格との比較/);
    assert.match(html, /Jetstar Japan/);
    assert.ok(html.indexOf('status-message--empty') < html.indexOf('実測価格との比較'), 'panel is below the message');
});

test('error screen: error message, then the panel with the data', () => {
    const html = renderScreen('error', { state: found, search });
    assert.match(html, /status-message--error/);
    assert.match(html, /Request failed: 500/);
    assert.match(html, /実測価格との比較/);
    assert.match(html, /Jetstar Japan/);
    assert.ok(html.indexOf('status-message--error') < html.indexOf('実測価格との比較'));
});

test('empty and error screens: notFound and noData show the muted line and the Skyscanner link', () => {
    for (const kind of ['empty', 'error']) {
        for (const status of ['notFound', 'noData']) {
            const html = renderScreen(kind, { state: { status }, search });
            assert.match(html, /この路線・日付の実測データはまだありません/, `${kind}/${status}`);
            assert.match(html, /skyscanner\.jp\/transport\/flights\/kix\/tpe\/261203\//, `${kind}/${status}`);
        }
    }
});

test('empty and error screens: hidden (400), loading and invalid search render the message only, no blank slot', () => {
    for (const kind of ['empty', 'error']) {
        for (const realPrices of [
            { state: { status: 'hidden' }, search },
            { state: { status: 'loading' }, search },
            { state: { status: 'hidden' }, search: null },
        ]) {
            const html = renderScreen(kind, realPrices);
            assert.match(html, kind === 'empty' ? /status-message--empty/ : /status-message--error/);
            assert.doesNotMatch(html, /実測価格との比較|実測データ|real-prices/, `${kind}/${realPrices.state.status}`);
        }
    }
});

test('loading screen of ResultsPage (initial render) shows the skeleton and no panel', () => {
    const html = renderPage('/results?origin=KIX&destination=TPE&departureDate=2026-12-03&passengers=adult&cabinClass=economy&mode=codeshare');
    assert.match(html, /skeleton/);
    assert.doesNotMatch(html, /実測価格との比較|実測データ|real-prices/);
});

const FOUND_SUBLINE = 'テスト環境にこの路線・日付のデータがありません。下の実測価格を参考にしてください。';
const DEFAULT_SUBLINE = '別の路線や日付で試してみてください';

test('EmptyResultsScreen, found: same title, new subline, panel below', () => {
    const html = renderEmptyScreen({ state: found, search });
    assert.match(html, /結果が見つかりませんでした/);
    assert.ok(html.includes(FOUND_SUBLINE), 'found subline');
    assert.ok(!html.includes(DEFAULT_SUBLINE), 'default subline is replaced');
    assert.match(html, /実測価格との比較/);
});

test('EmptyResultsScreen, not found / no data / hidden / loading: title and default subline unchanged', () => {
    for (const status of ['notFound', 'noData', 'hidden', 'loading']) {
        const html = renderEmptyScreen({ state: { status }, search });
        assert.match(html, /結果が見つかりませんでした/, status);
        assert.ok(html.includes(DEFAULT_SUBLINE), `${status}: default subline`);
        assert.ok(!html.includes(FOUND_SUBLINE), `${status}: no found subline`);
    }
});

test('error screen keeps its message in the found state (copy change is empty-screen only)', () => {
    const html = renderScreen('error', { state: found, search });
    assert.match(html, /Request failed: 500/);
    assert.ok(!html.includes(FOUND_SUBLINE));
});
