import { formatYen, isPanelVisible, skyscannerUrl } from '../../utils/realPrices';
import './RealPricesPanel.css';

function times(entry) {
    return `${entry.dep}–${entry.arr}${entry.arr_next_day ? '(翌日)' : ''}`;
}

function SummaryLine({ label, entry }) {
    if (!entry) return null;
    return (
        <li className="real-prices__line">
            <span className="real-prices__line-label">{label}</span>
            <span className="real-prices__line-main">
                {entry.airline}
                {entry.flight_number ? ` ${entry.flight_number}` : ''}
                <span className="mono real-prices__line-time">{times(entry)}</span>
            </span>
            <span className="mono real-prices__price">{formatYen(entry.price_jpy)}</span>
            <span className="real-prices__seller">{entry.seller}</span>
        </li>
    );
}

function PairSide({ side }) {
    return (
        <span className="real-prices__pair-side">
            <span className="real-prices__pair-name">
                {side.flight_number ?? ''} {side.airline}
            </span>
            <span className="mono real-prices__price">{formatYen(side.price_jpy)}</span>
            <span className="real-prices__seller">{side.seller}</span>
        </span>
    );
}

function EntriesTable({ entries }) {
    const hasSitePrice = entries.some((e) => e.airline_site_price_jpy != null);
    return (
        <details className="real-prices__details">
            <summary className="real-prices__summary">全{entries.length}件の価格を見る</summary>
            <div className="real-prices__table-wrap">
                <table className="real-prices__table">
                    <thead>
                        <tr>
                            <th scope="col">航空会社</th>
                            <th scope="col">出発–到着</th>
                            <th scope="col" className="real-prices__num">価格</th>
                            <th scope="col">販売元</th>
                            {hasSitePrice && <th scope="col" className="real-prices__num">公式サイト</th>}
                        </tr>
                    </thead>
                    <tbody>
                        {entries.map((entry, index) => (
                            <tr key={`${entry.flight_number ?? entry.airline}-${entry.dep}-${index}`}>
                                <td>
                                    {entry.airline}
                                    {entry.flight_number ? ` ${entry.flight_number}` : ''}
                                    {entry.kind === 'lcc' && <span className="real-prices__badge">LCC</span>}
                                    {entry.note && <span className="real-prices__note">{entry.note}</span>}
                                </td>
                                <td className="mono">{times(entry)}</td>
                                <td className="mono real-prices__num">{formatYen(entry.price_jpy)}</td>
                                <td>{entry.seller}</td>
                                {hasSitePrice && (
                                    <td className="mono real-prices__num">
                                        {entry.airline_site_price_jpy != null ? formatYen(entry.airline_site_price_jpy) : '–'}
                                    </td>
                                )}
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </details>
    );
}

// Reference prices checked by hand. Rendered apart from the offer cards and never mixed into them.
// `state` comes from useRealPrices; `search` is the normalised { origin, destination, departureDate }.
function RealPricesPanel({ state, search }) {
    if (!isPanelVisible(state, search)) return null;

    if (state.status !== 'found') {
        return (
            <section className="real-prices real-prices--empty" aria-label="実測価格との比較">
                <p className="real-prices__empty-text">この路線・日付の実測データはまだありません</p>
                <a
                    className="real-prices__link"
                    href={skyscannerUrl(search)}
                    target="_blank"
                    rel="noopener noreferrer"
                >
                    Skyscannerで同じ路線・日付を見る
                </a>
            </section>
        );
    }

    const { data } = state;
    const summary = data.summary ?? {};
    const pairs = Array.isArray(summary.codeshare_pairs) ? summary.codeshare_pairs : [];
    return (
        <section className="real-prices" aria-labelledby="real-prices-title">
            <h2 id="real-prices-title" className="real-prices__title">実測価格との比較</h2>
            <p className="real-prices__intro">
                手動で確認した実際の価格(確認日 <span className="mono">{data.captured_on}</span>)。現在の価格とは異なる場合があります
            </p>
            <p className="real-prices__source">出典: {data.source}・直行便のみ</p>

            {(summary.cheapest_lcc || summary.cheapest_full_service) && (
                <ul className="real-prices__lines">
                    <SummaryLine label="最安LCC" entry={summary.cheapest_lcc} />
                    <SummaryLine label="最安フルサービス" entry={summary.cheapest_full_service} />
                </ul>
            )}

            {pairs.length > 0 && (
                <div className="real-prices__pairs">
                    <h3 className="real-prices__subtitle">同じ便の価格差</h3>
                    <ul className="real-prices__pair-list">
                        {pairs.map((pair) => (
                            <li
                                key={`${pair.cheaper.flight_number}-${pair.pricier.flight_number}`}
                                className="real-prices__pair"
                            >
                                <PairSide side={pair.cheaper} />
                                <PairSide side={pair.pricier} />
                                <span className="real-prices__gap">
                                    差額 <span className="mono">{formatYen(pair.gap_jpy)}</span>
                                </span>
                            </li>
                        ))}
                    </ul>
                </div>
            )}

            <EntriesTable entries={data.entries} />
        </section>
    );
}

export default RealPricesPanel;
