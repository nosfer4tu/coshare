import { test } from 'node:test';
import assert from 'node:assert/strict';
import { groupOffers } from './groupOffers.js';

function offer(id, overrides = {}) {
    return {
        "Offer ID": id,
        "Owner Airline": "China Airlines",
        "Owner Airline IATA": "CI",
        "Operating Carrier": "China Airlines",
        "Operating IATA": "CI",
        "Marketing Carrier": "China Airlines",
        "Total Amount": 32000,
        "Currency": "JPY",
        "Departure Time": "2027-03-01T09:00:00",
        "First Departure Time": "2027-03-01T09:00:00",
        "Segment Count": 1,
        "is Codeshare": false,
        ...overrides,
    };
}

const ids = (groups) => groups.map((group) => group.map((o) => o["Offer ID"]));

test('two nonstop sellers of one flight pair', () => {
    const ci = offer("ci");
    const jl = offer("jl", { "Owner Airline": "Japan Airlines", "Owner Airline IATA": "JL", "Total Amount": 35000, "is Codeshare": true });
    assert.deepEqual(ids(groupOffers([ci, jl], "both")), [["ci", "jl"]]);
    assert.deepEqual(ids(groupOffers([ci, jl], "codeshare")), [["ci", "jl"]]);
});

test('connecting itineraries with different first legs and the same last leg do not pair', () => {
    const lastLeg = { "Departure Time": "2027-03-01T18:00:00", "Operating IATA": "CI", "Segment Count": 2 };
    const a = offer("a", { ...lastLeg, "First Departure Time": "2027-03-01T08:00:00", "Owner Airline IATA": "VJ" });
    const b = offer("b", { ...lastLeg, "First Departure Time": "2027-03-01T10:30:00", "Owner Airline IATA": "TR", "Total Amount": 30000 });
    assert.deepEqual(ids(groupOffers([a, b], "both")), [["a"], ["b"]]);
});

test('a connecting offer does not join a nonstop group sharing its key', () => {
    const nonstopCi = offer("ci");
    const nonstopJl = offer("jl", { "Owner Airline IATA": "JL", "Total Amount": 35000 });
    const connecting = offer("c", { "Segment Count": 2, "First Departure Time": "2027-03-01T05:00:00" });
    assert.deepEqual(ids(groupOffers([nonstopCi, connecting, nonstopJl], "both")), [["ci", "jl"], ["c"]]);
});

test('codeshare mode excludes connecting offers', () => {
    const connecting = offer("c", { "Segment Count": 2, "is Codeshare": true });
    const nonstop = offer("n", { "Departure Time": "2027-03-01T12:00:00", "is Codeshare": true });
    assert.deepEqual(ids(groupOffers([connecting, nonstop], "codeshare")), [["n"]]);
    assert.deepEqual(ids(groupOffers([connecting], "codeshare")), []);
});

test('both mode renders each connecting offer as its own single card, after the nonstop groups', () => {
    const connecting1 = offer("c1", { "Segment Count": 2 });
    const connecting2 = offer("c2", { "Segment Count": 3, "Total Amount": 20000 });
    const solo = offer("solo", { "Departure Time": "2027-03-01T12:00:00" });
    const result = groupOffers([connecting1, connecting2, solo], "both");
    assert.deepEqual(ids(result), [["solo"], ["c1"], ["c2"]]);
    assert.ok(result.every((group) => group.length === 1));
});

test('offers without Segment Count group as before', () => {
    const strip = (o) => { const { ["Segment Count"]: _count, ["First Departure Time"]: _first, ...rest } = o; return rest; };
    const ci = strip(offer("ci"));
    const jl = strip(offer("jl", { "Owner Airline IATA": "JL", "Total Amount": 35000 }));
    assert.deepEqual(ids(groupOffers([ci, jl], "both")), [["ci", "jl"]]);
});

test('codeshare mode keeps a single nonstop offer only when is Codeshare is true; both mode keeps it', () => {
    const own = offer("own");
    const sold = offer("sold", { "Departure Time": "2027-03-01T12:00:00", "is Codeshare": true });
    assert.deepEqual(ids(groupOffers([own, sold], "codeshare")), [["sold"]]);
    assert.deepEqual(ids(groupOffers([own, sold], "both")), [["own"], ["sold"]]);
});

test('sort: gapped pairs, then tied pairs, then single offers', () => {
    const tied1 = offer("t1", { "Departure Time": "T1" });
    const tied2 = offer("t2", { "Departure Time": "T1", "Owner Airline": "Mandarin Airlines" });
    const single = offer("s", { "Departure Time": "T2" });
    const gap1 = offer("g1", { "Departure Time": "T3" });
    const gap2 = offer("g2", { "Departure Time": "T3", "Owner Airline": "Japan Airlines", "Total Amount": 36000 });
    assert.deepEqual(ids(groupOffers([tied1, tied2, single, gap1, gap2], "both")), [["g1", "g2"], ["t1", "t2"], ["s"]]);
});
