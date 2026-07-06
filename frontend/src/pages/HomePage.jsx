import Navbar from "../components/common/Navbar";
import SearchModeSelector from "../components/search/SearchModeSelector";
import SearchBar from "../components/search/SearchBar";
import { useState } from "react";
import { useNavigate } from 'react-router-dom';
import "./HomePage.css";

function HomePage() {
    const [mode, setMode] = useState("codeshare");
    const navigate = useNavigate();
    const [origin, setOrigin] = useState("");
    const [destination, setDestination] = useState("");
    const [departureDate, setDepartureDate] = useState("");
    const [adults, setAdults] = useState(1);
    const [children, setChildren] = useState(0);
    const [cabinClass, setCabinClass] = useState("economy");
    const handleSearch = () => {
        const passengers = [
            ...Array(adults).fill("adult"),
            ...Array(children).fill("child")
        ]
        navigate("/results",{
            state:{ origin, destination, departureDate, passengers, cabinClass, mode}
        })
    }
    return (
    <div>
        <Navbar />
        <div className="home-page">
            <section className="home-page__hero">
                <h1 className="home-page__title">賢く飛ぼう、日本から</h1>
                <p className="home-page__subtitle">コードシェア便の価格差を発見し、最安値で予約しよう</p>
            </section>
            <SearchModeSelector mode={mode} onModeChange={setMode} />
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
    </div>
)
}

export default HomePage;