import Navbar from '../common/Navbar';
import { EmptyMessage } from '../common/StatusMessage';
import RealPricesPanel from './RealPricesPanel';
import { isPanelVisible } from '../../utils/realPrices';
import './RealPricesPanel.css';

// Empty-results and error screens: the status message (children) with the real-prices
// panel below it. The panel's data comes from useRealPrices, which depends only on the
// search params, so it shows even when the offer fetch failed or returned nothing.
// (The loading screen does not use this component, so it never shows the panel.)
function ResultsStatusScreen({ children, realPrices }) {
    const { state, search } = realPrices;
    return (
        <div>
            <Navbar />
            {children}
            {isPanelVisible(state, search) && (
                <div className="real-prices-slot">
                    <RealPricesPanel state={state} search={search} />
                </div>
            )}
        </div>
    );
}

// Shown instead of the default subline only when the panel below has real prices to point at.
const EMPTY_BODY_WITH_REAL_PRICES =
    'テスト環境にこの路線・日付のデータがありません。下の実測価格を参考にしてください。';

// Empty-results screen. The title stays the same; the subline changes only in the "found" state.
export function EmptyResultsScreen({ realPrices }) {
    const body = realPrices.state.status === 'found' ? EMPTY_BODY_WITH_REAL_PRICES : undefined;
    return (
        <ResultsStatusScreen realPrices={realPrices}>
            <EmptyMessage body={body} />
        </ResultsStatusScreen>
    );
}

export default ResultsStatusScreen;
