import { hasRealGap } from "./codeshareGap.js";

// "Same flight, different seller" is only well defined for nonstop offers. On a connection
// 'Departure Time' / 'Operating IATA' describe the LAST leg, so two unrelated itineraries
// can share that key. Offers without 'Segment Count' (older search_cache rows) are treated
// as nonstop and group as before.
function isConnecting(offer) {
    return offer["Segment Count"] > 1;
}

// Returns the groups to render, in display order. A group of 2+ offers is a codeshare group
// (CodeShareCard); a group of 1 is a FlightCard.
//   codeshare mode: connecting offers are dropped, and a single nonstop offer is kept only
//                   if 'is Codeshare' is true.
//   both mode:      each connecting offer is its own single-offer group.
// Order: codeshare groups with a real gap, tied codeshare groups, then single offers.
export function groupOffers(offers, mode) {
    const connecting = offers.filter(isConnecting);
    const grouped = offers.filter((offer) => !isConnecting(offer)).reduce((groups, offer) => {
        const key = `${offer["Departure Time"]}_${offer["Operating IATA"]}`;
        if (!groups[key]) groups[key] = [];
        groups[key].push(offer);
        return groups;
    }, {});
    const codeshareGroups = Object.values(grouped).filter((group) => group.length > 1);
    const regularGroups = Object.values(grouped).filter((group) => group.length === 1);
    const gappedCodeshareGroups = codeshareGroups.filter((group) => hasRealGap(group));
    const zeroGapCodeshareGroups = codeshareGroups.filter((group) => !hasRealGap(group));
    const connectingGroups = mode === "codeshare" ? [] : connecting.map((offer) => [offer]);
    return [...gappedCodeshareGroups, ...zeroGapCodeshareGroups, ...regularGroups, ...connectingGroups]
        .filter((group) => !(mode === "codeshare" && group.length === 1 && !group[0]["is Codeshare"]));
}
