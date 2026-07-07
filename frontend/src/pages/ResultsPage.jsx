import { useLocation, useNavigate } from "react-router-dom";
import { useEffect, useState} from "react";
import FlightCard from "../components/results/FlightCard";
import CodeShareCard from "../components/results/CodeShareCard";
import Navbar from "../components/common/Navbar";
import "./ResultsPage.css";
import SkeletonLoader from "../components/common/SkeletonLoader";
import { ErrorMessage, EmptyMessage } from "../components/common/StatusMessage";
import SearchBar from "../components/search/SearchBar";
import SearchModeSelector from "../components/search/SearchModeSelector";
function ResultsPage(){
    const location = useLocation();
    const { origin: initOrigin, destination: initDestination, departureDate: initDepartureDate, passengers: initPassengers, cabinClass: initCabinClass, mode } = location.state || {};
    const [origin, setOrigin] = useState(initOrigin ?? "");
    const [destination, setDestination] = useState(initDestination ?? "");
    const [departureDate, setDepartureDate] = useState(initDepartureDate ?? "");
    const [adults, setAdults] = useState(initPassengers?.filter(p => p === "adult").length ?? 1);
    const [children, setChildren] = useState(initPassengers?.filter(p => p === "child").length ?? 0);
    const passengers = [
        ...Array(adults).fill("adult"),
        ...Array(children).fill("child")
    ];
    const [cabinClass, setCabinClass] = useState(initCabinClass ?? "economy");
    const [searchMode, setSearchMode] = useState(mode ?? "codeshare");
    const [ results, setResults] = useState([]);
    const [ loading, setLoading] = useState(true);
    const [ error, setError] = useState(null);
    const navigate = useNavigate();

    const handleSearch = () => {
        navigate("/results", {
            state: { origin, destination, departureDate, passengers, cabinClass, mode: searchMode }
        });
    };

    useEffect(() => {
        if (mode === "trend") {
            navigate("/trends", { state: { origin, destination, departureDate, passengers, cabinClass}});
            return;
        }
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, []);
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
    if (loading) return (
        <div>
            <Navbar />
            <SkeletonLoader />
        </div>
    );
    if (error) return (
        <div>
            <Navbar />
            <ErrorMessage message={error} />
        </div>
    );
    const grouped = results.reduce((groups, offer) => {
        const key = `${offer["Departure Time"]}_${offer["Operating IATA"]}`;
        if (!groups[key]) groups[key] = [];
        groups[key].push(offer);
        return groups;     
    }, {});
    const codeshareGroups = Object.values(grouped).filter((group) => group.length > 1);
    const regularGroups = Object.values((grouped)).filter((group) => group.length === 1);
    const sortedGroups = [...codeshareGroups, ...regularGroups];
    if (sortedGroups.length === 0) return (
        <div>
            <Navbar />
            <EmptyMessage />
        </div>
    );
    return (
    <>
        <Navbar />
        <div className="results-page__search">
            <SearchModeSelector mode={searchMode} onModeChange={setSearchMode} />
            <SearchBar
                origin={origin}
                setOrigin={setOrigin}
                destination={destination}
                setDestination={setDestination}
                departureDate={departureDate}
                setDepartureDate={setDepartureDate}
                adults={adults}
                setAdults={setAdults}
                children={children}
                setChildren={setChildren}
                cabinClass={cabinClass}
                setCabinClass={setCabinClass}
                onSearch={handleSearch}
            />
        </div>
        <div className="results-page">
            <div className="results-page__header">
                <h1 className="results-page__title">{origin} → {destination}</h1>
                <p className="results-page__subtitle">{departureDate} • {passengers?.length}名</p>
            </div>
            <p className="results-page__section-label">コードシェア便の価格差</p>
            <div className="results-page__list">
                {sortedGroups.map((group) => {
                    if (mode === "codeshare" && group.length === 1 && !group[0]["is Codeshare"]) return null;
                    return group.length > 1 
                        ? <CodeShareCard key={group[0]["Offer ID"]} offers={group} />
                        : <FlightCard key={group[0]["Offer ID"]} offer={group[0]} />
                })}
            </div>
        </div>
        
    </>
)
}

export default ResultsPage;