function CodeShareCard({offers}){
    const cheapestOffer = offers.find(offer => offer["Total Amount"] === Math.min(...offers.map(o => o["Total Amount"])));
    const mostExpensiveOffer = offers.find(offer => offer["Total Amount"] === Math.max(...offers.map(o => o["Total Amount"])));
    const priceGap = mostExpensiveOffer["Total Amount"] - cheapestOffer["Total Amount"];
    if (priceGap === 0) return null;
    if (cheapestOffer["Owner Airline"] === mostExpensiveOffer["Owner Airline"]) return null;
    return(
        <>
            <section>
                <h1>同一便・コードシェア価格比較</h1>  
                <p>{cheapestOffer["Operating Carrier"]} 運航 • {new Date(cheapestOffer["Departure Time"]).toLocaleString('ja-JP')}</p>              
            </section>
            
            <div>
                <p>お得: {cheapestOffer["Owner Airline"]} — {cheapestOffer["Total Amount"].toLocaleString('ja-JP', { style: 'currency', currency: 'JPY' })}</p>
                <p>割高: {mostExpensiveOffer["Owner Airline"]} — {mostExpensiveOffer["Total Amount"].toLocaleString('ja-JP', { style: 'currency', currency: 'JPY' })}</p>
            </div>
            <p>価格差: {priceGap.toLocaleString('ja-JP', {style: 'currency', currency: 'JPY'})}</p>
        </>
    )
}
export default CodeShareCard;