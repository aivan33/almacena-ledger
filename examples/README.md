# Sample Data for Dashboard

This directory contains sample data for testing and demonstration purposes.

## Contents

### Sample Files

1. **`sample_dashboard_data.json`** - Ready-to-use dashboard data
   - 6 months of financial metrics (Jan-Jun 2025)
   - Dual-currency format (USD original, EUR converted)
   - 20 different KPI metrics
   - Can be used directly with the dashboard

2. **`sample_kpis_wide.csv`** - Wide-format KPI data
   - Same data in CSV wide format
   - Includes exchange rate row for conversion
   - Use this to test the data conversion scripts

## Quick Start

### Option 1: Use Pre-built Dashboard Data

```bash
# Copy sample data to processed directory
cp examples/data/sample_dashboard_data.json data/processed/dashboard_data.json

# Open the dashboard
start dashboard/index.html  # Windows
open dashboard/index.html   # macOS
xdg-open dashboard/index.html  # Linux
```

### Option 2: Test Data Conversion

```bash
# Convert wide-format CSV to dashboard format
python scripts/convert_kpis_wide_to_long.py examples/data/sample_kpis_wide.csv --both

# Run the pipeline
python data_pipeline.py

# Open the dashboard
start dashboard/index.html
```

## Sample Metrics Included

The sample data includes these KPIs:

### Financial Metrics
- GMV (Gross Merchandise Value)
- Funded Amount
- Average Portfolio Outstanding
- Arrangement Fees
- Accrued Interests
- Cost of Funds (Accrued)

### Operational Metrics
- Logistic Fees & Costs
- Cargo Insurance Fees & Costs
- Docs Management Fees
- Costs of Docs Delivery
- Warehouse Destination Fees & Costs

### Performance Metrics
- Number of Active Loans
- Average Loan Size
- Default Rate %
- Average Days Outstanding
- Number of Invoices
- Number of Boxes

## Data Format Details

### Dashboard JSON Format

```json
{
  "metrics": ["GMV", "Funded Amount", ...],
  "periods": ["Jan-25", "Feb-25", ...],
  "values_usd": {
    "GMV": [850000, 920000, ...],
    ...
  },
  "values_eur": {
    "GMV": [765000, 828000, ...],
    ...
  }
}
```

### Wide CSV Format

```csv
month,Jan-25,Feb-25,Mar-25,...
USD to EUR historical Rates (EoM),0.9,0.9,0.9,...
GMV,850000,920000,975000,...
Funded Amount,680000,736000,780000,...
```

The first data row should be the exchange rate (used for USD to EUR conversion).

## Using Your Own Data

To use your own data:

1. **For Dashboard JSON**: Replace the sample values with your actual KPIs while maintaining the structure
2. **For Wide CSV**: Follow the same column format (month name columns) and include the exchange rate row

### Tips

- Monetary values will be converted using the exchange rate row
- Percentages, counts, and days are not converted
- Ensure metric names match exactly for proper dashboard display
- Date columns should follow the "Mon-YY" format (e.g., "Jan-25", "Feb-25")

## Testing Different Scenarios

The sample data is designed to show:
- Growth trends (increasing GMV and funded amounts)
- Seasonal variations
- Improving performance (decreasing default rate)
- Stable operational metrics

Feel free to modify the values to test different scenarios in the dashboard!

## Need Help?

See the main [README.md](../README.md) for complete documentation on:
- Setting up Google Sheets integration
- Converting your own data
- Building standalone packages
- Troubleshooting common issues
