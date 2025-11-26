import { getState } from '../state/appState.js';
import { formatCurrency, formatPercent } from '../utils/formatters.js';

export function renderKPIs(container, data) {
    const state = getState();
    const currencyData = state.currency === 'usd' ? data.values_usd : data.values_eur;
    const symbol = state.currency === 'usd' ? '$' : '€';
    const periods = data.periods || [];

    // Calculate KPI values and MoM changes based on view mode
    const kpiData = {};
    const momChanges = {};

    if (currencyData) {
        Object.keys(currencyData).forEach(metric => {
            const values = currencyData[metric];

            if (state.summaryViewMode === 'range') {
                // Cumulative: Sum all values in the range
                kpiData[metric] = values.reduce((sum, val) => sum + (val || 0), 0);
                // No MoM for cumulative view
                momChanges[metric] = null;
            } else {
                // Single Period: Show latest value only
                const currentValue = values[values.length - 1];
                const previousValue = values[values.length - 2];

                kpiData[metric] = currentValue;

                // Calculate MoM percentage change
                if (previousValue != null && currentValue != null && previousValue !== 0) {
                    momChanges[metric] = ((currentValue - previousValue) / Math.abs(previousValue)) * 100;
                } else {
                    momChanges[metric] = null;
                }
            }
        });
    }

    // Display period info
    const periodInfo = state.summaryViewMode === 'range'
        ? `Total (${periods.length} periods)`
        : periods[periods.length - 1] || 'Latest';

    container.innerHTML = `
        <div class="kpi-section">
            <h2 class="section-title">Executive Summary <span class="period-badge">${periodInfo}</span></h2>
            <div class="kpi-grid">
                ${createKPICard('GMV', kpiData.GMV, symbol, 'primary', momChanges.GMV, true)}
                ${createKPICard('Funded Amount', kpiData['Funded Amount'], symbol, 'secondary', momChanges['Funded Amount'], true)}
                ${createKPICard('# Invoices', kpiData['# Invoices'], '', 'accent', momChanges['# Invoices'], true)}
                ${createKPICard('# Boxes', kpiData['# Boxes'], '', 'accent', momChanges['# Boxes'], true)}
                ${createKPICard('Avg Days Outstanding', kpiData['Avg Days Outstanding'], 'days', 'neutral', momChanges['Avg Days Outstanding'], false)}
                ${createKPICard('Cash Drag', kpiData['Cash Drag'] ? kpiData['Cash Drag'] * 100 : null, '%', 'warning', momChanges['Cash Drag'] ? momChanges['Cash Drag'] : null, false)}
            </div>
        </div>
    `;
}

function createKPICard(title, value, suffix, variant = 'primary', momChange = null, increaseIsGood = true) {
    const formattedValue = formatValue(value, suffix);

    // Format MoM change
    let trendHtml = '';
    if (momChange !== null && !isNaN(momChange)) {
        const isIncrease = momChange >= 0;
        const trendIndicator = isIncrease ? '↗' : '↘';

        // Determine if this change is good or bad based on the metric
        // For metrics where increase is good (GMV, Funded Amount, etc.): green for up, red for down
        // For metrics where decrease is good (Cash Drag, Days Outstanding): red for up, green for down
        let isGoodChange;
        if (increaseIsGood) {
            isGoodChange = isIncrease;  // Increase is good
        } else {
            isGoodChange = !isIncrease;  // Decrease is good
        }

        const trendClass = isGoodChange ? 'trend-up' : 'trend-down';
        const sign = isIncrease ? '+' : '';

        trendHtml = `
            <div class="kpi-trend ${trendClass}">
                <span class="trend-indicator">${trendIndicator}</span>
                <span class="trend-value">${sign}${momChange.toFixed(1)}%</span>
                <span class="trend-period">vs last period</span>
            </div>
        `;
    } else {
        trendHtml = `
            <div class="kpi-trend">
                <span class="trend-value">—</span>
                <span class="trend-period">No prior data</span>
            </div>
        `;
    }

    return `
        <div class="kpi-card kpi-${variant}">
            <div class="kpi-label">${title}</div>
            <div class="kpi-value">${formattedValue}</div>
            ${trendHtml}
        </div>
    `;
}

function formatValue(value, suffix) {
    if (value === null || value === undefined || isNaN(value)) return 'N/A';

    if (suffix === '$') {
        return formatCurrency(value, 'usd', 1);
    }

    if (suffix === '€') {
        return formatCurrency(value, 'eur', 1);
    }

    if (suffix === '%') {
        return formatPercent(value, 1);
    }

    if (suffix === 'days') {
        return `${Math.round(value)} ${suffix}`;
    }

    // Default number formatting (for counts like # Invoices, # Boxes)
    return Math.round(value).toLocaleString();
}
