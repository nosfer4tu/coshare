import { snapshotNoticeText } from '../../utils/snapshotNotice';
import './SnapshotNotice.css';

// Shown only when the response is a saved snapshot, in addition to TestDataNotice.
function SnapshotNotice({ capturedAt }) {
    const text = snapshotNoticeText(capturedAt);
    if (!text) return null;

    return (
        <div className="snapshot-notice" role="status">
            <p className="snapshot-notice__text">{text}</p>
        </div>
    );
}

export default SnapshotNotice;
