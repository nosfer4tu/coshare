import './SearchBar.css'
import AirportInput from './AirportInput';

function SearchBar({origin, setOrigin, destination, setDestination, departureDate, setDepartureDate, adults, setAdults, children, setChildren, cabinClass, setCabinClass, onSearch}){
    return (
        <div className="search-bar">
            <div className="search-bar__row">
                <div className="search-bar__field">
                    <AirportInput
                        label="出発地"
                        value={origin}
                        onChange={setOrigin}
                        placeholder="例：東京、NRT"
                    />
                </div>
                <div className="search-bar__field">
                    <AirportInput
                        label="目的地"
                        value={destination}
                        onChange={setDestination}
                        placeholder="例：ロサンゼルス、LAX"
                    />
                </div>
                <div className="search-bar__field">
                    <label className="search-bar__label">出発日</label>
                    <input 
                        className="search-bar__input"
                        type="date"
                        value={departureDate}
                        onChange={(e) => setDepartureDate(e.target.value)}
                    />
                </div>
            </div>
            <div className="search-bar__row">
                <div className="search-bar__field">
                    <label className="search-bar__label">大人（18歳以上）</label>
                    <div className="search-bar__counter">
                        <button className="search-bar__counter-btn" onClick={() => adults > 1 ? setAdults(adults - 1) : null}>−</button>
                        <span className="search-bar__counter-value">{adults}</span>
                        <button className="search-bar__counter-btn" onClick={() => setAdults(adults + 1)}>+</button>
                    </div>
                </div>
                <div className="search-bar__field">
                    <label className="search-bar__label">子供（0〜17歳）</label>
                    <div className="search-bar__counter">
                        <button className="search-bar__counter-btn" onClick={() => children > 0 ? setChildren(children - 1) : null}>−</button>
                        <span className="search-bar__counter-value">{children}</span>
                        <button className="search-bar__counter-btn" onClick={() => setChildren(children + 1)}>+</button>
                    </div>
                </div>
                <div className="search-bar__field">
                    <label className="search-bar__label">座席クラス</label>
                    <select className="search-bar__select" value={cabinClass} onChange={(e) => setCabinClass(e.target.value)}>
                        <option value="economy">エコノミー</option>
                        <option value="premium_economy">プレミアムエコノミー</option>
                        <option value="business">ビジネス</option>
                        <option value="first">ファースト</option>
                    </select>
                </div>
                <button className="search-bar__submit" onClick={onSearch}>検索</button>
            </div>
        </div>
    )
}

export default SearchBar;