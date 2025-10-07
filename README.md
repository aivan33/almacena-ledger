# Financial KPI Dashboard

An interactive financial dashboard with dual-currency support (USD/EUR) for tracking KPIs, with data fetching from Google Sheets/Drive and standalone packaging capabilities.

## Features

- 📊 **Interactive Dashboard**: Beautiful HTML-based dashboard with charts and KPI cards
- 💱 **Dual-Currency Support**: View data in both USD (original) and EUR (converted using ECB rates)
- 🔄 **Google Sheets/Drive Integration**: Fetch data directly from Google Sheets or Excel files in Drive
- 📦 **Standalone Packaging**: Create shareable dashboard packages (no installation required)
- 📈 **Multiple Views**: Main dashboard, analysis view, data validation, and debug modes
- 🎨 **Period Comparison**: Analyze trends across multiple time periods

## Quick Start

### Prerequisites

- Python 3.x
- Google API credentials (optional, for Google Sheets integration)

### Installation

```bash
# Install dependencies
pip install -r requirements.txt
```

### Try It Out with Sample Data

Want to test the dashboard first? Use the provided sample data:

```bash
# Copy sample data to processed directory
cp examples/data/sample_dashboard_data.json data/processed/dashboard_data.json

# Open the dashboard
start dashboard/index.html  # Windows
open dashboard/index.html   # macOS
xdg-open dashboard/index.html  # Linux
```

See [examples/README.md](examples/README.md) for complete sample data documentation.

## Usage

### Option 1: Fetch Data from Google Sheets/Drive

```bash
# Fetch KPI data from Google Sheets or Drive
python scripts/fetch_from_sheets.py <file-id> <sheet-name>

# Example:
python scripts/fetch_from_sheets.py 1ABC123xyz dashboard
```

This will:
1. Download the Excel file or read the Google Sheet
2. Process and clean the data
3. Convert USD to EUR using exchange rates in the data
4. Generate `data/processed/dashboard_data.json` with dual-currency values
5. Generate `data/processed/kpis_v2_pipeline.csv` (EUR values)

### Option 2: Convert Existing Wide-Format Data

If you have wide-format KPI data locally:

```bash
# Convert wide-format CSV to dashboard format
python scripts/convert_kpis_wide_to_long.py data/raw/kpis_v2.csv --both

# Run the pipeline
python data_pipeline.py
```

### Option 3: Use Direct Format Data

Place your data in direct format at `data/raw/kpi_data.csv`:

```csv
month,GMV,Funded Amount,Avg Days Outstanding,# Invoices,# Boxes
1/1/25,11352846,10107543,18,54,91
2/1/25,12671553,11641505,18,51,97
```

Then run:
```bash
python data_pipeline.py
```

## Google Sheets/Drive Setup

To fetch data from Google Sheets or Drive, you need Google API credentials:

### 1. Create Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project

### 2. Enable APIs

- Enable **Google Sheets API**
- Enable **Google Drive API**

### 3. Create Service Account

1. Navigate to "IAM & Admin" > "Service Accounts"
2. Click "Create Service Account"
3. Give it a name (e.g., "dashboard-fetcher")
4. Create and download the JSON key file

### 4. Configure Credentials

```bash
# Create credentials directory
mkdir credentials

# Copy your JSON file
cp ~/Downloads/your-key.json credentials/service-account.json

# OR use environment variable
export GOOGLE_CREDENTIALS_FILE="/path/to/your-credentials.json"
```

### 5. Share Your Google Sheet

- Open your Google Sheet or Drive file
- Click "Share"
- Add the service account email (from your JSON file)
- Grant "Viewer" permissions

### 6. Get File/Sheet ID

- **Google Sheets**: Copy ID from URL
  - `https://docs.google.com/spreadsheets/d/FILE_ID_HERE/edit`
- **Google Drive**: Right-click file > "Get link" > Copy ID

**Security Note**: Credentials are automatically excluded from git via `.gitignore`. Never commit credentials!

## Building Standalone Dashboard Package

Create a shareable dashboard that requires no Python or server:

```bash
# Build the package
python build_dashboard_package.py

# This creates:
# - dashboard-package/ (folder with standalone HTML)
# - almacena-dashboard.zip (ready to share)
```

The recipient just needs to:
1. Unzip the file
2. Double-click `Almacena-Dashboard.html`
3. View the dashboard in any browser!

## Data Format

### Dashboard JSON Format

The dashboard expects data in this format:

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

### Wide Format (for conversion)

```csv
month,January,February,March,...
GMV,"$11,763,388","$13,150,221","$7,042,922",...
Funded Amount,"$10,473,053","$12,081,263","$6,186,160",...
```

## Supported KPIs

### Financial Metrics
- GMV (Gross Merchandise Value)
- Funded Amount
- Average Portfolio Outstanding
- Arrangement Fees
- Accrued Interests
- Cost of Funds

### Insurance Metrics
- Cargo Insurance Fees
- Cargo Insurance Costs
- GMV Insured Percentage

### Logistics Metrics
- Logistic Fees
- Logistic Costs
- Warehouse Destination Fees/Costs
- Handling & Warehouse Fees/Costs

### Administrative Metrics
- Docs Management Fees
- Costs of Docs Delivery

### Performance Metrics
- Average Days Outstanding
- Number of Invoices
- Number of Boxes
- Number of Active Loans
- Average Loan Size
- Default Rate %
- Cash Drag %

## Currency Conversion

The system automatically converts USD to EUR for monetary values using exchange rates from your data or ECB historical rates.

**Converted to EUR:**
- All monetary values (GMV, fees, costs, interest, etc.)

**Not converted:**
- Percentages
- Counts (# of invoices, boxes, loans)
- Days Outstanding
- Exchange rates themselves

## Project Structure

```
dashboard/
├── dashboard/                # Dashboard HTML files
│   ├── index.html           # Main dashboard
│   ├── analysis.html        # Detailed analysis view
│   ├── data-validation.html # Data validation tools
│   └── debug.html           # Debug view
├── scripts/                 # Data processing scripts
│   ├── fetch_from_sheets.py # Google Sheets/Drive fetcher
│   └── convert_kpis_wide_to_long.py # Wide-to-long converter
├── data/
│   ├── raw/                 # Place your source data here
│   └── processed/           # Processed data output
│       ├── dashboard_data.json
│       └── kpis_v2_pipeline.csv
├── examples/                # Sample data for testing
├── credentials/             # Google API credentials (not in git)
├── data_pipeline.py         # Main data processing pipeline
├── build_dashboard_package.py # Standalone package builder
└── requirements.txt         # Python dependencies
```

## Environment Variables

- `GOOGLE_CREDENTIALS_FILE`: Path to Google service account JSON file
  - Default: `credentials/service-account.json`

## Scripts Reference

### fetch_from_sheets.py
Fetch and process data from Google Sheets/Drive with dual-currency support.

```bash
python scripts/fetch_from_sheets.py <file-id> [sheet-name]

# Options:
# - file-id: Google Sheets/Drive file ID (required)
# - sheet-name: Sheet name to read (default: 'dashboard')
```

### convert_kpis_wide_to_long.py
Convert wide-format KPI data to long format with currency conversion.

```bash
python scripts/convert_kpis_wide_to_long.py <input-file> [options]

# Options:
# --both: Generate both long and pipeline formats
# --pipeline-format <file>: Specify pipeline format output
# --no-conversion: Skip USD to EUR conversion
```

### data_pipeline.py
Process KPI data and generate dashboard JSON.

```bash
python data_pipeline.py

# Automatically detects and uses kpis_v2 data if available
# Generates dashboard_data.json for the dashboard
```

### build_dashboard_package.py
Create standalone dashboard package for sharing.

```bash
python build_dashboard_package.py

# Creates:
# - dashboard-package/ directory
# - almacena-dashboard.zip file
```

## Development

### Running Tests

```bash
# Test data conversion
python test_conversion.py

# Check data format
python check_sep.py
```

### Project Setup

```bash
# Initialize project structure
python setup_project.py
```

## Troubleshooting

### "Credentials file not found"
- Ensure `credentials/service-account.json` exists
- Or set `GOOGLE_CREDENTIALS_FILE` environment variable
- Check that the path is correct

### "Permission denied" on Google Sheets
- Verify the sheet is shared with your service account email
- Check that service account has at least "Viewer" permissions

### "No data found in sheet"
- Verify the sheet name is correct
- Check that the sheet contains data in the expected format
- Ensure the first row contains metric names

### Dashboard shows no data
- Check that `data/processed/dashboard_data.json` exists
- Verify the JSON file is properly formatted
- Open browser console (F12) for error messages

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Exchange rate data from [European Central Bank](https://www.ecb.europa.eu/stats/policy_and_exchange_rates/)
- Built with Python, Pandas, and vanilla JavaScript for maximum portability
