// Pure helpers for the saved-data banner (a search response with data_source "snapshot").

// The UTC date (YYYY-MM-DD) of a captured_at ISO string, or null when it is not a valid date.
export function snapshotDate(capturedAt) {
    const date = new Date(capturedAt);
    if (typeof capturedAt !== 'string' || Number.isNaN(date.getTime())) return null;
    return date.toISOString().slice(0, 10);
}

// What ResultsPage keeps from a search response: null for live data.
export function snapshotInfo(body) {
    if (!body || body.data_source !== 'snapshot') return null;
    return { capturedAt: body.captured_at };
}

export function snapshotNoticeText(capturedAt) {
    const date = snapshotDate(capturedAt);
    return date ? `保存済みのDuffelテストデータを表示しています(取得日 ${date})` : null;
}
