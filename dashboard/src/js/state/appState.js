// Application state management
const state = {
    viewMode: 'monthly', // 'monthly' or 'quarterly'
    currentPeriodIndex: null, // null = latest, -1 = YTD, -2 = LTM
    dateRangeStart: null,
    dateRangeEnd: null,
    currency: 'usd', // 'usd' or 'eur'
    summaryViewMode: 'period', // 'period' or 'range'
    currentPage: 'dashboard', // 'dashboard' or 'data'
    data: null
};

const listeners = [];

export function getState() {
    return { ...state };
}

export function setState(updates) {
    console.log('setState called with:', updates);
    console.log('State before:', { ...state });
    Object.assign(state, updates);
    console.log('State after:', { ...state });
    notifyListeners();
}

export function subscribe(listener) {
    listeners.push(listener);
    return () => {
        const index = listeners.indexOf(listener);
        if (index > -1) listeners.splice(index, 1);
    };
}

function notifyListeners() {
    listeners.forEach(listener => listener(state));
}

// Specific state updaters
export function setCurrency(currency) {
    setState({ currency });
}

export function setViewMode(mode) {
    setState({ viewMode: mode });
}

export function setDateRange(start, end) {
    setState({ dateRangeStart: start, dateRangeEnd: end });
}

export function setCurrentPeriod(index) {
    setState({ currentPeriodIndex: index });
}

export function setSummaryViewMode(mode) {
    setState({ summaryViewMode: mode });
}

export function setCurrentPage(page) {
    console.log('Setting page to:', page);
    setState({ currentPage: page });
}
