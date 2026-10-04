import { BrowserRouter, Routes, Route } from "react-router-dom";
import HomePage from "./pages/HomePage";
import ResultsPage from "./pages/ResultsPage";
import TrendPage from "./pages/TrendPage";
import DestinationPage from "./pages/DestinationPage";
import VerificationPage from "./pages/VerificationPage";

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<HomePage />}></Route>
        <Route path="/results" element={<ResultsPage />}></Route>
        <Route path="/trends" element={<TrendPage />}></Route>
        <Route path="/destinations" element={<DestinationPage />}></Route>
        <Route path="/verification" element={<VerificationPage />}></Route>
      </Routes>
    </BrowserRouter>
  )
}

export default App;