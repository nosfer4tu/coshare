import './Navbar.css'
import { Link } from 'react-router-dom';
function Navbar(){
    return(
        <nav className="navbar">
            <div className="navbar__inner">
                <Link to="/" className="navbar__logo">CoShare.jp</Link>
                <span className="navbar__tagline">同じ便、なぜ価格が違う？</span>
            </div>
        </nav>
    )
}

export default Navbar;