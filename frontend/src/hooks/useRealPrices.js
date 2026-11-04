import { useEffect, useState } from 'react';
import { fetchRealPrices, HIDDEN, normalizeSearch } from '../utils/realPrices';

const LOADING = { status: 'loading' };

// One request per committed search (route + date). Failures never throw: see fetchRealPrices.
export function useRealPrices(origin, destination, departureDate) {
    const search = normalizeSearch(origin, destination, departureDate);
    const from = search?.origin ?? '';
    const to = search?.destination ?? '';
    const date = search?.departureDate ?? '';
    const key = search ? `${from}-${to}-${date}` : '';
    const [result, setResult] = useState({ key: '', state: LOADING });

    useEffect(() => {
        if (!from) return undefined;
        const controller = new AbortController();
        fetchRealPrices({ origin: from, destination: to, departureDate: date }, { signal: controller.signal })
            .then((state) => {
                if (!controller.signal.aborted) setResult({ key: `${from}-${to}-${date}`, state });
            });
        return () => controller.abort();
    }, [from, to, date]);

    if (!search) return { search: null, state: HIDDEN };
    // Until the response for the current search arrives, show nothing (no stale panel).
    return { search, state: result.key === key ? result.state : LOADING };
}
