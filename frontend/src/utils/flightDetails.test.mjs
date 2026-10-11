import { test } from 'node:test';
import assert from 'node:assert/strict';
import { displayDeparture, connectionLabel } from './flightDetails.js';

test('displayDeparture prefers First Departure Time', () => {
    const offer = { "First Departure Time": "2026-12-02T10:40:00", "Departure Time": "2026-12-02T22:00:00" };
    assert.equal(displayDeparture(offer), "2026-12-02T10:40:00");
});

test('displayDeparture falls back to Departure Time when the key is missing', () => {
    assert.equal(displayDeparture({ "Departure Time": "2026-12-02T22:00:00" }), "2026-12-02T22:00:00");
});

test('displayDeparture falls back when First Departure Time is null', () => {
    const offer = { "First Departure Time": null, "Departure Time": "2026-12-02T22:00:00" };
    assert.equal(displayDeparture(offer), "2026-12-02T22:00:00");
});

test('connectionLabel counts connections from Segment Count', () => {
    assert.equal(connectionLabel({ "Segment Count": 2 }), "乗り継ぎ1回");
    assert.equal(connectionLabel({ "Segment Count": 3 }), "乗り継ぎ2回");
});

test('connectionLabel is null for direct offers and older cache rows', () => {
    assert.equal(connectionLabel({ "Segment Count": 1 }), null);
    assert.equal(connectionLabel({}), null);
});
