"""
Shared pytest fixtures and configuration for all tests.

This module provides common fixtures that can be used across all test files.
"""
import pytest
import pandas as pd
import json
import os
from pathlib import Path
from datetime import datetime
from unittest.mock import Mock, MagicMock


@pytest.fixture
def sample_kpi_data():
    """Sample KPI data in wide format (like the actual data source)."""
    return pd.DataFrame({
        'month': ['GMV', 'Funded Amount', 'Avg Days Outstanding', '# Invoices', '# Boxes', 'USD/EUR Rate'],
        'Jan-25': [11352846, 10107543, 18, 54, 91, 0.92],
        'Feb-25': [12500000, 11200000, 19, 58, 95, 0.93],
        'Mar-25': [13000000, 11700000, 17, 62, 98, 0.91]
    })


@pytest.fixture
def sample_sheet_values():
    """Sample data as returned by Google Sheets API."""
    return [
        ['month', 'Jan-25', 'Feb-25', 'Mar-25'],
        ['GMV', '11352846', '12500000', '13000000'],
        ['Funded Amount', '10107543', '11200000', '11700000'],
        ['Avg Days Outstanding', '18', '19', '17'],
        ['# Invoices', '54', '58', '62'],
        ['# Boxes', '91', '95', '98'],
        ['USD/EUR Rate', '0.92', '0.93', '0.91']
    ]


@pytest.fixture
def sample_credentials_file(tmp_path):
    """Create a temporary Google credentials file."""
    creds_data = {
        "type": "service_account",
        "project_id": "test-project",
        "private_key_id": "test-key-id",
        "private_key": "-----BEGIN PRIVATE KEY-----\ntest-key\n-----END PRIVATE KEY-----\n",
        "client_email": "test@test-project.iam.gserviceaccount.com",
        "client_id": "123456789",
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs"
    }

    creds_file = tmp_path / "test_credentials.json"
    with open(creds_file, 'w') as f:
        json.dump(creds_data, f)

    return str(creds_file)


@pytest.fixture
def sample_config_file(tmp_path):
    """Create a temporary config.json file."""
    config_data = {
        "google_drive_file_id": "test_file_id_123",
        "sheet_name": "dashboard",
        "credentials_file": "credentials/test.json",
        "data_settings": {
            "include_periods_through": "Sep-25",
            "exclude_periods": ["Oct-25", "Nov-25", "Dec-25"]
        }
    }

    config_file = tmp_path / "config.json"
    with open(config_file, 'w') as f:
        json.dump(config_data, f)

    return str(config_file)


@pytest.fixture
def mock_google_sheets_service():
    """Mock Google Sheets API service."""
    mock_service = MagicMock()

    # Mock spreadsheet metadata
    mock_service.spreadsheets().get().execute.return_value = {
        'sheets': [
            {'properties': {'title': 'dashboard'}},
            {'properties': {'title': 'Sheet1'}}
        ]
    }

    # Mock sheet values
    mock_service.spreadsheets().values().get().execute.return_value = {
        'values': [
            ['month', 'Jan-25', 'Feb-25'],
            ['GMV', '11352846', '12500000'],
            ['Funded Amount', '10107543', '11200000']
        ]
    }

    return mock_service


@pytest.fixture
def mock_google_drive_service():
    """Mock Google Drive API service."""
    mock_service = MagicMock()

    # Mock file metadata
    mock_service.files().get().execute.return_value = {
        'name': 'test_file.xlsx',
        'mimeType': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    }

    return mock_service


@pytest.fixture
def sample_csv_file(tmp_path):
    """Create a temporary CSV file with sample KPI data."""
    csv_data = """month,GMV,Funded Amount,Avg Days Outstanding,# Invoices,# Boxes
1/1/25,11352846,10107543,18,54,91
2/1/25,12500000,11200000,19,58,95
3/1/25,13000000,11700000,17,62,98
"""
    csv_file = tmp_path / "test_data.csv"
    csv_file.write_text(csv_data)
    return str(csv_file)


@pytest.fixture
def sample_dashboard_json():
    """Sample dashboard JSON data structure."""
    return {
        'metrics': ['GMV', 'Funded Amount', 'Avg Days Outstanding'],
        'periods': ['Jan-25', 'Feb-25', 'Mar-25'],
        'values_usd': {
            'GMV': [11352846, 12500000, 13000000],
            'Funded Amount': [10107543, 11200000, 11700000],
            'Avg Days Outstanding': [18, 19, 17]
        },
        'values_eur': {
            'GMV': [10444618.32, 11625000, 11830000],
            'Funded Amount': [9298939.56, 10416000, 10647000],
            'Avg Days Outstanding': [18, 19, 17]
        }
    }


@pytest.fixture
def temp_output_dir(tmp_path):
    """Create temporary output directories."""
    output_dir = tmp_path / "data" / "processed"
    output_dir.mkdir(parents=True, exist_ok=True)
    return str(output_dir)


@pytest.fixture(autouse=True)
def reset_environment():
    """Reset environment variables before each test."""
    # Store original environment
    original_env = os.environ.copy()

    # Set test environment variables
    os.environ['TESTING'] = 'true'
    os.environ['LOG_LEVEL'] = 'WARNING'

    yield

    # Restore original environment
    os.environ.clear()
    os.environ.update(original_env)


@pytest.fixture
def mock_logger(mocker):
    """Mock logger to verify logging calls without actual output."""
    return mocker.patch('scripts.logger_config.get_logger')


# Helper functions for tests

def assert_dataframe_equal(df1: pd.DataFrame, df2: pd.DataFrame, **kwargs):
    """
    Assert two dataframes are equal with better error messages.

    Args:
        df1: First dataframe
        df2: Second dataframe
        **kwargs: Additional arguments passed to pd.testing.assert_frame_equal
    """
    try:
        pd.testing.assert_frame_equal(df1, df2, **kwargs)
    except AssertionError as e:
        print(f"\nDataFrame comparison failed:")
        print(f"Expected shape: {df1.shape}, Got shape: {df2.shape}")
        print(f"Expected columns: {list(df1.columns)}")
        print(f"Got columns: {list(df2.columns)}")
        raise e


def create_test_excel_file(data: dict, file_path: Path, sheet_name: str = 'Sheet1'):
    """
    Create a test Excel file with given data.

    Args:
        data: Dictionary of data to write
        file_path: Path where to save the file
        sheet_name: Name of the sheet
    """
    df = pd.DataFrame(data)
    df.to_excel(file_path, sheet_name=sheet_name, index=False)
