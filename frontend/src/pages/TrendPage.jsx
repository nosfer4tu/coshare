import { useLocation } from "react-router-dom";
import { useEffect, useState } from "react";
import Navbar from "../components/common/Navbar";
import PriceTrendChart from "../components/results/PriceTrendChart";

function TrendPage(){
    const location = useLocation();
    const { origin, destination} = location.state || {};
    const [ results, setResults] = useState([]);
    const [ loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [recommendation, setRecommendation] = useState(null);

    useEffect(() => {
        let endpoint = "/api/trends/annual";
        const params = new URLSearchParams({
            origin,
            destination,
        });
        const fetchData = async () =>{
            try{
                if (!endpoint) throw new Error("Unknown search mode");
                const response = await fetch(endpoint + "?" + params.toString());
                if (!response.ok) throw new Error (`Request failed: ${response.status}`);
                const data = await response.json();
                setResults(data.data);
            } catch(error){
                setError(error.message);
            } finally{
                setLoading(false);
            }
        };
        fetchData();
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, []);
    useEffect(() => {
        let endpoint = "/api/trends/recommend";
        const params = new URLSearchParams({
            origin,
            destination
        })
        const fetchRecommendationData = async () => {
            try {
                if (!endpoint) throw new Error("Unknown search mode");
                const response = await fetch(endpoint + "?" + params.toString());
                if (!response.ok) throw new Error (`Request failed: ${response.status}`);
                const data = await response.json();
                setRecommendation(data);
            } catch (error) {
                setError(error.message);
            } finally {
                setLoading(false);
            }
        }
        fetchRecommendationData();
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, []);
    if (loading) return <p>読み込み中...</p>
    if (error) return <p>{error}</p>
    return (
        <div>
        <Navbar />
        <div style={{ maxWidth: '800px', margin: '0 auto', padding: '24px 16px' }}>
            <h1 style={{ fontSize: '20px', fontWeight: '600', marginBottom: '4px' }}>
                {origin} → {destination} 価格トレンド
            </h1>
            <p style={{ fontSize: '14px', color: '#6B7280', marginBottom: '24px' }}>
                取得データ: {results.length}件
            </p>
            <PriceTrendChart data={results} />
            {recommendation && (
                <div style={{ marginTop: 24, display: 'flex', gap: 16 }}>
                    <div style={{ flex: 1, padding: 16, background: '#CCFBF1', borderRadius: 12 }}>
                        <p style={{ fontSize: 12, color: '#0D9488', fontWeight: 600, marginBottom: 4 }}>最安月</p>
                        <p style={{ fontSize: 20, fontFamily: 'JetBrains Mono', color: '#111827', fontWeight: 600 }}>
                            {recommendation.cheapest_month}月
                        </p>
                        <p style={{ fontSize: 13, color: '#6B7280', marginTop: 4 }}>
                            平均 {Number(recommendation.cheapest_price).toLocaleString('ja-JP', { style: 'currency', currency: 'JPY' })}
                        </p>
                    </div>
                    <div style={{ flex: 1, padding: 16, background: '#FEF2F2', borderRadius: 12 }}>
                        <p style={{ fontSize: 12, color: '#EF4444', fontWeight: 600, marginBottom: 4 }}>最高値月</p>
                        <p style={{ fontSize: 20, fontFamily: 'JetBrains Mono', color: '#111827', fontWeight: 600 }}>
                            {recommendation.most_expensive_month}月
                        </p>
                        <p style={{ fontSize: 13, color: '#6B7280', marginTop: 4 }}>
                            平均 {Number(recommendation.most_expensive_price).toLocaleString('ja-JP', { style: 'currency', currency: 'JPY' })}
                        </p>
                    </div>
                </div>
            )}
        </div>
    </div>
    )
}

export default TrendPage;