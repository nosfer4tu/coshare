// Shared by CodeShareCard (render) and ResultsPage (sort order) so both
// agree on what counts as a "real" price gap vs. a tied codeshare pair.
export function getPriceExtremes(offers) {
    const sorted = [...offers].sort((a, b) => a["Total Amount"] - b["Total Amount"]);
    const cheapestOffer = sorted[0];
    const mostExpensiveOffer = sorted[sorted.length - 1];
    const priceGap = mostExpensiveOffer["Total Amount"] - cheapestOffer["Total Amount"];
    return { cheapestOffer, mostExpensiveOffer, priceGap };
}

export function hasRealGap(offers) {
    return getPriceExtremes(offers).priceGap > 0;
}
