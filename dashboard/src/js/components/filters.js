import { getState, setCurrency, setViewMode, setDateRange, setSummaryViewMode, subscribe } from '../state/appState.js';

export function renderFilters(container) {
    const state = getState();

    container.innerHTML = `
        <div class="filter-section">
            <div class="filter-controls">
                <!-- Currency Toggle -->
                <div class="filter-group">
                    <label class="filter-label">Currency</label>
                    <div class="toggle-group">
                        <button class="toggle-btn ${state.currency === 'usd' ? 'active' : ''}"
                                data-currency="usd" id="usdBtn">
                            USD ($)
                        </button>
                        <button class="toggle-btn ${state.currency === 'eur' ? 'active' : ''}"
                                data-currency="eur" id="eurBtn">
                            EUR (€)
                        </button>
                    </div>
                </div>

                <!-- View Mode Toggle -->
                <div class="filter-group">
                    <label class="filter-label">View Mode</label>
                    <div class="toggle-group">
                        <button class="toggle-btn ${state.viewMode === 'monthly' ? 'active' : ''}"
                                data-view="monthly" id="monthlyViewBtn">
                            Monthly
                        </button>
                        <button class="toggle-btn ${state.viewMode === 'quarterly' ? 'active' : ''}"
                                data-view="quarterly" id="quarterlyViewBtn">
                            Quarterly
                        </button>
                    </div>
                </div>

                <!-- KPI Summary Mode -->
                <div class="filter-group">
                    <label class="filter-label">KPI Display Mode</label>
                    <div class="toggle-group">
                        <button class="toggle-btn ${state.summaryViewMode === 'period' ? 'active' : ''}"
                                data-summary="period" id="periodBtn">
                            Period Only
                        </button>
                        <button class="toggle-btn ${state.summaryViewMode === 'range' ? 'active' : ''}"
                                data-summary="range" id="rangeBtn">
                            Cumulative Data Range
                        </button>
                    </div>
                </div>

                <!-- Date Range -->
                <div class="filter-group">
                    <label class="filter-label">Date Range</label>
                    <div class="date-range-inputs">
                        <select id="filterStartMonth" class="filter-select">
                            <option value="">From (all)</option>
                        </select>
                        <span class="range-separator">→</span>
                        <select id="filterEndMonth" class="filter-select">
                            <option value="">To (all)</option>
                        </select>
                    </div>
                </div>

                <!-- Reset Button -->
                <div class="filter-group filter-actions">
                    <button class="btn-reset" id="resetBtn">
                        <span>↺</span>
                        <span>Reset</span>
                    </button>
                </div>
            </div>
        </div>
    `;

    // Populate date selects if data is available
    populateDateSelects();

    // Attach event listeners
    attachFilterListeners();
}

function populateDateSelects() {
    const state = getState();
    const data = state.data;

    if (!data || !data.periods) return;

    const startSelect = document.getElementById('filterStartMonth');
    const endSelect = document.getElementById('filterEndMonth');

    if (startSelect && endSelect) {
        data.periods.forEach((period, index) => {
            const startOption = document.createElement('option');
            startOption.value = index;
            startOption.textContent = period;
            startSelect.appendChild(startOption);

            const endOption = document.createElement('option');
            endOption.value = index;
            endOption.textContent = period;
            endSelect.appendChild(endOption);
        });
    }
}

function attachFilterListeners() {
    // Currency toggle
    document.getElementById('usdBtn')?.addEventListener('click', () => {
        console.log('USD clicked');
        setCurrency('usd');
    });

    document.getElementById('eurBtn')?.addEventListener('click', () => {
        console.log('EUR clicked');
        setCurrency('eur');
    });

    // View mode toggle
    document.getElementById('monthlyViewBtn')?.addEventListener('click', () => {
        console.log('Monthly clicked');
        setViewMode('monthly');
    });

    document.getElementById('quarterlyViewBtn')?.addEventListener('click', () => {
        console.log('Quarterly clicked');
        setViewMode('quarterly');
    });

    // Summary view mode toggle
    document.getElementById('periodBtn')?.addEventListener('click', () => {
        console.log('Single Period clicked');
        setSummaryViewMode('period');
    });

    document.getElementById('rangeBtn')?.addEventListener('click', () => {
        console.log('Cumulative clicked');
        setSummaryViewMode('range');
    });

    // Date range selects
    document.getElementById('filterStartMonth')?.addEventListener('change', (e) => {
        const state = getState();
        const newStart = e.target.value || null;
        console.log('Start month changed to:', newStart);
        setDateRange(newStart, state.dateRangeEnd);
    });

    document.getElementById('filterEndMonth')?.addEventListener('change', (e) => {
        const state = getState();
        const newEnd = e.target.value || null;
        console.log('End month changed to:', newEnd);
        setDateRange(state.dateRangeStart, newEnd);
    });

    // Reset button
    document.getElementById('resetBtn')?.addEventListener('click', () => {
        console.log('Reset clicked');

        // Reset select values
        const startSelect = document.getElementById('filterStartMonth');
        const endSelect = document.getElementById('filterEndMonth');
        if (startSelect) startSelect.value = '';
        if (endSelect) endSelect.value = '';

        setDateRange(null, null);
        setViewMode('monthly');
        setCurrency('usd');
    });
}
