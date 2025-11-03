"""
Fetch KPI data from Google Sheets and save to local files for dashboard consumption.

Environment Variables:
    GOOGLE_CREDENTIALS_FILE: Path to Google service account JSON file
                            (default: credentials/service-account.json)
    LOG_LEVEL: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
              (default: INFO)
"""
import os
import json
import pandas as pd
from google.oauth2 import service_account
from googleapiclient.discovery import build
from dotenv import load_dotenv
from scripts.logger_config import get_logger, log_environment_info

# Load environment variables from .env file
load_dotenv()

# Initialize logger
logger = get_logger(__name__)

# Configuration - use environment variables with fallback
CREDENTIALS_FILE = os.getenv(
    'GOOGLE_CREDENTIALS_FILE',
    'credentials/service-account.json'
)
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
    if not os.path.exists(CREDENTIALS_FILE):
        logger.error(f"Credentials file not found: {CREDENTIALS_FILE}")
        logger.error("Please set GOOGLE_CREDENTIALS_FILE environment variable or place "
                    f"credentials at {CREDENTIALS_FILE}")
        logger.error("See README.md for setup instructions.")
        raise FileNotFoundError(
            f"Credentials file not found: {CREDENTIALS_FILE}\n"
            f"Please set GOOGLE_CREDENTIALS_FILE environment variable or place "
            f"credentials at {CREDENTIALS_FILE}\n"
            f"See README.md for setup instructions."
        )

    logger.debug(f"Loading credentials from: {CREDENTIALS_FILE}")
    creds = service_account.Credentials.from_service_account_file(
        CREDENTIALS_FILE, scopes=SCOPES)
    logger.info("Successfully loaded Google API credentials")
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
        logger.info(f"Downloading Excel file from Google Drive (ID: {file_id[:10]}...)")
        drive_service = get_drive_service()

        # Get file metadata
        file_metadata = drive_service.files().get(fileId=file_id).execute()
        logger.info(f"File name: {file_metadata.get('name')}")
        logger.debug(f"MIME type: {file_metadata.get('mimeType')}")

        # Download file
        request = drive_service.files().get_media(fileId=file_id)
        file_buffer = io.BytesIO()
        downloader = MediaIoBaseDownload(file_buffer, request)

        done = False
        while not done:
            status, done = downloader.next_chunk()
            logger.debug(f"Download progress: {int(status.progress() * 100)}%")

        file_buffer.seek(0)

        # Read Excel file
        logger.info("Parsing Excel file")
        df = pd.read_excel(file_buffer, sheet_name=None)  # Read all sheets
        logger.info(f"Successfully read {len(df)} sheet(s) from Excel file")
        return df

    except Exception as e:
        logger.error(f"Error downloading from Drive: {e}", exc_info=True)
        raise


def fetch_sheet_data(spreadsheet_id, sheet_name='dashboard'):
    """Fetch data from Google Sheets."""
    logger.info(f"Fetching data from Google Sheets (ID: {spreadsheet_id[:10]}...)")
    service = get_sheets_service()

    # First, try to get spreadsheet metadata to see available sheets
    try:
        metadata = service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
        sheets = metadata.get('sheets', [])
        sheet_titles = [s['properties']['title'] for s in sheets]
        logger.info(f"Available sheets: {sheet_titles}")

        # If sheet_name not found, use first sheet
        if sheet_name not in sheet_titles and sheets:
            sheet_name = sheet_titles[0]
            logger.warning(f"Requested sheet not found. Using first sheet: {sheet_name}")
    except Exception as e:
        logger.warning(f"Could not get metadata: {e}")
        # Continue anyway with provided sheet_name

    # Get the data from the sheet
    logger.debug(f"Reading data from sheet: {sheet_name}")
    sheet = service.spreadsheets()
    result = sheet.values().get(
        spreadsheetId=spreadsheet_id,
        range=f'{sheet_name}!A:Z'  # Adjust range as needed
    ).execute()

    values = result.get('values', [])

    if not values:
        logger.error('No data found in the sheet')
        raise ValueError('No data found in the sheet')

    logger.info(f"Successfully fetched {len(values)} rows from sheet")
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
    logger.debug("Starting USD to EUR conversion")
    # Make a copy
    df = df.copy()

    # Get the exchange rate row (should be labeled 'exch_rate' or similar)
    exch_rate_row = None
    for idx, row in df.iterrows():
        month_val = str(row['month']).lower()
        if 'exch' in month_val or 'rate' in month_val or 'eur' in month_val or 'usd' in month_val:
            exch_rate_row = row
            logger.info(f"Found exchange rate row: {row['month']}")
            break

    if exch_rate_row is None:
        logger.warning("No exchange rate row found. Skipping currency conversion.")
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
                    logger.warning(f"Error converting {metric} for period {col}: {e}")
                    continue

    logger.info(f"Converted {len(currency_metrics)} currency metrics to EUR")
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

    # Apply filtering from config if available
    config = load_config()
    if config and 'data_settings' in config:
        exclude_periods = config['data_settings'].get('exclude_periods', [])
        if exclude_periods:
            # Filter out excluded periods
            filtered_periods = []
            filtered_indices = []
            for i, period in enumerate(data['periods']):
                if period not in exclude_periods:
                    filtered_periods.append(period)
                    filtered_indices.append(i)

            # Update periods
            data['periods'] = filtered_periods

            # Filter values for each metric
            for metric in data['metrics']:
                if metric in data['values_usd']:
                    data['values_usd'][metric] = [data['values_usd'][metric][i] for i in filtered_indices]
                if metric in data['values_eur']:
                    data['values_eur'][metric] = [data['values_eur'][metric][i] for i in filtered_indices]

            logger.info(f"Filtered out periods: {', '.join(exclude_periods)}")

    return data


def load_config():
    """Load configuration from config.json."""
    config_path = 'config.json'
    if os.path.exists(config_path):
        with open(config_path, 'r') as f:
            return json.load(f)
    return None


def main(spreadsheet_id=None, sheet_name='dashboard'):
    """Main execution function."""
    logger.info("=" * 60)
    logger.info("Starting Dashboard Data Fetch Process")
    logger.info("=" * 60)

    # Try to load config if no spreadsheet_id provided
    if not spreadsheet_id:
        # Priority 1: Check environment variables (SECURE)
        spreadsheet_id = os.getenv('GOOGLE_DRIVE_FILE_ID')
        sheet_name = os.getenv('GOOGLE_SHEET_NAME', sheet_name)

        if spreadsheet_id:
            logger.info("Using file ID from environment variable")
        else:
            # Priority 2: Fall back to config.json (LEGACY - use .env instead!)
            config = load_config()
            if config and config.get('google_drive_file_id') and config['google_drive_file_id'] != 'YOUR_FILE_ID_HERE':
                spreadsheet_id = config['google_drive_file_id']
                sheet_name = config.get('sheet_name', sheet_name)
                logger.warning("[LEGACY] Using file ID from config.json - Please migrate to .env file")
            else:
                logger.error("No Google Drive file ID found!")
                logger.error("Please set credentials in one of these ways:")
                logger.error("  1. (RECOMMENDED) Set GOOGLE_DRIVE_FILE_ID in .env file")
                logger.error("  2. Pass as argument: python scripts/fetch_from_sheets.py <file_id>")
                logger.error("  3. (LEGACY) Update config.json")
                logger.error("See .env.example for secure setup instructions.")
                return

    logger.info("Fetching data from Google...")
    logger.info(f"File ID: {spreadsheet_id[:10]}...")
    logger.info(f"Sheet name: {sheet_name}")

    try:
        # Try Google Sheets API first
        try:
            logger.info("Attempting to read as Google Sheets...")
            values = fetch_sheet_data(spreadsheet_id, sheet_name)
            logger.info(f"Successfully fetched {len(values)} rows")
            df = convert_to_dataframe(values)
        except Exception as e:
            logger.info("Not a Google Sheet, trying as Excel file from Drive...")
            # Try as Excel file from Drive
            excel_data = download_excel_from_drive(spreadsheet_id)

            # Find the sheet with matching name or use first sheet
            if sheet_name in excel_data:
                df = excel_data[sheet_name]
            else:
                # Use first sheet
                first_sheet = list(excel_data.keys())[0]
                logger.warning(f"Sheet '{sheet_name}' not found, using: {first_sheet}")
                df = excel_data[first_sheet]

        logger.info(f"DataFrame ready: {df.shape[0]} rows x {df.shape[1]} columns")

        # Clean and process - this gives us USD values
        logger.info("Cleaning and processing data...")
        df_usd = clean_and_process(df)

        # Convert to EUR
        logger.info("Converting USD values to EUR...")
        df_eur = convert_to_eur(df_usd.copy())

        # Save wide format CSV (EUR version)
        logger.info(f"Saving wide format CSV to: {OUTPUT_CSV}")
        df_eur.to_csv(OUTPUT_CSV, index=False)
        logger.info(f"Successfully saved CSV")

        # Prepare and save JSON for dashboard with both currencies
        logger.info("Preparing dashboard JSON with dual currency support...")
        dashboard_data = prepare_dashboard_json(df_usd, df_eur)
        with open(OUTPUT_JSON, 'w') as f:
            json.dump(dashboard_data, f, indent=2)
        logger.info(f"Successfully saved dashboard JSON to: {OUTPUT_JSON}")

        logger.info("=" * 60)
        logger.info("Data pipeline completed successfully!")
        logger.info("Dashboard is ready to view at: dashboard/index.html")
        logger.info("=" * 60)

    except Exception as e:
        logger.error(f"Error in data pipeline: {str(e)}", exc_info=True)
        raise


if __name__ == '__main__':
    import sys

    if len(sys.argv) > 1:
        spreadsheet_id = sys.argv[1]
        sheet_name = sys.argv[2] if len(sys.argv) > 2 else 'dashboard'
        main(spreadsheet_id, sheet_name)
    else:
        # Try to use config.json
        main()