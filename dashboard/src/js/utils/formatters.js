// Formatting utilities for numbers, currency, and percentages

/**
 * Format large numbers with K/M/B suffixes
 * @param {number} value - The number to format
 * @param {number} decimals - Number of decimal places (default: 1)
 * @returns {string} Formatted number
 */
export function formatNumber(value, decimals = 1) {
    if (value === null || value === undefined || isNaN(value)) return '0';

    const absValue = Math.abs(value);
    const sign = value < 0 ? '-' : '';

    if (absValue >= 1000000000) {
        return sign + (absValue / 1000000000).toFixed(decimals) + 'B';
    } else if (absValue >= 1000000) {
        return sign + (absValue / 1000000).toFixed(decimals) + 'M';
    } else if (absValue >= 1000) {
        return sign + (absValue / 1000).toFixed(decimals) + 'K';
    }

    return sign + absValue.toFixed(decimals);
}

/**
 * Format currency with symbol and proper number formatting
 * @param {number} value - The number to format
 * @param {string} currency - Currency code ('usd' or 'eur')
 * @param {number} decimals - Number of decimal places (default: 1)
 * @returns {string} Formatted currency
 */
export function formatCurrency(value, currency = 'usd', decimals = 1) {
    const symbol = currency.toLowerCase() === 'eur' ? '€' : '$';
    const formatted = formatNumber(value, decimals);
    return `${symbol}${formatted}`;
}

/**
 * Format percentage
 * @param {number} value - The percentage value
 * @param {number} decimals - Number of decimal places (default: 1)
 * @returns {string} Formatted percentage
 */
export function formatPercent(value, decimals = 1) {
    if (value === null || value === undefined || isNaN(value)) return '0%';
    return `${value.toFixed(decimals)}%`;
}

/**
 * Format number for axis ticks (shorter format)
 * @param {number} value - The number to format
 * @returns {string} Formatted number
 */
export function formatAxisNumber(value) {
    if (value === 0) return '0';

    const absValue = Math.abs(value);
    const sign = value < 0 ? '-' : '';

    if (absValue >= 1000000) {
        return sign + (absValue / 1000000).toFixed(0) + 'M';
    } else if (absValue >= 1000) {
        return sign + (absValue / 1000).toFixed(0) + 'K';
    }

    return sign + absValue.toString();
}

/**
 * Format currency for tooltips (full precision)
 * @param {number} value - The number to format
 * @param {string} currency - Currency code ('usd' or 'eur')
 * @returns {string} Formatted currency with full precision
 */
export function formatCurrencyFull(value, currency = 'usd') {
    if (value === null || value === undefined || isNaN(value)) return '$0';

    const symbol = currency.toLowerCase() === 'eur' ? '€' : '$';
    return `${symbol}${value.toLocaleString('en-US', {
        minimumFractionDigits: 0,
        maximumFractionDigits: 0
    })}`;
}
