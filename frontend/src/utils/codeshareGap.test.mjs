import { test } from 'node:test';
import assert from 'node:assert/strict';
import { getPriceExtremes, hasRealGap } from './codeshareGap.js';

const equalPriceOffers = [
    {
        "Offer ID": "off_1",
        "Owner Airline": "China Airlines",
        "Owner Airline IATA": "CI",
        "Operating Carrier": "China Airlines",
        "Operating IATA": "CI",
        "Marketing Carrier": "China Airlines",
        "Total Amount": 32000,
        "Currency": "JPY",
        "Departure Time": "2027-03-01T09:00:00"
    },
    {
        "Offer ID": "off_2",
        "Owner Airline": "Mandarin Airlines",
        "Owner Airline IATA": "AE",
        "Operating Carrier": "China Airlines",
        "Operating IATA": "CI",
        "Marketing Carrier": "Mandarin Airlines",
        "Total Amount": 32000,
        "Currency": "JPY",
        "Departure Time": "2027-03-01T09:00:00"
    }
];

const gappedOffers = [
    { ...equalPriceOffers[0], "Total Amount": 32000 },
    { ...equalPriceOffers[1], "Total Amount": 41000 }
];

test('equal-price codeshare pair reports no real gap but keeps both distinct carriers', () => {
    const { cheapestOffer, mostExpensiveOffer, priceGap } = getPriceExtremes(equalPriceOffers);
    assert.equal(priceGap, 0);
    assert.notEqual(cheapestOffer["Owner Airline"], mostExpensiveOffer["Owner Airline"]);
    assert.equal(hasRealGap(equalPriceOffers), false);
});

test('gapped codeshare pair reports a real, positive gap', () => {
    const { priceGap } = getPriceExtremes(gappedOffers);
    assert.equal(priceGap, 9000);
    assert.equal(hasRealGap(gappedOffers), true);
});
