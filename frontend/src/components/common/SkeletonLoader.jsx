import './SkeletonLoader.css'

function SkeletonFlightCard() {
    return (
        <div className="skeleton-card">
            <div className="skeleton-row">
                <div className="shimmer" style={{ height: 15, width: 130 }}></div>
                <div className="shimmer" style={{ height: 13, width: 240 }}></div>
                <div className="shimmer" style={{ height: 18, width: 70 }}></div>
            </div>
        </div>
    )
}

function SkeletonCodeShareCard() {
    return (
        <div className="skeleton-card skeleton-card--codeshare">
            <div className="skeleton-row" style={{ marginBottom: 16 }}>
                <div className="shimmer" style={{ height: 13, width: 160 }}></div>
                <div className="shimmer" style={{ height: 13, width: 180 }}></div>
            </div>
            <div className="skeleton-row" style={{ marginBottom: 10 }}>
                <div className="shimmer" style={{ height: 16, width: 120 }}></div>
                <div className="shimmer" style={{ height: 20, width: 80 }}></div>
            </div>
            <div className="skeleton-row" style={{ marginBottom: 16 }}>
                <div className="shimmer" style={{ height: 16, width: 100 }}></div>
                <div className="shimmer" style={{ height: 20, width: 80 }}></div>
            </div>
            <div className="skeleton-gap">
                <div className="shimmer" style={{ height: 13, width: 40 }}></div>
                <div className="shimmer" style={{ height: 22, width: 120 }}></div>
            </div>
        </div>
    )
}

function SkeletonLoader() {
    return (
        <div className="skeleton-loader">
            <div style={{ marginBottom: 24 }}>
                <div className="shimmer" style={{ height: 24, width: 200, marginBottom: 8 }}></div>
                <div className="shimmer" style={{ height: 14, width: 140 }}></div>
            </div>
            <SkeletonCodeShareCard />
            <SkeletonCodeShareCard />
            <SkeletonFlightCard />
            <SkeletonFlightCard />
            <SkeletonFlightCard />
        </div>
    )
}

export default SkeletonLoader;