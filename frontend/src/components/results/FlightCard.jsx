import "./FlightCard.css"
import FlightDetails, { DetailRow } from "./FlightDetails";
import { hasDetails, formatFlightNumber, formatPoint, displayDeparture, connectionLabel, connectionAirline, showCodeshareBadge } from "../../utils/flightDetails";
import VerifiedBadge from "./VerifiedBadge";
function FlightCard({offer, getVerifiedCheck}){
    const connection = connectionLabel(offer);
    return(
        <div className="flight-card">
            <div className="flight-card__summary">
                <div className="flight-card__airline">
                    {connection ?
                        <p>{connectionAirline(offer)} <span className="flight-card__connection">{connection}</span></p>
                        : offer["Owner Airline IATA"] !== offer["Operating IATA"] ?
                        <p>{offer["Owner Airline"]} が発券 / {offer["Operating Carrier"]} が運航</p>
                        : offer["Operating Carrier"] !== offer["Marketing Carrier"] ?
                        <p>運航: {offer["Operating Carrier"]} / 販売: {offer["Marketing Carrier"]}</p> :
                        <p>{offer["Operating Carrier"]}</p>}
                    <VerifiedBadge check={getVerifiedCheck?.(offer["Owner Airline"], offer["Total Amount"])} />
                </div>
                <div className="flight-card__times">
                    <span>{new Date(displayDeparture(offer)).toLocaleString('ja-JP')}</span>
                    <span>→</span>
                    <span>{new Date(offer["Arrival Time"]).toLocaleString('ja-JP')}</span>
                </div>
                <p className="flight-card__price">
                    {offer["Total Amount"].toLocaleString('ja-JP', {style: 'currency', currency: 'JPY'})}
                </p>
                {showCodeshareBadge(offer) &&
                    <span className="flight-card__codeshare-badge">コードシェア便</span>
                }
            </div>
            {hasDetails(offer) && (
                <FlightDetails>
                    <DetailRow label="出発" value={formatPoint(offer["Departure Airport"], displayDeparture(offer))} />
                    <DetailRow label="到着" value={formatPoint(offer["Arrival Airport"], offer["Arrival Time"])} />
                    <DetailRow label="販売便名" value={formatFlightNumber(offer["Marketing IATA"], offer["Marketing Flight Number"], offer["Marketing Carrier"])} />
                    <DetailRow label="運航便名" value={formatFlightNumber(offer["Operating IATA"], offer["Operating Flight Number"], offer["Operating Carrier"])} />
                </FlightDetails>
            )}
        </div>
    )
}

export default FlightCard;
