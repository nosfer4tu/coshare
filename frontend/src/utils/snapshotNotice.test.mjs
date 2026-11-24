import { test } from 'node:test';
import assert from 'node:assert/strict';
import { snapshotDate, snapshotInfo, snapshotNoticeText } from './snapshotNotice.js';

test('snapshotDate: the UTC date of captured_at', () => {
    assert.equal(snapshotDate('2026-11-23T05:55:02Z'), '2026-11-23');
    assert.equal(snapshotDate('2026-11-04T07:44:01Z'), '2026-11-04');
});

test('snapshotDate: converts an offset to UTC, so the date is the UTC date', () => {
    assert.equal(snapshotDate('2026-11-24T02:00:00+09:00'), '2026-11-23');
    assert.equal(snapshotDate('2026-11-23T23:30:00-02:00'), '2026-11-24');
});

test('snapshotDate: null for anything that is not an ISO datetime string', () => {
    for (const bad of [undefined, null, '', 'yesterday', 12345, {}]) {
        assert.equal(snapshotDate(bad), null, String(bad));
    }
});

test('snapshotInfo: only a snapshot response yields info; live data yields null', () => {
    assert.deepEqual(snapshotInfo({ data: [], data_source: 'snapshot', captured_at: '2026-11-23T05:55:02Z' }),
        { capturedAt: '2026-11-23T05:55:02Z' });
    assert.equal(snapshotInfo({ data: [] }), null);
    assert.equal(snapshotInfo({ data: [], data_source: 'live' }), null);
    assert.equal(snapshotInfo(null), null);
    assert.equal(snapshotInfo(undefined), null);
});

test('snapshotNoticeText: the banner wording with the capture date', () => {
    assert.equal(snapshotNoticeText('2026-11-23T05:55:02Z'),
        '保存済みのDuffelテストデータを表示しています(取得日 2026-11-23)');
    assert.equal(snapshotNoticeText('nope'), null);
});
