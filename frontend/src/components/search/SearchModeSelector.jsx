import './SearchModeSelector.css'

function SearchModeSelector({mode, onModeChange}){
    return (
        <div className="mode-selector">
            <button 
                className={`mode-selector__btn ${mode === "codeshare" ? "mode-selector__btn--active" : ""}`}
                onClick={() => onModeChange("codeshare")}>
                コードシェア
            </button>
            <button 
                className={`mode-selector__btn ${mode === "trend" ? "mode-selector__btn--active" : ""}`}
                onClick={() => onModeChange("trend")}>
                価格トレンド
            </button>
            <button 
                className={`mode-selector__btn ${mode === "both" ? "mode-selector__btn--active" : ""}`}
                onClick={() => onModeChange("both")}>
                両方
            </button>
        </div>
    )
}

export default SearchModeSelector;