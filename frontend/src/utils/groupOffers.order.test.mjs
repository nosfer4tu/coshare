// Display order of the cards returned by groupOffers: gapped groups (largest gap first, equal gaps
// in arrival order), then tied groups, then single offers. Pairing itself is covered in
// groupOffers.test.mjs.
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { groupOffers } from './groupOffers.js';
import { getPriceExtremes } from './codeshareGap.js';

function offer(id, overrides = {}) {
    return {
        "Offer ID": id,
        "Owner Airline": "China Airlines",
        "Owner Airline IATA": "CI",
        "Operating IATA": "CI",
        "Total Amount": 30000,
        "Currency": "JPY",
        "Departure Time": "2027-03-01T09:00:00",
        "Segment Count": 1,
        "is Codeshare": false,
        ...overrides,
    };
}

// Two sellers of one flight (distinct departure time `at`); `gap` is the price difference.
function gapped(name, at, gap) {
    return [
        offer(`${name}-low`, { "Departure Time": at }),
        offer(`${name}-high`, { "Departure Time": at, "Owner Airline": "Japan Airlines", "Owner Airline IATA": "JL", "Total Amount": 30000 + gap, "is Codeshare": true }),
    ];
}

const ids = (groups) => groups.map((group) => group.map((o) => o["Offer ID"]));
const firstIds = (groups) => groups.map((group) => group[0]["Offer ID"].split("-")[0]);

test('three gapped groups arriving in mixed order come out biggest gap first', () => {
    const offers = [
        ...gapped("small", "T1", 5000),
        ...gapped("big", "T2", 20000),
        ...gapped("mid", "T3", 10000),
    ];
    for (const mode of ["both", "codeshare"]) {
        assert.deepEqual(firstIds(groupOffers(offers, mode)), ["big", "mid", "small"], mode);
    }
});

test('groups with equal gaps keep the order they arrived in', () => {
    const offers = [
        ...gapped("a", "T1", 3000),
        ...gapped("b", "T2", 9000),
        ...gapped("c", "T3", 3000),
        ...gapped("d", "T4", 9000),
        ...gapped("e", "T5", 3000),
    ];
    assert.deepEqual(firstIds(groupOffers(offers, "both")), ["b", "d", "a", "c", "e"]);
    // Reversing the input reverses the ties, which shows the original order is what decides.
    assert.deepEqual(firstIds(groupOffers([...offers].reverse(), "both")), ["d", "b", "e", "c", "a"]);
});

test('tied groups and single offers still come last, after every gapped group', () => {
    const tied = [
        offer("tied-1", { "Departure Time": "T9" }),
        offer("tied-2", { "Departure Time": "T9", "Owner Airline": "Mandarin Airlines", "Owner Airline IATA": "AE" }),
    ];
    const single = offer("single-1", { "Departure Time": "T8", "is Codeshare": true });
    const offers = [single, ...tied, ...gapped("small", "T1", 4000), ...gapped("big", "T2", 40000)];
    assert.deepEqual(ids(groupOffers(offers, "codeshare")), [
        ["big-low", "big-high"], ["small-low", "small-high"], ["tied-1", "tied-2"], ["single-1"],
    ]);
});

test('both mode: sorted gapped groups, tied groups, single offers, then connecting offers', () => {
    const connecting = offer("conn-1", { "Departure Time": "T7", "Segment Count": 2 });
    const single = offer("single-1", { "Departure Time": "T8" });
    const offers = [connecting, single, ...gapped("small", "T1", 4000), ...gapped("big", "T2", 40000)];
    assert.deepEqual(ids(groupOffers(offers, "both")), [
        ["big-low", "big-high"], ["small-low", "small-high"], ["single-1"], ["conn-1"],
    ]);
});

test('the gap that orders a group is the one the card shows: cheapest offer per seller', () => {
    // First group: CI sells 30,000 and a 80,000 fare tier, JL sells 40,000 -> gap 10,000
    // (the raw min-max spread of 50,000 must not decide the order).
    const tiers = [
        offer("tiers-ci", { "Departure Time": "T1" }),
        offer("tiers-ci-flex", { "Departure Time": "T1", "Total Amount": 80000 }),
        offer("tiers-jl", { "Departure Time": "T1", "Owner Airline": "Japan Airlines", "Owner Airline IATA": "JL", "Total Amount": 40000, "is Codeshare": true }),
    ];
    const wider = gapped("wider", "T2", 15000);
    const result = groupOffers([...tiers, ...wider], "both");
    assert.deepEqual(result.map((group) => getPriceExtremes(group).priceGap), [15000, 10000]);
    assert.deepEqual(firstIds(result), ["wider", "tiers"]);
});

test('ordering changes neither the membership nor the offer order inside a group, and does not mutate the input', () => {
    const offers = [...gapped("small", "T1", 5000), ...gapped("big", "T2", 20000)];
    const snapshot = offers.map((o) => o["Offer ID"]);
    const result = groupOffers(offers, "both");
    assert.deepEqual(ids(result), [["big-low", "big-high"], ["small-low", "small-high"]]);
    assert.deepEqual(offers.map((o) => o["Offer ID"]), snapshot);
});

test('a single gapped group, and no gapped groups at all, are unchanged', () => {
    assert.deepEqual(ids(groupOffers(gapped("only", "T1", 7000), "both")), [["only-low", "only-high"]]);
    const single = offer("s", { "Departure Time": "T1" });
    assert.deepEqual(ids(groupOffers([single], "both")), [["s"]]);
    assert.deepEqual(groupOffers([], "both"), []);
});
