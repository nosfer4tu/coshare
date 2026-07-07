import { useState, useEffect, useRef } from 'react';
import './AirportInput.css';

function AirportInput({ value, onChange, placeholder, label }) {
    const [query, setQuery] = useState(value || '');
    const [suggestions, setSuggestions] = useState([]);
    const [showDropdown, setShowDropdown] = useState(false);
    const debounceRef = useRef(null);
    const [selected, setSelected] = useState(!!value);

    useEffect(() => {
        if (selected) return;
        if (query.length < 2) {
            // eslint-disable-next-line react-hooks/set-state-in-effect
            setSuggestions([]);
            return;
        }
        clearTimeout(debounceRef.current);
        debounceRef.current = setTimeout(async () => {
            try {
                const response = await fetch(`/api/places/suggestions?query=${query}`);
                const data = await response.json();
                setSuggestions(data.data || []);
                setShowDropdown(true);
            } catch {
                setSuggestions([]);
            }
        }, 300);
    }, [query, selected]);

    const handleSelect = (place) => {
        const iataCode = place.iata_code || place.iata_city_code;
        setQuery(`${place.name} (${iataCode})`);
        onChange(iataCode);
        setShowDropdown(false);
        setSuggestions([]);
        setSelected(true);
    };

    return (
        <div className="airport-input">
            <label className="search-bar__label">{label}</label>
            <div className="airport-input__wrapper">
                <input
                    className="search-bar__input"
                    type="text"
                    value={query}
                    onChange={(e) => {
                        setQuery(e.target.value);
                        onChange(e.target.value);
                        setSelected(false);
                    }}
                    placeholder={placeholder}
                    onFocus={() => {
                        if (!selected && suggestions.length > 0) setShowDropdown(true);
                    }}
                    onBlur={() => setTimeout(() => setShowDropdown(false), 200)}
                />
                {showDropdown && suggestions.length > 0 && (
                    <ul className="airport-input__dropdown">
                        {suggestions.slice(0, 6).map((place) => (
                            <li
                                key={place.id}
                                className="airport-input__option"
                                onMouseDown={() => handleSelect(place)}
                            >
                                <span className="airport-input__iata">
                                    {place.iata_code || place.iata_city_code}
                                </span>
                                <span className="airport-input__name">{place.name}</span>
                                <span className="airport-input__country">{place.city?.name || place.iata_country_code}</span>
                            </li>
                        ))}
                    </ul>
                )}
            </div>
        </div>
    );
}

export default AirportInput;