import { useState, useEffect } from 'react';

/**
 * Dashboard Data Service Hook
 * Loads caller-provided API data and surfaces failures without substituting mock data.
 */
export function useDashboardService<T>(fetchData: () => Promise<T>) {
    const [data, setData] = useState<T | null>(null);
    const [loading, setLoading] = useState<boolean>(true);
    const [error, setError] = useState<Error | null>(null);

    useEffect(() => {
        let mounted = true;

        async function loadData() {
            setLoading(true);
            setError(null);

            try {
                const result = await fetchData();

                if (mounted) {
                    setData(result);
                }
            } catch (e) {
                if (mounted) {
                    setError(e instanceof Error ? e : new Error(String(e)));
                }
            } finally {
                if (mounted) {
                    setLoading(false);
                }
            }
        }

        loadData();

        return () => {
            mounted = false;
        };
    }, [fetchData]);

    return { data, loading, error };
}
