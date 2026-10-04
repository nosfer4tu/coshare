import { SHOW_TEST_DATA_NOTICE } from '../../constants/testDataNotice';
import './TestDataNotice.css';

function TestDataNotice({ children }) {
    if (!SHOW_TEST_DATA_NOTICE) return null;

    return (
        <div className="test-data-notice" role="note">
            <p className="test-data-notice__text">{children}</p>
        </div>
    );
}

export default TestDataNotice;
