// Renders the banner to static HTML through Vite's SSR loader (no DOM, no extra dependency).
import { test, before, after } from 'node:test';
import assert from 'node:assert/strict';
import { createServer } from 'vite';
import { createElement } from 'react';
import { renderToStaticMarkup } from 'react-dom/server';

let server;
let render;

before(async () => {
    server = await createServer({ server: { middlewareMode: true }, appType: 'custom', logLevel: 'silent' });
    const mod = await server.ssrLoadModule('/src/components/common/SnapshotNotice.jsx');
    render = (props) => renderToStaticMarkup(createElement(mod.default, props));
});

after(async () => {
    await server.close();
});

test('shows the saved-data banner with the capture date', () => {
    const html = render({ capturedAt: '2026-11-23T05:55:02Z' });
    assert.match(html, /保存済みのDuffelテストデータを表示しています\(取得日 2026-11-23\)/);
    assert.match(html, /role="status"/);
});

test('renders nothing when captured_at is missing or invalid', () => {
    assert.equal(render({ capturedAt: undefined }), '');
    assert.equal(render({ capturedAt: 'not a date' }), '');
});
