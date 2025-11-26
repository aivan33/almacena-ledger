// Data service - handles loading and caching dashboard data
let cachedData = null;

export async function loadDashboardData(forceRefresh = false) {
    if (cachedData && !forceRefresh) {
        return cachedData;
    }

    try {
        const timestamp = new Date().getTime();
        const response = await fetch(`/data/dashboard_data.json?t=${timestamp}`);

        if (!response.ok) {
            throw new Error('Failed to load dashboard data');
        }

        cachedData = await response.json();
        return cachedData;
    } catch (error) {
        console.error('Error loading dashboard data:', error);
        throw error;
    }
}

export function clearCache() {
    cachedData = null;
}

export function getData() {
    return cachedData;
}
