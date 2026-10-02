import { useLocation, useNavigate, useSearchParams } from "react-router-dom";
import { useEffect, useState} from "react";
import FlightCard from "../components/results/FlightCard";
import CodeShareCard from "../components/results/CodeShareCard";
import PriceGapExplainer from "../components/results/PriceGapExplainer";
import Navbar from "../components/common/Navbar";
import "./ResultsPage.css";
import SkeletonLoader from "../components/common/SkeletonLoader";
import { ErrorMessage, EmptyMessage } from "../components/common/StatusMessage";
import SearchBar from "../components/search/SearchBar";
import SearchModeSelector from "../components/search/SearchModeSelector";
import { hasRealGap } from "../utils/codeshareGap";
function ResultsPage(){
    const location = useLocation();
    const navigate = useNavigate();
    const [searchParams, setSearchParams] = useSearchParams();

    const initialPassengers = (searchParams.get("passengers") || "").split(",").filter(Boolean).length
        ? searchParams.get("passengers").split(",")
        : location.state?.passengers ?? [];

    const [origin, setOrigin] = useState(searchParams.get("origin") ?? location.state?.origin ?? "");
    const [destination, setDestination] = useState(searchParams.get("destination") ?? location.state?.destination ?? "");
    const [departureDate, setDepartureDate] = useState(searchParams.get("departureDate") ?? location.state?.departureDate ?? "");
    const [adults, setAdults] = useState(initialPassengers.filter(p => p === "adult").length || 1);
    const [children, setChildren] = useState(initialPassengers.filter(p => p === "child").length);
    const passengers = [
        ...Array(adults).fill("adult"),
        ...Array(children).fill("child")
    ];
    const [cabinClass, setCabinClass] = useState(searchParams.get("cabinClass") ?? location.state?.cabinClass ?? "economy");
    const [searchMode, setSearchMode] = useState(searchParams.get("mode") ?? location.state?.mode ?? "codeshare");
    const [ results, setResults] = useState([]);
    const [ loading, setLoading] = useState(true);
    const [ error, setError] = useState(null);

    const handleSearch = () => {
        const newPassengers = [
            ...Array(adults).fill("adult"),
            ...Array(children).fill("child")
        ];
        setSearchParams({
            origin,
            destination,
            departureDate,
            passengers: newPassengers.join(","),
            cabinClass,
            mode: searchMode
        });
    };

    // First navigation from HomePage arrives via router state; promote it into the
    // URL so every subsequent search is driven by searchParams alone.
    useEffect(() => {
        if (!searchParams.get("origin") && location.state) {
            const { origin: stateOrigin, destination: stateDestination, departureDate: stateDepartureDate, passengers: statePassengers, cabinClass: stateCabinClass, mode: stateMode } = location.state;
            setSearchParams({
                origin: stateOrigin ?? "",
                destination: stateDestination ?? "",
                departureDate: stateDepartureDate ?? "",
                passengers: (statePassengers ?? []).join(","),
                cabinClass: stateCabinClass ?? "economy",
                mode: stateMode ?? "codeshare"
            }, { replace: true });
        }
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, []);

    useEffect(() => {
        const mode = searchParams.get("mode");
        if (!mode) return;
        if (mode === "trend") {
            navigate("/trends", {
                state: {
                    origin: searchParams.get("origin"),
                    destination: searchParams.get("destination"),
                    departureDate: searchParams.get("departureDate"),
                    passengers: (searchParams.get("passengers") || "").split(",").filter(Boolean),
                    cabinClass: searchParams.get("cabinClass")
                }
            });
            return;
        }
        let endpoint;
        switch(mode){
            case "codeshare":
                endpoint = "/api/codeshare/detect";
                break;
            case "both":
                endpoint = "/api/flights/search";
                break;
            default:
                return;
        }
        const params = new URLSearchParams({
            origin: searchParams.get("origin") ?? "",
            destination: searchParams.get("destination") ?? "",
            departureDate: searchParams.get("departureDate") ?? "",
            passengers: searchParams.get("passengers") ?? "",
            cabinClass: searchParams.get("cabinClass") ?? "economy"
        });
        const url = endpoint + "?" + params.toString();
        const fetchData = async () =>{
            setLoading(true);
            setError(null);
            try {
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
    }, [searchParams, navigate]);

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
    const gappedCodeshareGroups = codeshareGroups.filter((group) => hasRealGap(group));
    const zeroGapCodeshareGroups = codeshareGroups.filter((group) => !hasRealGap(group));
    const sortedGroups = [...gappedCodeshareGroups, ...zeroGapCodeshareGroups, ...regularGroups];
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
            <PriceGapExplainer />
            <div className="results-page__list">
                {sortedGroups.map((group) => {
                    if (searchMode === "codeshare" && group.length === 1 && !group[0]["is Codeshare"]) return null;
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
