import { test } from 'node:test';
import assert from 'node:assert/strict';
import { displayDeparture, connectionLabel, connectionAirline, showCodeshareBadge } from './flightDetails.js';

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

test('connectionAirline is the display carrier name with no operator clause', () => {
    const offer = {
        "Segment Count": 2,
        "Owner Airline": "China Airlines",
        "Owner Airline IATA": "CI",
        "Operating Carrier": "EVA Air",
        "Operating IATA": "BR",
        "Marketing Carrier": "EVA Air",
    };
    assert.equal(connectionAirline(offer), "China Airlines");
    assert.ok(!connectionAirline(offer).includes("運航"));
    assert.ok(!connectionAirline(offer).includes("EVA Air"));
});

test('connectionAirline is null for direct offers and older cache rows', () => {
    assert.equal(connectionAirline({ "Segment Count": 1, "Owner Airline": "China Airlines" }), null);
    assert.equal(connectionAirline({ "Owner Airline": "China Airlines" }), null);
});

test('showCodeshareBadge is hidden on connecting offers even when the key is true', () => {
    assert.equal(showCodeshareBadge({ "Segment Count": 2, "is Marketing Codeshare": true }), false);
    assert.equal(showCodeshareBadge({ "Segment Count": 3, "is Marketing Codeshare": true }), false);
});

test('showCodeshareBadge still follows is Marketing Codeshare on direct offers', () => {
    assert.equal(showCodeshareBadge({ "Segment Count": 1, "is Marketing Codeshare": true }), true);
    assert.equal(showCodeshareBadge({ "Segment Count": 1, "is Marketing Codeshare": false }), false);
    assert.equal(showCodeshareBadge({ "is Marketing Codeshare": true }), true);
    assert.equal(showCodeshareBadge({ "Segment Count": 1 }), false);
});
