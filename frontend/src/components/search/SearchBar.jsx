function SearchBar({origin, setOrigin, destination, setDestination, departureDate, setDepartureDate, adults, setAdults, children, setChildren, cabinClass, setCabinClass, onSearch}){
        return (
            <>
                <label>出発地</label>
                <input 
                    type="text"
                    value={origin}
                    onChange={(e) => setOrigin(e.target.value)}
                    placeholder="出発地（例：TYO）"
                />
                <label>目的地</label>
                <input 
                    type="text"
                    value={destination}
                    onChange={(e) => setDestination(e.target.value)}
                    placeholder="目的地（例：CTS）"
                />
                <label>出発日</label>
                <input 
                    type="date"
                    value={departureDate}
                    onChange={(e) => setDepartureDate(e.target.value)}
                />
                <label>大人（18歳以上）</label>            
                <button onClick={() => adults > 1 ? setAdults(adults - 1) : null}>-</button>
                <span>{adults}</span>
                <button onClick={() => setAdults(adults + 1)}>+</button>
                <label>子供（0〜17歳）</label>
                <button onClick={() => children > 0 ? setChildren(children - 1) : null}>-</button>
                <span>{children}</span>
                <button onClick={() => setChildren(children + 1)}>+</button>
                <select value={cabinClass} onChange={(e) => setCabinClass(e.target.value)}>
                    <option value="economy">エコノミー</option>
                    <option value="premium_economy">プレミアムエコノミー</option>
                    <option value="business">ビジネス</option>
                    <option value="first">ファースト</option>
                </select>
                <button onClick={onSearch}>検索</button>
            </>
        )
    }

export default SearchBar;
