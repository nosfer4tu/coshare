function FlightCard({offer}){
    return(
        <>
            <div>
                {offer["Owner Airline IATA"] !== offer["Operating IATA"] ? 
                    <p>{offer["Owner Airline"]} が発券 / {offer["Operating Carrier"]} が運航</p> 
                    : offer["Operating Carrier"] !== offer["Marketing Carrier"] ? 
                    <p>運航: {offer["Operating Carrier"]} / 販売: {offer["Marketing Carrier"]}</p> :
                    <p>{offer["Operating Carrier"]}</p>}
                <p>{offer["Total Amount"].toLocaleString('ja-JP', {style: 'currency', currency: 'JPY'})}</p>
                <p>{new Date (offer["Departure Time"]).toLocaleString('ja-JP')}</p>
                <p>{new Date(offer["Arrival Time"]).toLocaleString('ja-JP')}</p>
                {offer["is Codeshare"] && <span>コードシェア便</span> }   
            </div>
        </>
    )
}

export default FlightCard;