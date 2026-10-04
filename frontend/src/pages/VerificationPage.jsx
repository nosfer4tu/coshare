import { useEffect, useState } from "react";
import Navbar from "../components/common/Navbar";
import { ErrorMessage } from "../components/common/StatusMessage";
import "../components/common/StatusMessage.css";
import "../components/common/SkeletonLoader.css";
import { MATCH_TOLERANCE_PERCENT, priceDifferencePercent } from "../utils/verifiedChecks";
import "./VerificationPage.css";

const EMPTY = "—";

const SOURCE_LABELS = {
    duffel: "Duffel(テスト環境)",
    flightlabs: "FlightLabs",
};

const VERDICT_LABELS = {
    match: "照合済み",
    mismatch: "相違あり",
    not_comparable: "比較不可",
};

const formatYen = (value) =>
    value ? Number(value).toLocaleString("ja-JP", { style: "currency", currency: "JPY" }) : EMPTY;

function formatDifference(check) {
    const percent = priceDifferencePercent(check.sandbox_price_jpy, check.real_price_jpy);
    if (percent === null) return EMPTY;
    return `${percent > 0 ? "+" : ""}${percent}%`;
}

function SourceLink({ url }) {
    if (typeof url === "string" && url.startsWith("https://")) {
        return <a href={url} target="_blank" rel="noopener noreferrer">{formatSourceHost(url)}</a>;
    }
    return <span>{url || EMPTY}</span>;
}

function formatSourceHost(url) {
    try {
        return new URL(url).hostname + " ↗";
    } catch {
        return url;
    }
}

function VerificationPage() {
    const [checks, setChecks] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        const fetchData = async () => {
            try {
                const response = await fetch("/api/verified-checks");
                if (!response.ok) throw new Error(`Request failed: ${response.status}`);
                const data = await response.json();
                setChecks(Array.isArray(data.data) ? data.data : []);
            } catch (error) {
                setError(error.message);
            } finally {
                setLoading(false);
            }
        };
        fetchData();
    }, []);

    let body;
    if (loading) {
        body = (
            <div>
                <div className="shimmer" style={{ height: 40, marginBottom: 8 }}></div>
                <div className="shimmer" style={{ height: 40, marginBottom: 8 }}></div>
                <div className="shimmer" style={{ height: 40 }}></div>
            </div>
        );
    } else if (error) {
        body = <ErrorMessage message={error} />;
    } else if (checks.length === 0) {
        body = (
            <div className="status-message status-message--empty">
                <p className="status-message__title">照合記録はまだありません。</p>
            </div>
        );
    } else {
        body = (
            <div className="verification-page__table-wrap">
                <table className="verification-page__table">
                    <thead>
                        <tr>
                            <th scope="col">路線</th>
                            <th scope="col">搭乗日</th>
                            <th scope="col">航空会社</th>
                            <th scope="col">取得元</th>
                            <th scope="col" className="verification-page__num">ツール価格</th>
                            <th scope="col" className="verification-page__num">公式サイト価格</th>
                            <th scope="col" className="verification-page__num">差</th>
                            <th scope="col">判定</th>
                            <th scope="col">確認日</th>
                            <th scope="col">メモ</th>
                        </tr>
                    </thead>
                    <tbody>
                        {checks.map((check) => (
                            <tr key={check.id}>
                                <td className="mono">{check.route}</td>
                                <td className="mono">{check.flight_date}</td>
                                <td>{check.carrier_checked}</td>
                                <td>{SOURCE_LABELS[check.sandbox_source] ?? check.sandbox_source}</td>
                                <td className="verification-page__num mono">{formatYen(check.sandbox_price_jpy)}</td>
                                <td className="verification-page__num mono">{formatYen(check.real_price_jpy)}</td>
                                <td className="verification-page__num mono">{formatDifference(check)}</td>
                                <td>
                                    <span className={`verification-page__verdict verification-page__verdict--${check.verdict}`}>
                                        {VERDICT_LABELS[check.verdict] ?? check.verdict}
                                    </span>
                                </td>
                                <td className="mono">{check.check_date}</td>
                                <td className="verification-page__notes">
                                    {check.notes && <span>{check.notes} </span>}
                                    <SourceLink url={check.real_source_url} />
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        );
    }

    return (
        <div>
            <Navbar />
            <div className="verification-page">
                <h1 className="verification-page__title">データ検証</h1>
                <p className="verification-page__intro">
                    この画面は、アプリが取得した価格を航空会社の公式サイトで手作業で照合した記録です。
                    価格は確認日時点のもので、現在の検索結果とは異なる場合があります。
                    ツール価格は固定レート(¥155/USD)で円換算しています。
                </p>
                <p className="verification-page__note">
                    「照合済み」は、ツール価格が公式サイト価格の±{MATCH_TOLERANCE_PERCENT}%以内であることを示します(同一価格ではありません)。
                </p>
                {body}
            </div>
        </div>
    );
}

export default VerificationPage;
