/**
 * Chart Configuration Utilities
 * Uses design tokens from tokens.json for consistent styling
 */

// Design Tokens (from CSS variables)
export const CHART_COLORS = {
  series: [
    '#013E3F', // chart-1
    '#006768', // chart-2
    '#009091', // chart-3
    '#20D9DC', // chart-4
    '#E1AA12', // chart-5
    '#F98F45'  // chart-6
  ],
  grid: 'rgba(102, 102, 102, 0.2)',
  dataLabels: '#222222',
  waterfall: {
    positive: '#4CAF50',
    negative: '#F44336',
    total: '#013E3F'
  },
  cashflow: {
    inflow: '#4CAF50',
    outflow: '#F44336',
    net: '#013E3F'
  },
  semantic: {
    success: '#4CAF50',
    warning: '#FFC107',
    error: '#F44336',
    info: '#2196F3'
  }
};

// Typography tokens
export const CHART_TYPOGRAPHY = {
  fontFamily: "'Segoe UI', Inter, Arial, sans-serif",
  fontSize: {
    xs: 12,
    sm: 14,
    md: 16,
    lg: 20
  },
  fontWeight: {
    regular: 400,
    medium: 500,
    bold: 700
  }
};

/**
 * Base chart configuration template (per tokens.json specifications)
 */
export const baseChartConfig = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: {
      display: true,
      position: 'top',
      labels: {
        font: {
          family: CHART_TYPOGRAPHY.fontFamily,
          size: CHART_TYPOGRAPHY.fontSize.sm,
          weight: CHART_TYPOGRAPHY.fontWeight.medium
        },
        color: CHART_COLORS.dataLabels,
        padding: 16,
        usePointStyle: true,
        pointStyle: 'circle'
      }
    },
    tooltip: {
      backgroundColor: 'rgba(0, 0, 0, 0.8)',
      titleFont: {
        family: CHART_TYPOGRAPHY.fontFamily,
        size: CHART_TYPOGRAPHY.fontSize.sm,
        weight: CHART_TYPOGRAPHY.fontWeight.medium
      },
      bodyFont: {
        family: CHART_TYPOGRAPHY.fontFamily,
        size: CHART_TYPOGRAPHY.fontSize.sm
      },
      padding: 12,
      cornerRadius: 4,
      displayColors: true
    },
    // Data labels enabled by default (per tokens.json)
    datalabels: {
      display: false, // Will be enabled per chart type as needed
      color: CHART_COLORS.dataLabels,
      font: {
        family: CHART_TYPOGRAPHY.fontFamily,
        size: CHART_TYPOGRAPHY.fontSize.xs,
        weight: CHART_TYPOGRAPHY.fontWeight.medium
      },
      align: 'end',
      anchor: 'end',
      formatter: (value) => {
        if (value >= 1000000) {
          return (value / 1000000).toFixed(1) + 'M';
        } else if (value >= 10000) {
          return (value / 1000).toFixed(0) + 'K';
        }
        return value.toFixed(0);
      }
    }
  },
  scales: {
    x: {
      grid: {
        color: CHART_COLORS.grid,
        drawBorder: false,
        // Dashed grid lines per tokens.json
        borderDash: [5, 5]
      },
      ticks: {
        font: {
          family: CHART_TYPOGRAPHY.fontFamily,
          size: CHART_TYPOGRAPHY.fontSize.sm
        },
        color: CHART_COLORS.dataLabels
      }
    },
    y: {
      grid: {
        color: CHART_COLORS.grid,
        drawBorder: false,
        // Dashed grid lines per tokens.json
        borderDash: [5, 5]
      },
      ticks: {
        font: {
          family: CHART_TYPOGRAPHY.fontFamily,
          size: CHART_TYPOGRAPHY.fontSize.sm
        },
        color: CHART_COLORS.dataLabels
      },
      beginAtZero: true
    }
  }
};

/**
 * Format large numbers for chart axes (K for thousands, M for millions)
 */
export function formatAxisValue(value, threshold = 10000) {
  if (Math.abs(value) >= 1000000) {
    return (value / 1000000).toFixed(1) + 'M';
  } else if (Math.abs(value) >= threshold) {
    return (value / 1000).toFixed(0) + 'K';
  }
  return value.toFixed(0);
}

/**
 * Format currency values
 */
export function formatCurrency(value, currency = 'EUR', compact = false) {
  if (compact && Math.abs(value) >= 1000000) {
    return `${currency === 'EUR' ? '€' : '$'}${(value / 1000000).toFixed(1)}M`;
  } else if (compact && Math.abs(value) >= 1000) {
    return `${currency === 'EUR' ? '€' : '$'}${(value / 1000).toFixed(0)}K`;
  }

  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: currency,
    minimumFractionDigits: 0,
    maximumFractionDigits: 0
  }).format(value);
}

/**
 * Format percentage values
 */
export function formatPercentage(value, decimals = 1) {
  return (value * 100).toFixed(decimals) + '%';
}

/**
 * Create line chart configuration
 */
export function createLineChartConfig(labels, datasets, options = {}) {
  const config = {
    type: 'line',
    data: {
      labels,
      datasets: datasets.map((dataset, index) => ({
        label: dataset.label,
        data: dataset.data,
        borderColor: dataset.color || CHART_COLORS.series[index % CHART_COLORS.series.length],
        backgroundColor: (dataset.color || CHART_COLORS.series[index % CHART_COLORS.series.length]) + '20',
        borderWidth: 3,
        tension: 0.4,
        fill: dataset.fill !== undefined ? dataset.fill : true,
        pointRadius: 5,
        pointHoverRadius: 7,
        pointBackgroundColor: dataset.color || CHART_COLORS.series[index % CHART_COLORS.series.length],
        pointBorderColor: '#FFFFFF',
        pointBorderWidth: 2,
        pointHoverBorderWidth: 3,
        ...dataset
      }))
    },
    options: {
      ...baseChartConfig,
      ...options
    }
  };

  return config;
}

/**
 * Create bar chart configuration
 */
export function createBarChartConfig(labels, datasets, options = {}) {
  const config = {
    type: 'bar',
    data: {
      labels,
      datasets: datasets.map((dataset, index) => ({
        label: dataset.label,
        data: dataset.data,
        backgroundColor: dataset.color || CHART_COLORS.series[index % CHART_COLORS.series.length],
        borderRadius: {
          topLeft: 8,
          topRight: 8,
          bottomLeft: 0,
          bottomRight: 0
        },
        borderSkipped: false,
        barThickness: 'flex',
        maxBarThickness: 60,
        ...dataset
      }))
    },
    options: {
      ...baseChartConfig,
      ...options
    }
  };

  return config;
}

/**
 * Create waterfall chart configuration
 */
export function createWaterfallChartConfig(labels, data, options = {}) {
  const backgroundColors = data.map(value => {
    if (value > 0) return CHART_COLORS.waterfall.positive;
    if (value < 0) return CHART_COLORS.waterfall.negative;
    return CHART_COLORS.waterfall.total;
  });

  const config = {
    type: 'bar',
    data: {
      labels,
      datasets: [{
        label: 'Value',
        data: data,
        backgroundColor: backgroundColors,
        borderRadius: {
          topLeft: 8,
          topRight: 8,
          bottomLeft: 0,
          bottomRight: 0
        },
        borderSkipped: false,
        barThickness: 'flex',
        maxBarThickness: 60
      }]
    },
    options: {
      ...baseChartConfig,
      plugins: {
        ...baseChartConfig.plugins,
        legend: {
          display: false
        },
        tooltip: {
          ...baseChartConfig.plugins.tooltip,
          callbacks: {
            label: (context) => {
              const value = context.parsed.y;
              return formatCurrency(value);
            }
          }
        }
      },
      scales: {
        ...baseChartConfig.scales,
        y: {
          ...baseChartConfig.scales.y,
          ticks: {
            ...baseChartConfig.scales.y.ticks,
            callback: (value) => formatAxisValue(value)
          }
        }
      },
      ...options
    }
  };

  return config;
}

/**
 * Create cashflow chart configuration (stacked bar chart)
 */
export function createCashflowChartConfig(labels, inflowData, outflowData, options = {}) {
  const config = {
    type: 'bar',
    data: {
      labels,
      datasets: [
        {
          label: 'Inflow',
          data: inflowData,
          backgroundColor: CHART_COLORS.cashflow.inflow,
          borderRadius: {
            topLeft: 8,
            topRight: 8,
            bottomLeft: 0,
            bottomRight: 0
          },
          borderSkipped: false,
          barThickness: 'flex',
          maxBarThickness: 60
        },
        {
          label: 'Outflow',
          data: outflowData,
          backgroundColor: CHART_COLORS.cashflow.outflow,
          borderRadius: {
            topLeft: 8,
            topRight: 8,
            bottomLeft: 0,
            bottomRight: 0
          },
          borderSkipped: false,
          barThickness: 'flex',
          maxBarThickness: 60
        }
      ]
    },
    options: {
      ...baseChartConfig,
      plugins: {
        ...baseChartConfig.plugins,
        tooltip: {
          ...baseChartConfig.plugins.tooltip,
          callbacks: {
            label: (context) => {
              const label = context.dataset.label || '';
              const value = context.parsed.y;
              return `${label}: ${formatCurrency(value)}`;
            }
          }
        }
      },
      scales: {
        ...baseChartConfig.scales,
        x: {
          ...baseChartConfig.scales.x,
          stacked: true
        },
        y: {
          ...baseChartConfig.scales.y,
          stacked: true,
          ticks: {
            ...baseChartConfig.scales.y.ticks,
            callback: (value) => formatAxisValue(value)
          }
        }
      },
      ...options
    }
  };

  return config;
}

/**
 * Create mixed chart configuration (line + bar)
 */
export function createMixedChartConfig(labels, datasets, options = {}) {
  const config = {
    type: 'bar',
    data: {
      labels,
      datasets: datasets.map((dataset, index) => {
        const baseDataset = {
          label: dataset.label,
          data: dataset.data,
          ...dataset
        };

        if (dataset.type === 'line') {
          return {
            ...baseDataset,
            type: 'line',
            borderColor: dataset.color || CHART_COLORS.series[index % CHART_COLORS.series.length],
            backgroundColor: 'transparent',
            borderWidth: 3,
            tension: 0.4,
            fill: false,
            pointRadius: 5,
            pointHoverRadius: 7,
            pointBackgroundColor: dataset.color || CHART_COLORS.series[index % CHART_COLORS.series.length],
            pointBorderColor: '#FFFFFF',
            pointBorderWidth: 2,
            pointHoverBorderWidth: 3,
            yAxisID: dataset.yAxisID || 'y'
          };
        } else {
          return {
            ...baseDataset,
            type: 'bar',
            backgroundColor: dataset.color || CHART_COLORS.series[index % CHART_COLORS.series.length],
            borderRadius: {
              topLeft: 8,
              topRight: 8,
              bottomLeft: 0,
              bottomRight: 0
            },
            borderSkipped: false,
            barThickness: 'flex',
            maxBarThickness: 60,
            yAxisID: dataset.yAxisID || 'y'
          };
        }
      })
    },
    options: {
      ...baseChartConfig,
      ...options
    }
  };

  return config;
}
