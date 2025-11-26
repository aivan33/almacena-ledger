"""
Constants and configuration values for the Almacena Dashboard project.

This module centralizes all magic numbers, default values, and configuration
constants to improve code maintainability.
"""

# Google API Configuration
GOOGLE_SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets.readonly',
    'https://www.googleapis.com/auth/drive.readonly'
]

# Default file paths
DEFAULT_CREDENTIALS_FILE = 'credentials/service-account.json'
DEFAULT_OUTPUT_CSV = 'data/processed/kpis_v2_pipeline.csv'
DEFAULT_OUTPUT_JSON = 'data/processed/dashboard_data.json'
DEFAULT_CONFIG_FILE = 'config.json'

# Google Sheets configuration
DEFAULT_SHEET_NAME = 'dashboard'
SHEETS_RANGE_TEMPLATE = '{sheet_name}!A:Z'  # Read columns A through Z

# Currency metrics (values that need USD to EUR conversion)
CURRENCY_METRICS = [
    'GMV',
    'Funded Amount',
    'Arrangement Fees',
    'Logistic Fees',
    'Accrued Interests',
    'Avg Portfolio Outstanding',
    'Cargo Insurance Costs',
    'Cargo Insurance Fees',
    'Cost of Funds Accrued',
    'Costs Docs Delivery',
    'Docs Management Fees',
    'Handling Warehouse Costs',
    'Handling Warehouse Fees',
    'Logistic Costs',
    'Cash Drag'
]

# Column name mappings for standardization
COLUMN_MAPPINGS = {
    'GMV': 'gmv',
    'Funded Amount': 'funded_amount',
    'Avg Days Outstanding': 'avg_days_outstanding',
    '# Invoices': 'num_invoices',
    '# Boxes': 'num_boxes',
    'month': 'month'
}

# Numeric columns for data processing
NUMERIC_COLUMNS = [
    'gmv',
    'funded_amount',
    'avg_days_outstanding',
    'num_invoices',
    'num_boxes',
    'accrued_interests',
    'arrangement_fees',
    'avg_portfolio_outstanding',
    'cargo_insurance_costs',
    'cargo_insurance_fees',
    'cost_of_funds_accrued',
    'costs_docs_delivery',
    'docs_management_fees',
    'gmv_insured_pct',
    'handling_warehouse_costs',
    'handling_warehouse_fees',
    'logistic_costs',
    'logistic_fees',
    'cash_drag',
    'usd_eur_rate_eom'
]

# Data processing constants
DOWNLOAD_PROGRESS_LOG_INTERVAL = 10  # Log every 10% of download progress
MAX_DOWNLOAD_TIMEOUT = 300  # 5 minutes in seconds
LOG_FILE_MAX_BYTES = 10 * 1024 * 1024  # 10 MB
LOG_FILE_BACKUP_COUNT = 5

# Exchange rate detection keywords
EXCHANGE_RATE_KEYWORDS = ['exch', 'rate', 'eur', 'usd']

# Data validation thresholds
MIN_VALID_ROWS = 1  # Minimum rows required after cleaning
DAYS_OUTSTANDING_EXCELLENT = 20  # Days
DAYS_OUTSTANDING_GOOD = 25  # Days

# Date format patterns
DATE_FORMATS = [
    '%m/%d/%Y',  # M/D/YYYY
    '%B %Y',     # Month Name YYYY
    '%m/%d/%y',  # M/D/YY
    '%b-%y'      # Mon-YY (output format)
]

# Webhook server configuration
WEBHOOK_HOST = '0.0.0.0'
WEBHOOK_PORT = 5000
WEBHOOK_TIMEOUT = 300  # 5 minutes in seconds

# Flask configuration
FLASK_DEBUG = False

# Database Configuration
import os
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///dashboard.db')

# Authentication Constants
TOKEN_EXPIRY_HOURS = 24
MAX_LOGIN_ATTEMPTS = 5
ACCOUNT_LOCKOUT_MINUTES = 15
JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'CHANGE_THIS_IN_PRODUCTION')
JWT_ALGORITHM = 'HS256'

# Password Requirements
MIN_PASSWORD_LENGTH = 8
PASSWORD_REQUIRE_UPPERCASE = True
PASSWORD_REQUIRE_NUMBER = True
PASSWORD_REQUIRE_SPECIAL = True

# Rate Limiting
RATE_LIMITS = {
    'login': '5 per minute',
    'api_default': '10 per minute',
    'webhook': '1 per minute',
    'health': '60 per minute'
}
