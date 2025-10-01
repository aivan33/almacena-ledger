# KPI Dashboard Pipeline

## Quick Start

1. **Install dependencies**:
   ```bash
   pip install pandas numpy
   ```

2. **Add your data**:
   - **Option A**: Place your CSV file in `data/raw/kpi_data.csv` in direct format
   - **Option B**: Place your wide-format KPIs data in `data/raw/kpis_v2.csv` (automatically converted)

3. **For wide-format KPIs data (Option B)**:
   ```bash
   # Convert wide-format data to pipeline format
   python scripts/convert_kpis_wide_to_long.py data/raw/kpis_v2.csv --both
   ```

4. **Run the pipeline**:
   ```bash
   python data_pipeline.py
   ```

5. **View dashboard**:
   - Open `dashboard/index.html` in your browser

## Data Formats

### Direct Format (kpi_data.csv)
```csv
month,GMV,Funded Amount,Avg Days Outstanding,# Invoices,# Boxes
1/1/25,11352846,10107543,18,54,91
2/1/25,12671553,11641505,18,51,97
...
```

### Wide Format (kpis_v2.csv)
```csv
month,January,February,March,April,May,June,...
GMV,"$11,763,388","$13,150,221","$7,042,922",...
Funded Amount,"$10,473,053","$12,081,263","$6,186,160",...
Avg Days Outstanding,18,18,27,...
...
```

### KPI Metrics Supported
The pipeline now supports extensive KPI metrics including:
- Core metrics: GMV, Funded Amount, Average Days Outstanding, Number of Invoices/Boxes
- Financial metrics: Arrangement Fees, Accrued Interests, Cost of Funds
- Insurance metrics: Cargo Insurance Fees/Costs, GMV Insured Percentage
- Logistics metrics: Logistic Fees/Costs, Handling & Warehouse Fees/Costs
- Administrative: Docs Management Fees, Costs of Docs Delivery
- Performance metrics: Cash Drag percentage
- Exchange rates: USD to EUR historical rates

### Currency Conversion
**Automatic USD to EUR Conversion**: The pipeline automatically converts all monetary values from USD to EUR using the historical exchange rates provided in the data (`USD to EUR historical Rates (EoM)` column). This includes:

**Converted to EUR:**
- GMV, Funded Amount, Portfolio Outstanding
- All fees (Arrangement, Logistic, Insurance, Management, etc.)
- All costs (Insurance, Docs Delivery, Warehouse, etc.)
- Accrued Interests, Cost of Funds

**Not converted (preserved as-is):**
- Percentages (Cash Drag, GMV Insured %)
- Counts (# Invoices, # Boxes)
- Days Outstanding
- Exchange rates themselves

## Scripts

### KPIs Data Conversion
```bash
# Convert wide-format KPIs to long format (with automatic USD to EUR conversion)
python scripts/convert_kpis_wide_to_long.py data/raw/kpis_v2.csv -o data/processed/kpis_v2_long.csv

# Convert to pipeline-compatible format (with EUR conversion)
python scripts/convert_kpis_wide_to_long.py data/raw/kpis_v2.csv --pipeline-format data/processed/kpis_v2_pipeline.csv

# Generate both formats (with EUR conversion)
python scripts/convert_kpis_wide_to_long.py data/raw/kpis_v2.csv --both

# Skip currency conversion (keep USD values)
python scripts/convert_kpis_wide_to_long.py data/raw/kpis_v2.csv --both --no-conversion
```

### Pipeline Processing
```bash
# Run the complete KPI pipeline (automatically detects and uses kpis_v2 data if available)
python data_pipeline.py
```

## Files
- `data/raw/` - Place your raw CSV data here
  - `kpi_data.csv` - Direct format data
  - `kpis_v2.csv` - Wide format data (gets converted automatically)
- `data/processed/` - Processed data will be saved here
  - `kpis_v2_long.csv` - Long format conversion
  - `kpis_v2_pipeline.csv` - Pipeline-compatible format
  - `dashboard_data.json` - Final processed data for dashboard
  - `processed_data.csv` - CSV export of processed data
- `scripts/` - Data processing scripts
  - `convert_kpis_wide_to_long.py` - Wide-to-long conversion utility
- `dashboard/` - Dashboard HTML file
