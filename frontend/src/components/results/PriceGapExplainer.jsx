import { useState } from 'react';
import './PriceGapExplainer.css';

function PriceGapExplainer() {
    const [isOpen, setIsOpen] = useState(false);

    return (
        <div className="price-gap-explainer">
            <button
                type="button"
                className="price-gap-explainer__toggle"
                aria-expanded={isOpen}
                aria-controls="price-gap-explainer-panel"
                onClick={() => setIsOpen((open) => !open)}
            >
                なぜ価格が違う？
            </button>
            <div
                id="price-gap-explainer-panel"
                className="price-gap-explainer__panel"
                hidden={!isOpen}
            >
                <h2 className="price-gap-explainer__heading">なぜ同じ便で価格が違うの？</h2>
                <p className="price-gap-explainer__body">
                    同じ飛行機に乗っても、どの航空会社の便名で買うかで運賃が変わることが
                    あります。各社が運賃クラス(座席の在庫)を個別に設定し、航空会社間の収益配分の
                    取り決めや販売経路も会社ごとに異なるためです。
                </p>
                <p className="price-gap-explainer__note">
                    安い方が必ずしも同じ条件とは限りません。手荷物・変更条件・マイルの積算率が
                    異なる場合があるので、予約前に各社の公式サイトで確認してください。
                </p>
            </div>
        </div>
    );
}

export default PriceGapExplainer;
