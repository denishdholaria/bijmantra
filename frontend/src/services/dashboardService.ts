import { useState, useEffect } from 'react';

/**
 * Twin-Engine Data Service Hook
 * Provides a standardized way to switch between Mock Data (offline/development) 
 * and Real Data (production/API), conforming to the BijMantra PWA standards.
 */
export function useDashboardService<T>(
    fetchRealData: () => Promise<T>,
    fetchMockData: () => Promise<T>,
    dependencies: any[] = []
) {
    const [data, setData] = useState<T | null>(null);
    const [loading, setLoading] = useState<boolean>(true);
    const [error, setError] = useState<Error | null>(null);

    useEffect(() => {
        let mounted = true;

        async function loadData() {
            setLoading(true);
            setError(null);

            try {
                // Here we could check a global offline flag, 
                // network status, or local storage configuration.
                const isOffline = !navigator.onLine;

                let result: T;
                if (isOffline) {
                    console.log('[useDashboardService] Offline mode: loading mock data');
                    result = await fetchMockData();
                } else {
                    try {
                        result = await fetchRealData();
                    } catch (e) {
                        console.warn('[useDashboardService] Real API failed, falling back to mock data', e);
                        result = await fetchMockData();
                    }
                }

                if (mounted) {
                    setData(result);
                }
            } catch (e: any) {
                if (mounted) {
                    setError(e);
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
    }, dependencies);

    return { data, loading, error };
}
