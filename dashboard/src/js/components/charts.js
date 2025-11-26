import { Chart, registerables } from 'chart.js';
import ChartDataLabels from 'chartjs-plugin-datalabels';
import { getState } from '../state/appState.js';
import { formatCurrency, formatPercent, formatAxisNumber, formatCurrencyFull } from '../utils/formatters.js';

// Register Chart.js components
Chart.register(...registerables, ChartDataLabels);

const chartInstances = {};

// Shared chart styling configuration
const getCommonLegendConfig = () => ({
    display: true,
    position: 'top',
    labels: {
        font: { size: 12, weight: '500' },
        padding: 16,
        usePointStyle: true,
        color: '#013E3F',
        boxWidth: 8,
        boxHeight: 8
    }
});

const getCommonTooltipConfig = (currency) => ({
    backgroundColor: 'rgba(17, 24, 39, 0.96)',
    padding: 14,
    titleFont: { size: 13, weight: '600' },
    bodyFont: { size: 12, weight: '400' },
    cornerRadius: 8,
    displayColors: true,
    boxPadding: 6
});

const getCommonAxisConfig = () => ({
    ticks: {
        font: { size: 11, weight: '400' },
        color: '#9ca3af'
    },
    grid: {
        color: 'rgba(0, 0, 0, 0.04)',
        drawBorder: false
    }
});

// Smart data labels configuration for line charts
const getLineChartLabelsConfig = (formatter, dataLength) => ({
    display: (context) => {
        // Show labels only for first, last, and every other point if more than 5 points
        const index = context.dataIndex;
        if (dataLength <= 5) return true;
        if (dataLength <= 7) return index === 0 || index === dataLength - 1 || index === Math.floor(dataLength / 2);
        return index === 0 || index === dataLength - 1 || index % 2 === 0;
    },
    align: 'top',
    anchor: 'end',
    offset: 4,
    clamp: true,
    clip: false,
    formatter: formatter,
    font: {
        size: 10,
        weight: '400'
    },
    color: '#6b7280',
    backgroundColor: (context) => {
        return 'rgba(255, 255, 255, 0.8)';
    },
    borderRadius: 3,
    padding: { top: 2, bottom: 2, left: 4, right: 4 }
});

// Data labels for bar charts
const getBarChartLabelsConfig = (formatter, showInside = false) => ({
    display: true,
    anchor: showInside ? 'center' : 'end',
    align: showInside ? 'center' : 'top',
    offset: showInside ? 0 : 2,
    clamp: true,
    formatter: formatter,
    font: {
        size: 10,
        weight: '400'
    },
    color: showInside ? '#ffffff' : '#6b7280'
});

export function renderCharts(container, data) {
    const state = getState();
    console.log('Rendering charts with currency:', state.currency);

    container.innerHTML = `
        <h2 class="section-title">Performance Analytics</h2>
        <div class="charts-grid">
            <div class="chart-container full-width large">
                <div class="chart-title">GMV vs Funded Amount Trend</div>
                <div class="chart-subtitle">Tracks relationship between total GMV and funded amount over time</div>
                <div class="chart-wrapper">
                    <canvas id="gmvFundedChart"></canvas>
                </div>
            </div>

            <div class="chart-container">
                <div class="chart-title">Revenue Streams Breakdown</div>
                <div class="chart-subtitle">Monthly breakdown of all revenue streams</div>
                <div class="chart-wrapper">
                    <canvas id="revenueBreakdownChart"></canvas>
                </div>
            </div>

            <div class="chart-container">
                <div class="chart-title">Profitability Waterfall</div>
                <div class="chart-subtitle">How gross revenue flows to net margin</div>
                <div class="chart-wrapper">
                    <canvas id="waterfallChart"></canvas>
                </div>
            </div>

            <div class="chart-container">
                <div class="chart-title">Portfolio Health Metrics</div>
                <div class="chart-subtitle">Key risk indicators for portfolio monitoring</div>
                <div class="chart-wrapper">
                    <canvas id="portfolioHealthChart"></canvas>
                </div>
            </div>

            <div class="chart-container">
                <div class="chart-title">Cash Drag Trend Analysis</div>
                <div class="chart-subtitle">Capital efficiency with target thresholds</div>
                <div class="chart-wrapper">
                    <canvas id="cashDragChart"></canvas>
                </div>
            </div>

            <div class="chart-container">
                <div class="chart-title">Operational Volume Metrics</div>
                <div class="chart-subtitle">Tracks operational volumes and efficiency ratio</div>
                <div class="chart-wrapper">
                    <canvas id="operationalChart"></canvas>
                </div>
            </div>
        </div>
    `;

    // Create charts
    createGMVFundedChart(data, state);
    createRevenueBreakdownChart(data, state);
    createWaterfallChart(data, state);
    createPortfolioHealthChart(data, state);
    createCashDragChart(data, state);
    createOperationalChart(data, state);
}

function createGMVFundedChart(data, state) {
    const ctx = document.getElementById('gmvFundedChart');
    if (!ctx) return;

    const periods = data.periods || [];
    const currencyData = state.currency === 'usd' ? data.values_usd : data.values_eur;
    const currency = state.currency;

    chartInstances.gmvFunded = new Chart(ctx, {
        type: 'line',
        data: {
            labels: periods,
            datasets: [
                {
                    label: 'GMV',
                    data: currencyData?.GMV || [],
                    borderColor: '#013E3F',
                    backgroundColor: 'rgba(1, 62, 63, 0.1)',
                    borderWidth: 3,
                    fill: true,
                    tension: 0.4,
                    pointRadius: 5,
                    pointHoverRadius: 7
                },
                {
                    label: 'Funded Amount',
                    data: currencyData?.['Funded Amount'] || [],
                    borderColor: '#009091',
                    backgroundColor: 'rgba(0, 144, 145, 0.1)',
                    borderWidth: 3,
                    fill: true,
                    tension: 0.4,
                    pointRadius: 5,
                    pointHoverRadius: 7
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                datalabels: getLineChartLabelsConfig(
                    (value) => value ? formatCurrency(value, currency, 1) : '',
                    periods.length
                ),
                legend: {
                    ...getCommonLegendConfig(),
                    labels: {
                        ...getCommonLegendConfig().labels,
                        pointStyle: 'circle'
                    }
                },
                tooltip: {
                    ...getCommonTooltipConfig(currency),
                    callbacks: {
                        label: (context) => {
                            const label = context.dataset.label || '';
                            const value = formatCurrencyFull(context.parsed.y, currency);
                            return `${label}: ${value}`;
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        callback: (value) => formatCurrency(value, currency, 0),
                        font: { size: 11, weight: '400' },
                        color: '#9ca3af'
                    },
                    grid: {
                        color: 'rgba(0, 0, 0, 0.04)',
                        drawBorder: false
                    }
                },
                x: {
                    ticks: {
                        font: { size: 11, weight: '400' },
                        color: '#9ca3af'
                    },
                    grid: {
                        display: false,
                        drawBorder: false
                    }
                }
            }
        }
    });
}

function createRevenueBreakdownChart(data, state) {
    const ctx = document.getElementById('revenueBreakdownChart');
    if (!ctx) return;

    const periods = data.periods || [];
    const currencyData = state.currency === 'usd' ? data.values_usd : data.values_eur;
    const currency = state.currency;

    chartInstances.revenueBreakdown = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: periods,
            datasets: [
                {
                    label: 'Arrangement Fees',
                    data: currencyData?.['Arrangement Fees'] || [],
                    backgroundColor: '#013E3F'
                },
                {
                    label: 'Logistic Fees',
                    data: currencyData?.['Logistic Fees'] || [],
                    backgroundColor: '#009091'
                },
                {
                    label: 'Accrued Interests',
                    data: currencyData?.['Accrued Interests'] || [],
                    backgroundColor: '#20D9DC'
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                datalabels: {
                    display: function(context) {
                        // Calculate total for this bar (sum of all datasets at this index)
                        const dataIndex = context.dataIndex;
                        const chart = context.chart;
                        let total = 0;
                        chart.data.datasets.forEach(dataset => {
                            total += dataset.data[dataIndex] || 0;
                        });

                        // Hide label if this value is less than 10% of total
                        const value = context.dataset.data[dataIndex] || 0;
                        const percentage = total > 0 ? (value / total) * 100 : 0;
                        return percentage >= 10;
                    },
                    formatter: (value) => value ? formatCurrency(value, currency, 1) : '',
                    color: '#FFFFFF',
                    font: {
                        size: 10,
                        weight: '500'
                    },
                    anchor: 'center',
                    align: 'center'
                },
                legend: {
                    ...getCommonLegendConfig(),
                    labels: {
                        ...getCommonLegendConfig().labels,
                        pointStyle: 'rect'
                    }
                },
                tooltip: {
                    ...getCommonTooltipConfig(currency),
                    callbacks: {
                        label: (context) => {
                            const label = context.dataset.label || '';
                            const value = formatCurrencyFull(context.parsed.y, currency);
                            return `${label}: ${value}`;
                        },
                        footer: (tooltipItems) => {
                            const total = tooltipItems.reduce((sum, item) => sum + item.parsed.y, 0);
                            return `Total: ${formatCurrencyFull(total, currency)}`;
                        }
                    }
                }
            },
            scales: {
                x: {
                    stacked: true,
                    ticks: {
                        font: { size: 11, weight: '400' },
                        color: '#9ca3af'
                    },
                    grid: {
                        display: false,
                        drawBorder: false
                    }
                },
                y: {
                    stacked: true,
                    beginAtZero: true,
                    ticks: {
                        callback: (value) => formatCurrency(value, currency, 0),
                        font: { size: 11, weight: '400' },
                        color: '#9ca3af'
                    },
                    grid: {
                        color: 'rgba(0, 0, 0, 0.04)',
                        drawBorder: false
                    }
                }
            }
        }
    });
}

function createWaterfallChart(data, state) {
    const ctx = document.getElementById('waterfallChart');
    if (!ctx) return;

    const currencyData = state.currency === 'usd' ? data.values_usd : data.values_eur;
    const currency = state.currency;
    const lastIdx = data.periods.length - 1;

    // Calculate latest period values
    const arrangementFees = (currencyData?.['Arrangement Fees']?.[lastIdx] || 0);
    const logisticFees = (currencyData?.['Logistic Fees']?.[lastIdx] || 0);
    const accruedInterests = (currencyData?.['Accrued Interests']?.[lastIdx] || 0);
    const totalRevenue = arrangementFees + logisticFees + accruedInterests;

    const logisticCosts = (currencyData?.['Logistic Costs']?.[lastIdx] || 0);
    const insuranceCosts = (currencyData?.['Cargo Insurance Costs']?.[lastIdx] || 0);
    const costOfFunds = (currencyData?.['Cost of Funds (Accrued)']?.[lastIdx] || 0);
    const docsCosts = (currencyData?.['Costs of Docs Delivery']?.[lastIdx] || 0);
    const warehouseCosts = (currencyData?.['Warehouse Destination Costs']?.[lastIdx] || 0);
    const totalCosts = logisticCosts + insuranceCosts + costOfFunds + docsCosts + warehouseCosts;

    const netMargin = totalRevenue - totalCosts;

    chartInstances.waterfall = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: ['Gross Revenue', 'Total Costs', 'Net Margin'],
            datasets: [{
                label: `P&L (${data.periods[lastIdx]})`,
                data: [totalRevenue, -totalCosts, netMargin],
                backgroundColor: ['#009091', '#F4845F', '#013E3F']
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                datalabels: getBarChartLabelsConfig(
                    (value) => formatCurrency(Math.abs(value), currency, 1),
                    false
                ),
                legend: {
                    display: false
                },
                tooltip: {
                    ...getCommonTooltipConfig(currency),
                    callbacks: {
                        label: (context) => {
                            const value = Math.abs(context.parsed.y);
                            return `${context.label}: ${formatCurrencyFull(value, currency)}`;
                        }
                    }
                }
            },
            scales: {
                y: {
                    ticks: {
                        callback: (value) => formatCurrency(value, currency, 0),
                        font: { size: 11, weight: '400' },
                        color: '#9ca3af'
                    },
                    grid: {
                        color: 'rgba(0, 0, 0, 0.04)',
                        drawBorder: false
                    }
                },
                x: {
                    ticks: {
                        font: { size: 11, weight: '500' },
                        color: '#013E3F'
                    },
                    grid: {
                        display: false,
                        drawBorder: false
                    }
                }
            }
        }
    });
}

function createPortfolioHealthChart(data, state) {
    const ctx = document.getElementById('portfolioHealthChart');
    if (!ctx) return;

    const periods = data.periods || [];
    const currencyData = state.currency === 'usd' ? data.values_usd : data.values_eur;
    const currency = state.currency;

    chartInstances.portfolioHealth = new Chart(ctx, {
        type: 'line',
        data: {
            labels: periods,
            datasets: [{
                label: '% GMV Insured',
                data: currencyData?.['% GMV Insured'] || [],
                borderColor: '#013E3F',
                backgroundColor: 'rgba(1, 62, 63, 0.1)',
                borderWidth: 3,
                fill: true,
                tension: 0.4,
                pointRadius: 5,
                pointHoverRadius: 7
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                datalabels: getLineChartLabelsConfig(
                    (value) => value ? formatPercent(value, 2) : '',
                    periods.length
                ),
                legend: {
                    ...getCommonLegendConfig(),
                    labels: {
                        ...getCommonLegendConfig().labels,
                        pointStyle: 'circle'
                    }
                },
                tooltip: {
                    ...getCommonTooltipConfig(currency),
                    callbacks: {
                        label: (context) => {
                            return `${context.dataset.label}: ${formatPercent(context.parsed.y, 2)}`;
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    grace: '10%',
                    ticks: {
                        callback: (value) => formatPercent(value, 2),
                        font: { size: 11, weight: '400' },
                        color: '#9ca3af'
                    },
                    grid: {
                        color: 'rgba(0, 0, 0, 0.04)',
                        drawBorder: false
                    }
                },
                x: {
                    ticks: {
                        font: { size: 11, weight: '400' },
                        color: '#9ca3af'
                    },
                    grid: {
                        display: false,
                        drawBorder: false
                    }
                }
            }
        }
    });
}

function createCashDragChart(data, state) {
    const ctx = document.getElementById('cashDragChart');
    if (!ctx) return;

    const periods = data.periods || [];
    const currencyData = state.currency === 'usd' ? data.values_usd : data.values_eur;
    const currency = state.currency;

    // Cash Drag is stored as decimal (0-1 range), convert to percentage (0-100 range)
    const cashDragData = (currencyData?.['Cash Drag'] || []).map(value => value * 100);

    chartInstances.cashDrag = new Chart(ctx, {
        type: 'line',
        data: {
            labels: periods,
            datasets: [
                {
                    label: 'Cash Drag %',
                    data: cashDragData,
                    borderColor: '#009091',
                    backgroundColor: 'rgba(0, 144, 145, 0.1)',
                    borderWidth: 3,
                    fill: true,
                    tension: 0.4,
                    pointRadius: 5,
                    pointHoverRadius: 7
                },
                {
                    label: 'Target (15%)',
                    data: Array(periods.length).fill(15),
                    borderColor: '#FF9800',
                    backgroundColor: 'transparent',
                    borderWidth: 2,
                    borderDash: [8, 4],
                    pointRadius: 0,
                    pointHoverRadius: 0
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                datalabels: {
                    ...getLineChartLabelsConfig(
                        (value, context) => {
                            // Only show labels for Cash Drag %, not the target line
                            if (context.datasetIndex === 0 && value !== null) {
                                return formatPercent(value, 1);
                            }
                            return '';
                        },
                        periods.length
                    ),
                    display: (context) => {
                        // Hide labels for target line dataset
                        if (context.datasetIndex !== 0) return false;
                        // Use smart display logic for actual data
                        const index = context.dataIndex;
                        const dataLength = periods.length;
                        if (dataLength <= 5) return true;
                        if (dataLength <= 7) return index === 0 || index === dataLength - 1 || index === Math.floor(dataLength / 2);
                        return index === 0 || index === dataLength - 1 || index % 2 === 0;
                    }
                },
                legend: {
                    ...getCommonLegendConfig(),
                    labels: {
                        ...getCommonLegendConfig().labels,
                        pointStyle: 'line',
                        boxWidth: 20,
                        boxHeight: 2
                    }
                },
                tooltip: {
                    ...getCommonTooltipConfig(currency),
                    callbacks: {
                        label: (context) => {
                            const value = context.parsed.y;
                            return `${context.dataset.label}: ${formatPercent(value, 2)}`;
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    grace: '10%',
                    ticks: {
                        callback: (value) => formatPercent(value, 0),
                        font: { size: 11, weight: '400' },
                        color: '#9ca3af'
                    },
                    grid: {
                        color: 'rgba(0, 0, 0, 0.04)',
                        drawBorder: false
                    }
                },
                x: {
                    ticks: {
                        font: { size: 11, weight: '400' },
                        color: '#9ca3af'
                    },
                    grid: {
                        display: false,
                        drawBorder: false
                    }
                }
            }
        }
    });
}

function createOperationalChart(data, state) {
    const ctx = document.getElementById('operationalChart');
    if (!ctx) return;

    const periods = data.periods || [];
    const currencyData = state.currency === 'usd' ? data.values_usd : data.values_eur;
    const currency = state.currency;

    chartInstances.operational = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: periods,
            datasets: [
                {
                    label: '# Invoices',
                    data: currencyData?.['# Invoices'] || [],
                    backgroundColor: '#013E3F',
                    yAxisID: 'y'
                },
                {
                    label: '# Boxes',
                    data: currencyData?.['# Boxes'] || [],
                    backgroundColor: '#009091',
                    yAxisID: 'y'
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                datalabels: {
                    display: true,
                    formatter: (value) => value ? Math.round(value).toLocaleString() : '',
                    color: '#FFFFFF',
                    font: {
                        size: 10,
                        weight: '500'
                    },
                    anchor: 'center',
                    align: 'center'
                },
                legend: {
                    ...getCommonLegendConfig(),
                    labels: {
                        ...getCommonLegendConfig().labels,
                        pointStyle: 'rect'
                    }
                },
                tooltip: {
                    ...getCommonTooltipConfig(currency),
                    callbacks: {
                        label: (context) => {
                            const label = context.dataset.label || '';
                            const value = Math.round(context.parsed.y).toLocaleString();
                            return `${label}: ${value}`;
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        callback: (value) => Math.round(value).toLocaleString(),
                        font: { size: 11, weight: '400' },
                        color: '#9ca3af'
                    },
                    grid: {
                        color: 'rgba(0, 0, 0, 0.04)',
                        drawBorder: false
                    }
                },
                x: {
                    ticks: {
                        font: { size: 11, weight: '400' },
                        color: '#9ca3af'
                    },
                    grid: {
                        display: false,
                        drawBorder: false
                    }
                }
            }
        }
    });
}

export function destroyCharts() {
    Object.values(chartInstances).forEach(chart => chart?.destroy());
}
