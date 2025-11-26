// Data Tables component - comprehensive data view
import { formatCurrency, formatPercent, formatCurrencyFull } from '../utils/formatters.js';
import { getState } from '../state/appState.js';

export function renderDataTables(container, data) {
    const state = getState();
    const currencyData = state.currency === 'usd' ? data.values_usd : data.values_eur;
    const currency = state.currency;
    const symbol = currency === 'usd' ? '$' : '€';

    container.innerHTML = `
        <div class="data-tables-section">
            <div class="section-header">
                <h2 class="section-title">Complete Data Reference</h2>
                <p class="section-subtitle">All metrics across all periods in tabular format</p>
            </div>

            <div class="table-tabs">
                <button class="table-tab active" data-table="financial">Financial Metrics</button>
                <button class="table-tab" data-table="operational">Operational Metrics</button>
                <button class="table-tab" data-table="ratios">Ratios & Percentages</button>
            </div>

            <div class="table-views">
                <div id="financial-table" class="table-view active">
                    ${renderFinancialTable(data, currencyData, symbol)}
                </div>
                <div id="operational-table" class="table-view">
                    ${renderOperationalTable(data, currencyData)}
                </div>
                <div id="ratios-table" class="table-view">
                    ${renderRatiosTable(data, currencyData)}
                </div>
            </div>
        </div>
    `;

    // Add tab switching
    setupTableTabs(container);
}

function renderFinancialTable(data, currencyData, symbol) {
    const financialMetrics = [
        'GMV',
        'Funded Amount',
        'Arrangement Fees',
        'Logistic Fees',
        'Accrued Interests',
        'Logistic Costs',
        'Cargo Insurance Fees',
        'Cargo Insurance Costs',
        'Cost of Funds (Accrued)',
        'Costs of Docs Delivery',
        'Warehouse Destination Fees',
        'Warehouse Destination Costs',
        'Avg Portfolio Outstanding'
    ];

    return `
        <div class="table-container">
            <table class="data-table">
                <thead>
                    <tr>
                        <th>Metric</th>
                        ${data.periods.map(p => `<th class="number">${p}</th>`).join('')}
                    </tr>
                </thead>
                <tbody>
                    ${financialMetrics.map(metric => {
                        const values = currencyData?.[metric] || [];
                        return `
                            <tr>
                                <td><strong>${metric}</strong></td>
                                ${values.map(v => `<td class="number">${v != null ? symbol + v.toLocaleString(undefined, {minimumFractionDigits: 0, maximumFractionDigits: 0}) : '-'}</td>`).join('')}
                            </tr>
                        `;
                    }).join('')}
                </tbody>
            </table>
        </div>
    `;
}

function renderOperationalTable(data, currencyData) {
    const operationalMetrics = [
        '# Invoices',
        '# Boxes',
        'Avg Days Outstanding'
    ];

    return `
        <div class="table-container">
            <table class="data-table">
                <thead>
                    <tr>
                        <th>Metric</th>
                        ${data.periods.map(p => `<th class="number">${p}</th>`).join('')}
                    </tr>
                </thead>
                <tbody>
                    ${operationalMetrics.map(metric => {
                        const values = currencyData?.[metric] || [];
                        return `
                            <tr>
                                <td><strong>${metric}</strong></td>
                                ${values.map(v => `<td class="number">${v != null ? Math.round(v).toLocaleString() : '-'}</td>`).join('')}
                            </tr>
                        `;
                    }).join('')}
                </tbody>
            </table>
        </div>
    `;
}

function renderRatiosTable(data, currencyData) {
    const ratioMetrics = [
        '% GMV Insured',
        'Cash Drag',
        'exch_rate'
    ];

    return `
        <div class="table-container">
            <table class="data-table">
                <thead>
                    <tr>
                        <th>Metric</th>
                        ${data.periods.map(p => `<th class="number">${p}</th>`).join('')}
                    </tr>
                </thead>
                <tbody>
                    ${ratioMetrics.map(metric => {
                        const values = currencyData?.[metric] || [];
                        const isPercent = metric.includes('%') || metric === 'Cash Drag';
                        const isCashDrag = metric === 'Cash Drag';
                        return `
                            <tr>
                                <td><strong>${metric}</strong></td>
                                ${values.map(v => {
                                    if (v == null) return '<td class="number">-</td>';
                                    // Cash Drag is stored as decimal (0-1), multiply by 100
                                    if (isCashDrag) return `<td class="number">${(v * 100).toFixed(2)}%</td>`;
                                    if (isPercent) return `<td class="number">${v.toFixed(2)}%</td>`;
                                    return `<td class="number">${v.toFixed(4)}</td>`;
                                }).join('')}
                            </tr>
                        `;
                    }).join('')}
                </tbody>
            </table>
        </div>
    `;
}

function setupTableTabs(container) {
    const tabs = container.querySelectorAll('.table-tab');
    const views = container.querySelectorAll('.table-view');

    tabs.forEach(tab => {
        tab.addEventListener('click', () => {
            const tableType = tab.dataset.table;

            // Update active tab
            tabs.forEach(t => t.classList.remove('active'));
            tab.classList.add('active');

            // Update active view
            views.forEach(v => v.classList.remove('active'));
            const targetView = container.querySelector(`#${tableType}-table`);
            if (targetView) {
                targetView.classList.add('active');
            }
        });
    });
}
