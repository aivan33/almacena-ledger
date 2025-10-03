"""
Fetch KPI data from Google Sheets and save to local files for dashboard consumption.
"""
import os
import json
import pandas as pd
from google.oauth2 import service_account
from googleapiclient.discovery import build

# Configuration
CREDENTIALS_FILE = 'credentials/genuine-ridge-473708-b9-1004a2f89ab7.json'
SPREADSHEET_ID = None  # Will be extracted from URL or provided
SHEET_NAME = 'dashboard'  # The sheet name to read from
SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets.readonly',
    'https://www.googleapis.com/auth/drive.readonly'
]

# Output paths
OUTPUT_CSV = 'data/processed/kpis_v2_pipeline.csv'
OUTPUT_JSON = 'data/processed/dashboard_data.json'


def get_credentials():
    """Get credentials for Google API."""
    creds = service_account.Credentials.from_service_account_file(
        CREDENTIALS_FILE, scopes=SCOPES)
    return creds


def get_sheets_service():
    """Initialize and return Google Sheets API service."""
    creds = get_credentials()
    service = build('sheets', 'v4', credentials=creds)
    return service


def get_drive_service():
    """Initialize and return Google Drive API service."""
    creds = get_credentials()
    service = build('drive', 'v3', credentials=creds)
    return service


def download_excel_from_drive(file_id):
    """Download Excel file from Google Drive and read it."""
    import io
    from googleapiclient.http import MediaIoBaseDownload

    try:
        drive_service = get_drive_service()

        # Get file metadata
        file_metadata = drive_service.files().get(fileId=file_id).execute()
        print(f"File name: {file_metadata.get('name')}")
        print(f"MIME type: {file_metadata.get('mimeType')}")

        # Download file
        request = drive_service.files().get_media(fileId=file_id)
        file_buffer = io.BytesIO()
        downloader = MediaIoBaseDownload(file_buffer, request)

        done = False
        while not done:
            status, done = downloader.next_chunk()
            print(f"Download progress: {int(status.progress() * 100)}%")

        file_buffer.seek(0)

        # Read Excel file
        df = pd.read_excel(file_buffer, sheet_name=None)  # Read all sheets
        return df

    except Exception as e:
        print(f"Error downloading from Drive: {e}")
        raise


def fetch_sheet_data(spreadsheet_id, sheet_name='dashboard'):
    """Fetch data from Google Sheets."""
    service = get_sheets_service()

    # First, try to get spreadsheet metadata to see available sheets
    try:
        metadata = service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
        sheets = metadata.get('sheets', [])
        print(f"Available sheets: {[s['properties']['title'] for s in sheets]}")

        # If sheet_name not found, use first sheet
        sheet_titles = [s['properties']['title'] for s in sheets]
        if sheet_name not in sheet_titles and sheets:
            sheet_name = sheet_titles[0]
            print(f"Using first sheet: {sheet_name}")
    except Exception as e:
        print(f"Could not get metadata: {e}")
        # Continue anyway with provided sheet_name

    # Get the data from the sheet
    sheet = service.spreadsheets()
    result = sheet.values().get(
        spreadsheetId=spreadsheet_id,
        range=f'{sheet_name}!A:Z'  # Adjust range as needed
    ).execute()

    values = result.get('values', [])

    if not values:
        raise ValueError('No data found in the sheet')

    return values


def convert_to_dataframe(values):
    """Convert Google Sheets data to pandas DataFrame."""
    # First row is headers
    headers = values[0]
    data_rows = values[1:]

    # Create DataFrame
    df = pd.DataFrame(data_rows, columns=headers)

    return df


def clean_and_process(df):
    """Clean and process the dataframe to match expected format."""
    # Make a copy to avoid modifying original
    df = df.copy()

    # Clean currency values (remove $, commas, and convert to float)
    for col in df.columns:
        if col != 'month':  # Skip the month column
            # Convert to string first to handle mixed types
            df[col] = df[col].astype(str)
            df[col] = df[col].replace('', pd.NA)
            df[col] = df[col].replace('nan', pd.NA)
            df[col] = df[col].str.replace('$', '', regex=False)
            df[col] = df[col].str.replace(',', '', regex=False)
            df[col] = df[col].str.replace('%', '', regex=False)
            df[col] = df[col].str.strip()

    return df


def convert_to_eur(df):
    """Convert USD amounts to EUR using the exchange rate row."""
    # Make a copy
    df = df.copy()

    # Get the exchange rate row (should be labeled 'exch_rate' or similar)
    exch_rate_row = None
    for idx, row in df.iterrows():
        month_val = str(row['month']).lower()
        if 'exch' in month_val or 'rate' in month_val or 'eur' in month_val or 'usd' in month_val:
            exch_rate_row = row
            print(f"Found exchange rate row: {row['month']}")
            break

    if exch_rate_row is None:
        print("Warning: No exchange rate row found. Skipping currency conversion.")
        return df

    # Define which metrics should be converted (currency values)
    currency_metrics = [
        'GMV', 'Funded Amount', 'Arrangement Fees', 'Logistic Fees',
        'Logistic Costs', 'Cargo Insurance Fees', 'Cargo Insurance Costs',
        'Accrued Interests', 'Cost of Funds (Accrued)', 'Docs Management Fees',
        'Costs of Docs Delivery', 'Warehouse Destination Fees',
        'Warehouse Destination Costs', 'Avg Portfolio Outstanding'
    ]

    # Get column names (periods)
    period_cols = [col for col in df.columns if col != 'month']

    # Apply conversion to each currency metric
    for idx, row in df.iterrows():
        metric = row['month']
        if metric in currency_metrics:
            for col in period_cols:
                try:
                    amount = pd.to_numeric(row[col], errors='coerce')
                    rate = pd.to_numeric(exch_rate_row[col], errors='coerce')

                    if pd.notna(amount) and pd.notna(rate) and rate != 0:
                        # Convert USD to EUR
                        df.at[idx, col] = amount * rate

                except Exception as e:
                    print(f"Error converting {metric} for period {col}: {e}")
                    continue

    print(f"Converted {len(currency_metrics)} currency metrics to EUR")
    return df


def convert_to_long_format(df):
    """Convert wide format to long format for easier processing."""
    # Melt the dataframe
    id_vars = ['month']
    value_vars = [col for col in df.columns if col not in id_vars]

    df_long = df.melt(
        id_vars=id_vars,
        value_vars=value_vars,
        var_name='date',
        value_name='value'
    )

    return df_long


def prepare_dashboard_json(df_usd, df_eur):
    """Prepare JSON format for dashboard consumption with both USD and EUR."""
    from datetime import datetime

    # Convert dates to month names
    date_cols = [col for col in df_usd.columns if col != 'month']

    # Convert datetime columns to string format
    formatted_periods = []
    for col in date_cols:
        if isinstance(col, datetime):
            formatted_periods.append(col.strftime('%b-%y'))
        elif isinstance(col, str) and '00:00:00' in col:
            # Parse datetime string
            try:
                dt = pd.to_datetime(col)
                formatted_periods.append(dt.strftime('%b-%y'))
            except:
                formatted_periods.append(col)
        else:
            formatted_periods.append(str(col))

    # Prepare data structure with both currencies
    data = {
        'metrics': df_usd['month'].tolist(),
        'periods': formatted_periods,
        'values_usd': {},
        'values_eur': {}
    }

    # Add USD values
    for idx, row in df_usd.iterrows():
        metric_name = str(row['month'])
        values = []
        for col in date_cols:
            val = row[col]
            if pd.notna(val) and val != '' and val != '<NA>':
                try:
                    values.append(float(val))
                except (ValueError, TypeError):
                    values.append(str(val))
            else:
                values.append(None)
        data['values_usd'][metric_name] = values

    # Add EUR values
    for idx, row in df_eur.iterrows():
        metric_name = str(row['month'])
        values = []
        for col in date_cols:
            val = row[col]
            if pd.notna(val) and val != '' and val != '<NA>':
                try:
                    values.append(float(val))
                except (ValueError, TypeError):
                    values.append(str(val))
            else:
                values.append(None)
        data['values_eur'][metric_name] = values

    return data


def main(spreadsheet_id=None, sheet_name='dashboard'):
    """Main execution function."""
    if not spreadsheet_id:
        print("Please provide a Google Sheets ID")
        print("Usage: python scripts/fetch_from_sheets.py <spreadsheet_id>")
        return

    print(f"Fetching data from Google...")
    print(f"File ID: {spreadsheet_id}")
    print(f"Sheet name: {sheet_name}")

    try:
        # Try Google Sheets API first
        try:
            print("Attempting to read as Google Sheets...")
            values = fetch_sheet_data(spreadsheet_id, sheet_name)
            print(f"Successfully fetched {len(values)} rows")
            df = convert_to_dataframe(values)
        except Exception as e:
            print(f"Not a Google Sheet, trying as Excel file from Drive...")
            # Try as Excel file from Drive
            excel_data = download_excel_from_drive(spreadsheet_id)

            # Find the sheet with matching name or use first sheet
            if sheet_name in excel_data:
                df = excel_data[sheet_name]
            else:
                # Use first sheet
                first_sheet = list(excel_data.keys())[0]
                print(f"Sheet '{sheet_name}' not found, using: {first_sheet}")
                df = excel_data[first_sheet]

        print(f"DataFrame ready: {df.shape[0]} rows x {df.shape[1]} columns")

        # Clean and process - this gives us USD values
        df_usd = clean_and_process(df)

        # Convert to EUR
        df_eur = convert_to_eur(df_usd.copy())

        # Save wide format CSV (EUR version)
        df_eur.to_csv(OUTPUT_CSV, index=False)
        print(f"Saved wide format to: {OUTPUT_CSV}")

        # Prepare and save JSON for dashboard with both currencies
        dashboard_data = prepare_dashboard_json(df_usd, df_eur)
        with open(OUTPUT_JSON, 'w') as f:
            json.dump(dashboard_data, f, indent=2)
        print(f"Saved dashboard JSON to: {OUTPUT_JSON}")

        print("\nData pipeline completed successfully!")
        print(f"Dashboard is ready to view at: dashboard/index.html")

    except Exception as e:
        print(f"Error: {str(e)}")
        raise


if __name__ == '__main__':
    import sys

    if len(sys.argv) > 1:
        spreadsheet_id = sys.argv[1]
        sheet_name = sys.argv[2] if len(sys.argv) > 2 else 'dashboard'
        main(spreadsheet_id, sheet_name)
    else:
        print("Usage: python scripts/fetch_from_sheets.py <spreadsheet_id> [sheet_name]")
        print("\nExample:")
        print("  python scripts/fetch_from_sheets.py 1ABC123xyz dashboard")