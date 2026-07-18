// Duffel's API returns no consumer booking URLs (bookings go through Duffel's
// Orders API, which this project doesn't use), so official airline links are
// maintained here as a static lookup instead. Prefers each airline's Japanese
// site where one exists, otherwise the global homepage.
// Manually curated 2026-07 — verify periodically for staleness.
const airlineBookingUrls = {
    CI: 'https://www.china-airlines.com/jp/jp',      // China Airlines
    JL: 'https://www.jal.co.jp',                      // JAL
    NH: 'https://www.ana.co.jp',                       // ANA
    BR: 'https://www.evaair.com/ja-jp/',                // EVA Air
    KE: 'https://www.koreanair.com/jp/ja',              // Korean Air
    OZ: 'https://flyasiana.com/C/JP/JA/index',          // Asiana Airlines
    CX: 'https://www.cathaypacific.com/cx/ja_JP.html',  // Cathay Pacific
    TG: 'https://www.thaiairways.com/ja_JP/index.page', // Thai Airways
    SQ: 'https://www.singaporeair.com/ja_JP/jp/home',   // Singapore Airlines
    UA: 'https://www.united.com/ja/jp',                 // United Airlines
    AA: 'https://www.aa.com',                           // American Airlines
    MU: 'https://jp.ceair.com',                         // China Eastern
    '7C': 'https://www.jejuair.net/jp/index.do',        // Jeju Air
};

export default airlineBookingUrls;
