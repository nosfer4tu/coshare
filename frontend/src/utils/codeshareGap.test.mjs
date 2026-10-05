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

// Fixtures from KIX-TPE 2026-11-11 (economy, 1 adult): several fare tiers per seller.
const tier = (airline, iata, amount, departure) => ({
    "Offer ID": `off_${iata}_${departure}_${amount}`,
    "Owner Airline": airline,
    "Owner Airline IATA": iata,
    "Operating Carrier": "China Airlines",
    "Operating IATA": "CI",
    "Total Amount": amount,
    "Currency": "JPY",
    "Departure Time": departure
});
const ci = (amount, departure) => tier("China Airlines", "CI", amount, departure);
const jl = (amount, departure) => tier("Japan Airlines", "JL", amount, departure);

test("multi-tier group compares each seller's cheapest offer (12:45)", () => {
    const d = "2026-11-11T12:45:00";
    const group = [ci(74446, d), jl(222658, d), ci(62976, d), jl(98658, d), jl(91682, d)];
    const { cheapestOffer, mostExpensiveOffer, priceGap } = getPriceExtremes(group);
    assert.equal(cheapestOffer["Owner Airline"], "China Airlines");
    assert.equal(cheapestOffer["Total Amount"], 62976);
    assert.equal(mostExpensiveOffer["Owner Airline"], "Japan Airlines");
    assert.equal(mostExpensiveOffer["Total Amount"], 91682);
    assert.equal(priceGap, 28706);
    assert.equal(hasRealGap(group), true);
});

test("multi-tier group compares each seller's cheapest offer (19:00)", () => {
    const d = "2026-11-11T19:00:00";
    const group = [ci(77702, d), ci(89326, d), jl(118342, d), jl(124232, d), jl(222658, d)];
    const { cheapestOffer, mostExpensiveOffer, priceGap } = getPriceExtremes(group);
    assert.equal(cheapestOffer["Total Amount"], 77702);
    assert.equal(mostExpensiveOffer["Total Amount"], 118342);
    assert.equal(priceGap, 40640);
});

test('equal per-seller cheapest prices stay neutral even when higher tiers differ', () => {
    const d = "2026-11-11T09:00:00";
    const group = [ci(80000, d), ci(95000, d), jl(80000, d), jl(222658, d)];
    const { cheapestOffer, mostExpensiveOffer, priceGap } = getPriceExtremes(group);
    assert.equal(priceGap, 0);
    assert.notEqual(cheapestOffer["Owner Airline"], mostExpensiveOffer["Owner Airline"]);
    assert.equal(hasRealGap(group), false);
});
