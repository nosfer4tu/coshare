import "./FlightCard.css"
function FlightCard({offer}){
    return(
        <div className="flight-card">
            <div className="flight-card__airline">
                {offer["Owner Airline IATA"] !== offer["Operating IATA"] ? 
                    <p>{offer["Owner Airline"]} が発券 / {offer["Operating Carrier"]} が運航</p> 
                    : offer["Operating Carrier"] !== offer["Marketing Carrier"] ? 
                    <p>運航: {offer["Operating Carrier"]} / 販売: {offer["Marketing Carrier"]}</p> :
                    <p>{offer["Operating Carrier"]}</p>}
            </div>
            <div className="flight-card__times">
                <span>{new Date(offer["Departure Time"]).toLocaleString('ja-JP')}</span>
                <span>→</span>
                <span>{new Date(offer["Arrival Time"]).toLocaleString('ja-JP')}</span>
            </div>
            <p className="flight-card__price">
                {offer["Total Amount"].toLocaleString('ja-JP', {style: 'currency', currency: 'JPY'})}
            </p>
            {offer["is Codeshare"] && 
                <span className="flight-card__codeshare-badge">コードシェア便</span>
            }   
        </div>
    )
}

export default FlightCard;