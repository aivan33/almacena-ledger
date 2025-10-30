# Dashboard Setup Context

## Google Sheets Configuration

### File ID Location
The Google Drive/Sheets file ID is stored in `config.json` at the root of the dashboard directory.

To find your file ID:
1. Open your Google Sheet
2. Look at the URL: `https://docs.google.com/spreadsheets/d/FILE_ID_HERE/edit`
3. Copy the long string between `/d/` and `/edit`
4. Update `config.json` with this ID

### Current Configuration
- **File ID**: Check `config.json` → `google_drive_file_id`
- **Sheet Name**: dashboard (configurable in `config.json`)
- **Data Range**: Through September 2025 only

## Quick Commands

### Update Dashboard Data
```bash
# This will automatically use the file ID from config.json
python scripts/fetch_from_sheets.py $(python -c "import json; print(json.load(open('config.json'))['google_drive_file_id'])") dashboard

# Or use the /update slash command
/update
```

### Build Dashboard Package
```bash
cd dashboard
python build_dashboard_package.py
```

## Chart Settings

### GMV Chart
- Minimum Y-axis: 5M (with buffer to prevent values touching bottom)
- Buffer factor: 0.9 (shows 10% below minimum data point)

### Portfolio Health Metrics Chart
- Days minimum Y-axis: 10
- Data labels: % GMV Insured positioned at bottom near X-axis
- Data labels: Positioned to avoid overlap

## Last Update
File created: 2025-10-23
Purpose: Maintain context for faster setup and avoid repeated configuration questions
