/**
 * Main dashboard application with design tokens integration
 */

import {
  CHART_COLORS,
  createLineChartConfig,
  createBarChartConfig,
  createWaterfallChartConfig,
  createCashflowChartConfig,
  createMixedChartConfig,
  formatCurrency,
  formatPercentage,
  formatAxisValue
} from './charts/chartConfig.js';

// Global state
let dashboardData = null;
let currentCurrency = 'EUR'; // EUR or USD
let charts = {}; // Store chart instances

/**
 * Initialize the dashboard
 */
document.addEventListener('DOMContentLoaded', async () => {
  try {
    await loadDashboardData();
    loadUserInfo();
    setupEventListeners();
    renderDashboard();
  } catch (error) {
    console.error('Failed to initialize dashboard:', error);
    showError('Failed to load dashboard data. Please refresh the page.');
  }
});

/**
 * Load dashboard data from JSON file
 */
async function loadDashboardData() {
  try {
    // Try to load from public directory first
    let response = await fetch('/data/processed/dashboard_data.json');

    if (!response.ok) {
      console.warn('Data file not found, using mock data');
      dashboardData = getMockData();
      return;
    }

    dashboardData = await response.json();
    console.log('Dashboard data loaded successfully', dashboardData);
  } catch (error) {
    console.error('Error loading dashboard data:', error);
    // Fallback to mock data if file doesn't exist
    dashboardData = getMockData();
  }
}

/**
 * Load user info (mock for now)
 */
function loadUserInfo() {
  document.getElementById('user-email').textContent = 'Demo User';
  document.getElementById('user-role').textContent = 'VIEWER';
}

/**
 * Setup event listeners
 */
function setupEventListeners() {
  // Logout button
  document.getElementById('logout-btn')?.addEventListener('click', () => {
    console.log('Logout clicked');
  });

  // Currency switcher (will be added to HTML)
  document.querySelectorAll('.currency-btn').forEach(btn => {
    btn.addEventListener('click', (e) => {
      const currency = e.target.dataset.currency;
      if (currency && currency !== currentCurrency) {
        currentCurrency = currency;
        updateCurrencySwitcher();
        renderDashboard();
      }
    });
  });

  // Refresh button (will be added to HTML)
  document.getElementById('refresh-btn')?.addEventListener('click', async () => {
    await loadDashboardData();
    renderDashboard();
  });
}

/**
 * Update currency switcher UI
 */
function updateCurrencySwitcher() {
  document.querySelectorAll('.currency-btn').forEach(btn => {
    if (btn.dataset.currency === currentCurrency) {
      btn.classList.add('active');
    } else {
      btn.classList.remove('active');
    }
  });
}

/**
 * Render entire dashboard
 */
function renderDashboard() {
  if (!dashboardData) {
    console.error('No dashboard data available');
    return;
  }

  renderKPIs();
  renderCharts();
  renderDataTable();
}

/**
 * Render KPI cards
 */
function renderKPIs() {
  const values = currentCurrency === 'EUR' ? dashboardData.values_eur : dashboardData.values_usd;
  const periods = dashboardData.periods;
  const latest = periods.length - 1;
  const prev = latest - 1;

  // GMV
  renderKPI(
    'kpi-gmv',
    'kpi-gmv-change',
    values['GMV'][latest],
    values['GMV'][prev],
    'GMV',
    currentCurrency,
    true
  );

  // Funded Amount
  renderKPI(
    'kpi-funded',
    'kpi-funded-change',
    values['Funded Amount'][latest],
    values['Funded Amount'][prev],
    'Funded Amount',
    currentCurrency,
    true
  );

  // Avg Days Outstanding
  renderKPI(
    'kpi-days',
    'kpi-days-change',
    values['Avg Days Outstanding'][latest],
    values['Avg Days Outstanding'][prev],
    'Avg Days Outstanding',
    null,
    false,
    true // Lower is better
  );

  // Number of Invoices
  renderKPI(
    'kpi-invoices',
    'kpi-invoices-change',
    values['# Invoices'][latest],
    values['# Invoices'][prev],
    '# Invoices',
    null,
    false
  );
}

/**
 * Render individual KPI
 */
function renderKPI(valueId, changeId, currentValue, previousValue, metric, currency, isCurrency, lowerIsBetter = false) {
  const valueEl = document.getElementById(valueId);
  const changeEl = document.getElementById(changeId);

  if (!valueEl || !changeEl) return;

  // Format value
  if (isCurrency) {
    valueEl.textContent = formatCurrency(currentValue, currency);
  } else {
    valueEl.textContent = Math.round(currentValue).toLocaleString();
  }

  // Calculate change
  const change = currentValue - previousValue;
  const changePercent = (change / previousValue * 100).toFixed(1);

  // Determine if positive or negative
  let isPositive;
  if (lowerIsBetter) {
    isPositive = change < 0;
  } else {
    isPositive = change > 0;
  }

  // Format change text
  let changeText;
  if (isCurrency) {
    changeText = `${change > 0 ? '+' : ''}${changePercent}% MoM`;
  } else if (metric === 'Avg Days Outstanding') {
    changeText = `${change > 0 ? '+' : ''}${change.toFixed(1)} days MoM`;
  } else {
    changeText = `${change > 0 ? '+' : ''}${changePercent}% MoM`;
  }

  changeEl.textContent = changeText;
  changeEl.className = `kpi-change ${isPositive ? 'positive' : 'negative'}`;
}

/**
 * Render all charts
 */
function renderCharts() {
  const values = currentCurrency === 'EUR' ? dashboardData.values_eur : dashboardData.values_usd;
  const periods = dashboardData.periods;

  // Destroy existing charts
  Object.values(charts).forEach(chart => chart?.destroy());
  charts = {};

  // GMV Trend (Line Chart)
  charts.gmv = createChart(
    'chart-gmv',
    createLineChartConfig(
      periods,
      [{
        label: `GMV (${currentCurrency})`,
        data: values['GMV'],
        color: CHART_COLORS.series[0]
      }],
      {
        plugins: {
          tooltip: {
            callbacks: {
              label: (context) => formatCurrency(context.parsed.y, currentCurrency)
            }
          }
        },
        scales: {
          y: {
            ticks: {
              callback: (value) => formatCurrency(value, currentCurrency, true)
            }
          }
        }
      }
    )
  );

  // Funded Amount Trend (Line Chart)
  charts.funded = createChart(
    'chart-funded',
    createLineChartConfig(
      periods,
      [{
        label: `Funded Amount (${currentCurrency})`,
        data: values['Funded Amount'],
        color: CHART_COLORS.series[1]
      }],
      {
        plugins: {
          tooltip: {
            callbacks: {
              label: (context) => formatCurrency(context.parsed.y, currentCurrency)
            }
          }
        },
        scales: {
          y: {
            ticks: {
              callback: (value) => formatCurrency(value, currentCurrency, true)
            }
          }
        }
      }
    )
  );

  // Days Outstanding (Line Chart)
  charts.days = createChart(
    'chart-days',
    createLineChartConfig(
      periods,
      [{
        label: 'Avg Days Outstanding',
        data: values['Avg Days Outstanding'],
        color: CHART_COLORS.series[4]
      }],
      {
        plugins: {
          tooltip: {
            callbacks: {
              label: (context) => `${context.parsed.y.toFixed(1)} days`
            }
          }
        }
      }
    )
  );

  // Invoice Count (Bar Chart)
  charts.invoices = createChart(
    'chart-invoices',
    createBarChartConfig(
      periods,
      [{
        label: '# Invoices',
        data: values['# Invoices'],
        color: CHART_COLORS.series[2]
      }]
    )
  );

  // Revenue Breakdown (Stacked Bar Chart) - if container exists
  if (document.getElementById('chart-revenue-breakdown')) {
    charts.revenueBreakdown = createChart(
      'chart-revenue-breakdown',
      createBarChartConfig(
        periods,
        [
          {
            label: 'Arrangement Fees',
            data: values['Arrangement Fees'],
            color: CHART_COLORS.series[0]
          },
          {
            label: 'Logistic Fees',
            data: values['Logistic Fees'],
            color: CHART_COLORS.series[1]
          },
          {
            label: 'Cargo Insurance Fees',
            data: values['Cargo Insurance Fees'],
            color: CHART_COLORS.series[2]
          },
          {
            label: 'Accrued Interests',
            data: values['Accrued Interests'],
            color: CHART_COLORS.series[3]
          }
        ],
        {
          plugins: {
            tooltip: {
              callbacks: {
                label: (context) => {
                  return `${context.dataset.label}: ${formatCurrency(context.parsed.y, currentCurrency)}`;
                }
              }
            }
          },
          scales: {
            x: {
              stacked: true
            },
            y: {
              stacked: true,
              ticks: {
                callback: (value) => formatCurrency(value, currentCurrency, true)
              }
            }
          }
        }
      )
    );
  }

  // Cost Analysis (Stacked Bar Chart) - if container exists
  if (document.getElementById('chart-cost-analysis')) {
    charts.costAnalysis = createChart(
      'chart-cost-analysis',
      createBarChartConfig(
        periods,
        [
          {
            label: 'Logistic Costs',
            data: values['Logistic Costs'],
            color: CHART_COLORS.series[0]
          },
          {
            label: 'Cargo Insurance Costs',
            data: values['Cargo Insurance Costs'],
            color: CHART_COLORS.series[1]
          },
          {
            label: 'Cost of Funds',
            data: values['Cost of Funds (Accrued)'],
            color: CHART_COLORS.series[2]
          }
        ],
        {
          plugins: {
            tooltip: {
              callbacks: {
                label: (context) => {
                  return `${context.dataset.label}: ${formatCurrency(context.parsed.y, currentCurrency)}`;
                }
              }
            }
          },
          scales: {
            x: {
              stacked: true
            },
            y: {
              stacked: true,
              ticks: {
                callback: (value) => formatCurrency(value, currentCurrency, true)
              }
            }
          }
        }
      )
    );
  }

  // GMV Insured % (Line Chart) - if container exists
  if (document.getElementById('chart-gmv-insured')) {
    charts.gmvInsured = createChart(
      'chart-gmv-insured',
      createLineChartConfig(
        periods,
        [{
          label: '% GMV Insured',
          data: values['% GMV Insured'],
          color: CHART_COLORS.series[5]
        }],
        {
          plugins: {
            tooltip: {
              callbacks: {
                label: (context) => formatPercentage(context.parsed.y)
              }
            }
          },
          scales: {
            y: {
              ticks: {
                callback: (value) => formatPercentage(value)
              }
            }
          }
        }
      )
    );
  }

  // Portfolio Outstanding (Mixed Chart) - if container exists
  if (document.getElementById('chart-portfolio')) {
    charts.portfolio = createChart(
      'chart-portfolio',
      createMixedChartConfig(
        periods,
        [
          {
            type: 'bar',
            label: `Avg Portfolio Outstanding (${currentCurrency})`,
            data: values['Avg Portfolio Outstanding'],
            color: CHART_COLORS.series[0]
          },
          {
            type: 'line',
            label: 'Cash Drag',
            data: values['Cash Drag'],
            color: CHART_COLORS.series[4],
            yAxisID: 'y1'
          }
        ],
        {
          plugins: {
            tooltip: {
              callbacks: {
                label: (context) => {
                  if (context.dataset.label.includes('Cash Drag')) {
                    return `Cash Drag: ${formatPercentage(context.parsed.y)}`;
                  }
                  return `${context.dataset.label}: ${formatCurrency(context.parsed.y, currentCurrency)}`;
                }
              }
            }
          },
          scales: {
            y: {
              type: 'linear',
              position: 'left',
              ticks: {
                callback: (value) => formatCurrency(value, currentCurrency, true)
              }
            },
            y1: {
              type: 'linear',
              position: 'right',
              grid: {
                drawOnChartArea: false
              },
              ticks: {
                callback: (value) => formatPercentage(value)
              }
            }
          }
        }
      )
    );
  }
}

/**
 * Create a chart instance
 */
function createChart(canvasId, config) {
  const canvas = document.getElementById(canvasId);
  if (!canvas) {
    console.warn(`Canvas element ${canvasId} not found`);
    return null;
  }

  const ctx = canvas.getContext('2d');
  return new Chart(ctx, config);
}

/**
 * Render data table
 */
function renderDataTable() {
  const tableContainer = document.getElementById('data-table');
  if (!tableContainer) return;

  const values = currentCurrency === 'EUR' ? dashboardData.values_eur : dashboardData.values_usd;
  const periods = dashboardData.periods;

  let html = '<div class="data-table"><table>';

  // Header
  html += '<thead><tr><th>Metric</th>';
  periods.forEach(period => {
    html += `<th>${period}</th>`;
  });
  html += '</tr></thead>';

  // Body
  html += '<tbody>';
  dashboardData.metrics.forEach(metric => {
    if (metric === 'exch_rate') return; // Skip exchange rate

    html += `<tr><td>${metric}</td>`;
    const metricValues = values[metric];

    if (metricValues) {
      metricValues.forEach(value => {
        if (value === null || value === undefined) {
          html += '<td>-</td>';
        } else if (metric.includes('%') || metric.includes('Cash Drag')) {
          html += `<td>${formatPercentage(value)}</td>`;
        } else if (metric === '# Invoices' || metric === '# Boxes') {
          html += `<td>${Math.round(value).toLocaleString()}</td>`;
        } else if (metric === 'Avg Days Outstanding') {
          html += `<td>${value.toFixed(1)}</td>`;
        } else {
          html += `<td>${formatCurrency(value, currentCurrency)}</td>`;
        }
      });
    }

    html += '</tr>';
  });
  html += '</tbody></table></div>';

  tableContainer.innerHTML = html;
}

/**
 * Show error message
 */
function showError(message) {
  const mainContent = document.querySelector('.dashboard-main .container-fluid');
  if (mainContent) {
    const errorDiv = document.createElement('div');
    errorDiv.className = 'error';
    errorDiv.textContent = message;
    mainContent.prepend(errorDiv);
  }
}

/**
 * Mock data fallback
 */
function getMockData() {
  return {
    periods: ['Jan-25', 'Feb-25', 'Mar-25', 'Apr-25', 'May-25', 'Jun-25', 'Jul-25', 'Aug-25', 'Sep-25'],
    metrics: ['GMV', 'Funded Amount', 'Avg Days Outstanding', '# Invoices'],
    values_eur: {
      'GMV': [11366988, 12629571, 6519261, 8279561, 12055656, 9512635, 10575952, 7358239, 12541404],
      'Funded Amount': [10120134, 11602936, 5726201, 7020395, 10774465, 8477332, 9090442, 5633906, 10421162],
      'Avg Days Outstanding': [17.5, 18.4, 27.1, 19.0, 18.4, 22.2, 17.7, 24.1, 17.3],
      '# Invoices': [54, 51, 25, 41, 55, 43, 53, 40, 64]
    },
    values_usd: {
      'GMV': [11763388, 13150220, 7042921, 9304590, 13594140, 10970744, 12359126, 8577261, 14714399],
      'Funded Amount': [10473052, 12081262, 6186159, 7889537, 12149449, 9776748, 10623148, 6567262, 12226791],
      'Avg Days Outstanding': [17.5, 18.4, 27.1, 19.0, 18.4, 22.2, 17.7, 24.1, 17.3],
      '# Invoices': [54, 51, 25, 41, 55, 43, 53, 40, 64]
    }
  };
}
