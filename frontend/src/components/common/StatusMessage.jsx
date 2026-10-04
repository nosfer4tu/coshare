import './StatusMessage.css'
import { Link } from 'react-router-dom'

export function ErrorMessage({ message }) {
    return (
        <div className="status-message status-message--error">
            <p className="status-message__title">エラーが発生しました</p>
            <p className="status-message__body">{message}</p>
            <Link to="/" className="status-message__link">検索に戻る</Link>
        </div>
    )
}

export function EmptyMessage({ title = '結果が見つかりませんでした', body = '別の路線や日付で試してみてください' }) {
    return (
        <div className="status-message status-message--empty">
            <p className="status-message__title">{title}</p>
            <p className="status-message__body">{body}</p>
            <Link to="/" className="status-message__link">検索に戻る</Link>
        </div>
    )
}