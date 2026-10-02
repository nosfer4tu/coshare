import './CodeShareCard.css'
import airlineBookingUrls from '../../constants/airlineBookingUrls';
import { getPriceExtremes } from '../../utils/codeshareGap';

function CodeShareCard({offers}){
    const { cheapestOffer, mostExpensiveOffer, priceGap } = getPriceExtremes(offers);
    const hasGap = priceGap > 0;
    if (cheapestOffer["Owner Airline"] === mostExpensiveOffer["Owner Airline"]) return null;

    const cheapestUrl = airlineBookingUrls[cheapestOffer["Owner Airline IATA"]];
    const expensiveUrl = airlineBookingUrls[mostExpensiveOffer["Owner Airline IATA"]];

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
                    <span className="codeshare-card__airline">{hasGap && '✓ '}{cheapestOffer["Owner Airline"]}</span>
                    <span className={`codeshare-card__price ${hasGap ? 'codeshare-card__price--cheap' : 'codeshare-card__price--equal'}`}>
                        {cheapestOffer["Total Amount"].toLocaleString('ja-JP', { style: 'currency', currency: 'JPY' })}
                    </span>
                </div>
                <div className="codeshare-card__row">
                    <span className="codeshare-card__airline">{mostExpensiveOffer["Owner Airline"]}</span>
                    <span className={`codeshare-card__price ${hasGap ? 'codeshare-card__price--expensive' : 'codeshare-card__price--equal'}`}>
                        {mostExpensiveOffer["Total Amount"].toLocaleString('ja-JP', { style: 'currency', currency: 'JPY' })}
                    </span>
                </div>
            </div>
            {hasGap ? (
                <div className="codeshare-card__gap">
                    <span className="codeshare-card__gap-label">価格差</span>
                    <span className="codeshare-card__gap-amount">
                        {priceGap.toLocaleString('ja-JP', { style: 'currency', currency: 'JPY' })} お得
                    </span>
                </div>
            ) : (
                <div className="codeshare-card__gap codeshare-card__gap--neutral">
                    <span className="codeshare-card__gap-label">コードシェア間の価格差はありません</span>
                </div>
            )}
            {(cheapestUrl || expensiveUrl) && (
                <div className="codeshare-card__booking">
                    <span className="codeshare-card__booking-label">どこで購入する?</span>
                    <div className="codeshare-card__booking-links">
                        {cheapestUrl && (
                            <a
                                className="codeshare-card__booking-primary"
                                href={cheapestUrl}
                                target="_blank"
                                rel="noopener noreferrer"
                            >
                                {cheapestOffer["Owner Airline"]}公式サイトへ ↗
                            </a>
                        )}
                        {expensiveUrl && (
                            <a
                                className="codeshare-card__booking-secondary"
                                href={expensiveUrl}
                                target="_blank"
                                rel="noopener noreferrer"
                            >
                                {mostExpensiveOffer["Owner Airline"]}公式サイト ↗
                            </a>
                        )}
                    </div>
                    <div className="codeshare-card__explanation">
                        <span className="codeshare-card__explanation-icon">ℹ️</span>
                        <p className="codeshare-card__explanation-text">
                            この便は{cheapestOffer["Operating Carrier"]}が運航していますが、
                            {cheapestOffer["Owner Airline"]}と{mostExpensiveOffer["Owner Airline"]}が
                            それぞれ独自に発券・販売しています（コードシェア便）。
                        </p>
                    </div>
                    <span className="codeshare-card__booking-caption">
                        公式サイトで同じ便を検索してください
                    </span>
                </div>
            )}
        </div>

    )
}
export default CodeShareCard;