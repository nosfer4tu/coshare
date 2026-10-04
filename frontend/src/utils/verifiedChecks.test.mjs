import { test } from 'node:test';
import assert from 'node:assert/strict';
import {
    CARD_SANDBOX_SOURCE,
    matchesCard,
    findBadgeCheck,
    priceDifferencePercent,
} from './verifiedChecks.js';

const card = { route: 'AAA-BBB', flightDate: '2026-03-04', carrierName: 'Example Airlines' };

const check = (overrides = {}) => ({
    id: 1,
    route: 'AAA-BBB',
    check_date: '2026-01-02',
    flight_date: '2026-03-04',
    carrier_checked: 'Example Airlines',
    sandbox_source: CARD_SANDBOX_SOURCE,
    sandbox_price_jpy: 10000,
    real_price_jpy: 10000,
    real_source_url: 'https://example.com/',
    verdict: 'match',
    notes: null,
    ...overrides,
});

test('matchesCard: exact route, date and carrier match', () => {
    assert.equal(matchesCard(check(), card), true);
});

test('matchesCard: carrier is trimmed and case-insensitive', () => {
    assert.equal(matchesCard(check({ carrier_checked: '  EXAMPLE airlines ' }), card), true);
    assert.equal(matchesCard(check(), { ...card, carrierName: ' example AIRLINES' }), true);
});

test('matchesCard: no fuzzy matching on the carrier name', () => {
    assert.equal(matchesCard(check({ carrier_checked: 'Example Air' }), card), false);
    assert.equal(matchesCard(check({ carrier_checked: 'Example Airlines Japan' }), card), false);
});

test('matchesCard: route and flight date must be equal', () => {
    assert.equal(matchesCard(check({ route: 'AAA-CCC' }), card), false);
    assert.equal(matchesCard(check({ flight_date: '2026-03-05' }), card), false);
});

test('matchesCard: empty or missing carrier never matches', () => {
    assert.equal(matchesCard(check({ carrier_checked: '' }), { ...card, carrierName: '' }), false);
    assert.equal(matchesCard(check(), { ...card, carrierName: undefined }), false);
    assert.equal(matchesCard(null, card), false);
});

test('findBadgeCheck: a matching check from the card source with verdict match gives a badge', () => {
    const c = check();
    assert.equal(findBadgeCheck([c], card), c);
});

test('findBadgeCheck: only the matching check yields a badge (one match, one mismatch)', () => {
    const matching = check({ id: 1 });
    const mismatching = check({ id: 2, carrier_checked: 'Other Airways', verdict: 'mismatch', sandbox_price_jpy: 15000 });
    const checks = [matching, mismatching];
    assert.equal(findBadgeCheck(checks, card), matching);
    assert.equal(findBadgeCheck(checks, { ...card, carrierName: 'Other Airways' }), null);
});

test('findBadgeCheck: no badge for mismatch or not_comparable verdicts', () => {
    assert.equal(findBadgeCheck([check({ verdict: 'mismatch' })], card), null);
    assert.equal(findBadgeCheck([check({ verdict: 'not_comparable' })], card), null);
});

test('findBadgeCheck: no badge when the check is from another price source', () => {
    assert.equal(findBadgeCheck([check({ sandbox_source: 'flightlabs' })], card), null);
});

test('findBadgeCheck: no badge for a different flight date', () => {
    assert.equal(findBadgeCheck([check({ flight_date: '2026-03-05' })], card), null);
});

test('findBadgeCheck: a newer non-match check suppresses an older match', () => {
    const older = check({ id: 1, check_date: '2026-01-02' });
    const newer = check({ id: 2, check_date: '2026-02-02', verdict: 'mismatch' });
    assert.equal(findBadgeCheck([older, newer], card), null);
    assert.equal(findBadgeCheck([newer, older], card), null);
});

test('findBadgeCheck: a newer match wins over an older mismatch', () => {
    const older = check({ id: 1, check_date: '2026-01-02', verdict: 'mismatch' });
    const newer = check({ id: 2, check_date: '2026-02-02' });
    assert.equal(findBadgeCheck([older, newer], card), newer);
});

test('findBadgeCheck: empty or missing list', () => {
    assert.equal(findBadgeCheck([], card), null);
    assert.equal(findBadgeCheck(undefined, card), null);
});

test('priceDifferencePercent: positive when the tool price is higher, rounded', () => {
    assert.equal(priceDifferencePercent(11000, 10000), 10);
    assert.equal(priceDifferencePercent(9000, 10000), -10);
    assert.equal(priceDifferencePercent(10000, 10000), 0);
    assert.equal(priceDifferencePercent(10333, 10000), 3);
});

test('priceDifferencePercent: null when a price is missing or real is 0', () => {
    assert.equal(priceDifferencePercent(null, 10000), null);
    assert.equal(priceDifferencePercent(10000, null), null);
    assert.equal(priceDifferencePercent(undefined, undefined), null);
    assert.equal(priceDifferencePercent(10000, 0), null);
});
