import { useId, useState } from 'react';
import './FlightDetails.css';

// Toggle + collapsible panel shared by FlightCard and CodeShareCard.
function FlightDetails({ children }) {
    const [isOpen, setIsOpen] = useState(false);
    const panelId = useId();

    return (
        <div className="flight-details">
            <button
                type="button"
                className="flight-details__toggle"
                aria-expanded={isOpen}
                aria-controls={panelId}
                onClick={() => setIsOpen((open) => !open)}
            >
                {isOpen ? '詳細を閉じる' : '詳細を見る'}
                <span className="flight-details__chevron" aria-hidden="true">{isOpen ? '▲' : '▼'}</span>
            </button>
            <dl id={panelId} className="flight-details__panel" hidden={!isOpen}>
                {children}
            </dl>
        </div>
    );
}

// One label/value line; renders nothing when the value is absent.
export function DetailRow({ label, value }) {
    if (!value) return null;
    return (
        <div className="flight-details__row">
            <dt>{label}</dt>
            <dd>{value}</dd>
        </div>
    );
}

export default FlightDetails;
