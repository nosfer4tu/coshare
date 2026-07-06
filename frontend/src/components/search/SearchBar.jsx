import './SearchBar.css'

function SearchBar({origin, setOrigin, destination, setDestination, departureDate, setDepartureDate, adults, setAdults, children, setChildren, cabinClass, setCabinClass, onSearch}){
    return (
        <div className="search-bar">
            <div className="search-bar__row">
                <div className="search-bar__field">
                    <label className="search-bar__label">出発地</label>
                    <input 
                        className="search-bar__input"
                        type="text"
                        value={origin}
                        onChange={(e) => setOrigin(e.target.value)}
                        placeholder="例：TYO"
                    />
                </div>
                <div className="search-bar__field">
                    <label className="search-bar__label">目的地</label>
                    <input 
                        className="search-bar__input"
                        type="text"
                        value={destination}
                        onChange={(e) => setDestination(e.target.value)}
                        placeholder="例：LAX"
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