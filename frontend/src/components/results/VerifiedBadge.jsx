import { Link } from 'react-router-dom';
import './VerifiedBadge.css';

// A dated record, not a claim about the card's current price: it only says when a
// manual check against the official site was made, and links to the full record.
function VerifiedBadge({ check }) {
    if (!check) return null;
    return (
        <Link to="/verification" className="verified-badge">
            {check.check_date}に公式サイトと照合
        </Link>
    );
}

export default VerifiedBadge;
