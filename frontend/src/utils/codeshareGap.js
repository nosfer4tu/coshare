// Shared by CodeShareCard (render) and ResultsPage (sort order) so both
// agree on what counts as a "real" price gap vs. a tied codeshare pair.
//
// A group can hold several fare tiers per seller, so the comparison is between
// each seller's cheapest offer (seller = 'Owner Airline'), not the raw extremes.
export function getPriceExtremes(offers) {
    const cheapestBySeller = new Map();
    for (const offer of offers) {
        const best = cheapestBySeller.get(offer["Owner Airline"]);
        if (!best || offer["Total Amount"] < best["Total Amount"]) {
            cheapestBySeller.set(offer["Owner Airline"], offer);
        }
    }
    const sorted = [...cheapestBySeller.values()].sort((a, b) => a["Total Amount"] - b["Total Amount"]);
    const cheapestOffer = sorted[0];
    const mostExpensiveOffer = sorted[sorted.length - 1];
    const priceGap = mostExpensiveOffer["Total Amount"] - cheapestOffer["Total Amount"];
    return { cheapestOffer, mostExpensiveOffer, priceGap };
}

export function hasRealGap(offers) {
    return getPriceExtremes(offers).priceGap > 0;
}
