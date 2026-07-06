import './CodeShareCard.css'

function CodeShareCard({offers}){
    const cheapestOffer = offers.find(offer => offer["Total Amount"] === Math.min(...offers.map(o => o["Total Amount"])));
    const mostExpensiveOffer = offers.find(offer => offer["Total Amount"] === Math.max(...offers.map(o => o["Total Amount"])));
    const priceGap = mostExpensiveOffer["Total Amount"] - cheapestOffer["Total Amount"];
    if (priceGap === 0) return null;
    if (cheapestOffer["Owner Airline"] === mostExpensiveOffer["Owner Airline"]) return null;
    
    return(
        <div className="codeshare-card">
            <div className="codeshare-card__header">
                <span className="codeshare-card__title">同一便・コードシェア価格比較</span>
                <span className="codeshare-card__flight-info">
                    {cheapestOffer["Operating Carrier"]} 運航 • {new Date(cheapestOffer["Departure Time"]).toLocaleString('ja-JP')}
                </span>
            </div>
            <div className="codeshare-card__comparison">
                <div className="codeshare-card__row">
                    <span className="codeshare-card__airline">✓ {cheapestOffer["Owner Airline"]}</span>
                    <span className="codeshare-card__price codeshare-card__price--cheap">
                        {cheapestOffer["Total Amount"].toLocaleString('ja-JP', { style: 'currency', currency: 'JPY' })}
                    </span>
                </div>
                <div className="codeshare-card__row">
                    <span className="codeshare-card__airline">{mostExpensiveOffer["Owner Airline"]}</span>
                    <span className="codeshare-card__price codeshare-card__price--expensive">
                        {mostExpensiveOffer["Total Amount"].toLocaleString('ja-JP', { style: 'currency', currency: 'JPY' })}
                    </span>
                </div>
            </div>
            <div className="codeshare-card__gap">
                <span className="codeshare-card__gap-label">価格差</span>
                <span className="codeshare-card__gap-amount">
                    {priceGap.toLocaleString('ja-JP', { style: 'currency', currency: 'JPY' })} お得
                </span>
            </div>
        </div>
    )
}
export default CodeShareCard;