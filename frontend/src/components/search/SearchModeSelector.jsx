function SearchModeSelector({mode, onModeChange}){
    return (
        <div>
            <button className={mode === "codeshare" ? "btn-active" : "btn"}
            onClick={() => onModeChange("codeshare")} >
                コードシェア
            </button>
            <button className={mode === "trend" ? "btn-active" : "btn"}
            onClick={() => onModeChange("trend")} >
                価格トレンド
            </button>
            <button className={mode === "both" ? "btn-active" : "btn"}
            onClick={() => onModeChange("both")} >
                両方
            </button>
        </div>
        
    )
}

export default SearchModeSelector;