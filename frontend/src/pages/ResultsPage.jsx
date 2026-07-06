import { useLocation } from "react-router-dom";
import { useEffect, useState} from "react";
import FlightCard from "../components/results/FlightCard";
import CodeShareCard from "../components/results/CodeShareCard";
import Navbar from "../components/common/Navbar";
import "./ResultsPage.css";
function ResultsPage(){
    const location = useLocation();
    const { origin, destination, departureDate, passengers, cabinClass, mode} = location.state || {};
    const [ results, setResults] = useState([]);
    const [ loading, setLoading] = useState(true);
    const [ error, setError] = useState(null);
    
    useEffect(() => {
        let endpoint;
        switch(mode){
            case "codeshare":
                endpoint = "/api/codeshare/detect";
                break;
            case "trend":
                endpoint = "/api/trends/annual";
                break;
            case "both":
                endpoint = "/api/flights/search";
                break;
            default:
                return;       
        }
        const params = new URLSearchParams({
            origin,
            destination,
            departureDate,
            passengers: passengers?.join(",") ?? "",
            cabinClass
        });
        const url = endpoint + "?" + params.toString();
        const fetchData = async () =>{
            try {
                if (!endpoint) throw new Error("Unknown search mode");
                const response = await fetch(url);
                if (!response.ok) throw new Error(`Request failed: ${response.status}`);
                const data = await response.json();
                setResults(data.data);
            } catch (error) {
                setError(error.message);
            } finally{
                setLoading(false);
            }
        };
        fetchData();
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, []);
    if (loading) return <p>読み込み中...</p>
    if (error) return <p>{error}</p>
    const grouped = results.reduce((groups, offer) => {
        const key = `${offer["Departure Time"]}_${offer["Operating IATA"]}`;
        if (!groups[key]) groups[key] = [];
        groups[key].push(offer);
        return groups;     
    }, {});
    const codeshareGroups = Object.values(grouped).filter((group) => group.length > 1);
    const regularGroups = Object.values((grouped)).filter((group) => group.length === 1);
    const sortedGroups = [...codeshareGroups, ...regularGroups];
    return (
    <>
        <Navbar />
        <div className="results-page">
            <div className="results-page__header">
                <h1 className="results-page__title">{origin} → {destination}</h1>
                <p className="results-page__subtitle">{departureDate} • {passengers?.length}名</p>
            </div>
            <p className="results-page__section-label">コードシェア便の価格差</p>
            <div className="results-page__list">
                {sortedGroups.map((group) => (
                    group.length > 1 
                    ? <CodeShareCard key={group[0]["Offer ID"]} offers={group} />
                    : <FlightCard key={group[0]["Offer ID"]} offer={group[0]} />
                ))}
            </div>
        </div>
    </>
)
}

export default ResultsPage;