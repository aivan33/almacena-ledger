// Data filtering utilities

export function filterDataByDateRange(data, startIndex, endIndex) {
    if (!data || !data.periods) return data;

    // If no range specified, return all data
    if (startIndex === null && endIndex === null) {
        return data;
    }

    const start = startIndex !== null ? parseInt(startIndex) : 0;
    const end = endIndex !== null ? parseInt(endIndex) : data.periods.length - 1;

    console.log(`Filtering data from index ${start} to ${end}`);

    // Filter periods
    const filteredPeriods = data.periods.slice(start, end + 1);

    // Filter all metrics in values_usd and values_eur
    const filteredValuesUsd = {};
    const filteredValuesEur = {};

    if (data.values_usd) {
        Object.keys(data.values_usd).forEach(metric => {
            filteredValuesUsd[metric] = data.values_usd[metric].slice(start, end + 1);
        });
    }

    if (data.values_eur) {
        Object.keys(data.values_eur).forEach(metric => {
            filteredValuesEur[metric] = data.values_eur[metric].slice(start, end + 1);
        });
    }

    return {
        ...data,
        periods: filteredPeriods,
        values_usd: filteredValuesUsd,
        values_eur: filteredValuesEur
    };
}
