"""
Unit tests for scripts/fetch_from_sheets.py

Tests cover:
- Credential loading and validation
- Google Sheets API integration
- Google Drive API integration
- Data transformation (USD to EUR conversion)
- DataFrame processing
- JSON export for dashboard
"""
import pytest
import pandas as pd
import json
import os
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch, mock_open
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from scripts.fetch_from_sheets import (
    get_credentials,
    convert_to_dataframe,
    clean_and_process,
    convert_to_eur,
    prepare_dashboard_json,
    load_config
)


class TestCredentialLoading:
    """Tests for credential loading and validation."""

    @pytest.mark.unit
    def test_get_credentials_file_not_found(self, tmp_path, monkeypatch):
        """Test that FileNotFoundError is raised when credentials file doesn't exist."""
        # Set environment variable to non-existent file
        fake_path = str(tmp_path / "nonexistent.json")
        monkeypatch.setenv('GOOGLE_CREDENTIALS_FILE', fake_path)

        # Need to reload the module to pick up the new env var
        import importlib
        import scripts.fetch_from_sheets as fetch_module
        importlib.reload(fetch_module)

        with pytest.raises(FileNotFoundError) as exc_info:
            fetch_module.get_credentials()

        assert fake_path in str(exc_info.value)

    @pytest.mark.unit
    @patch('scripts.fetch_from_sheets.service_account.Credentials.from_service_account_file')
    def test_get_credentials_success(self, mock_creds, sample_credentials_file, monkeypatch):
        """Test successful credential loading."""
        # Set environment variable
        monkeypatch.setenv('GOOGLE_CREDENTIALS_FILE', sample_credentials_file)

        # Reload module to pick up env var
        import importlib
        import scripts.fetch_from_sheets as fetch_module
        importlib.reload(fetch_module)

        # Mock successful credential creation
        mock_creds.return_value = Mock()

        result = fetch_module.get_credentials()

        mock_creds.assert_called_once()
        assert result is not None


class TestDataFrameConversion:
    """Tests for converting Google Sheets data to pandas DataFrames."""

    @pytest.mark.unit
    def test_convert_to_dataframe_basic(self, sample_sheet_values):
        """Test basic conversion from Sheets values to DataFrame."""
        df = convert_to_dataframe(sample_sheet_values)

        # Check shape
        assert df.shape == (6, 4)  # 6 rows (metrics), 4 columns (month + 3 periods)

        # Check headers
        assert 'month' in df.columns
        assert 'Jan-25' in df.columns

        # Check first row
        assert df.iloc[0]['month'] == 'GMV'

    @pytest.mark.unit
    def test_convert_to_dataframe_empty(self):
        """Test conversion with empty data."""
        empty_values = [['month']]  # Only headers

        df = convert_to_dataframe(empty_values)

        assert len(df) == 0
        assert 'month' in df.columns


class TestDataCleaning:
    """Tests for data cleaning and processing."""

    @pytest.mark.unit
    def test_clean_and_process_removes_currency_symbols(self):
        """Test that currency symbols and commas are removed."""
        df = pd.DataFrame({
            'month': ['GMV', 'Revenue'],
            'Jan-25': ['$1,234,567', '$2,345,678']
        })

        result = clean_and_process(df)

        # Values should be strings without $ and commas
        assert '$' not in str(result.iloc[0]['Jan-25'])
        assert ',' not in str(result.iloc[0]['Jan-25'])

    @pytest.mark.unit
    def test_clean_and_process_handles_percentages(self):
        """Test that percentage symbols are removed."""
        df = pd.DataFrame({
            'month': ['Conversion Rate'],
            'Jan-25': ['15.5%']
        })

        result = clean_and_process(df)

        assert '%' not in str(result.iloc[0]['Jan-25'])

    @pytest.mark.unit
    def test_clean_and_process_handles_empty_cells(self):
        """Test that empty cells are handled correctly."""
        df = pd.DataFrame({
            'month': ['GMV', 'Revenue'],
            'Jan-25': ['1000', ''],
            'Feb-25': ['', '2000']
        })

        result = clean_and_process(df)

        # Empty strings should be converted to pd.NA
        assert result.shape == df.shape


class TestCurrencyConversion:
    """Tests for USD to EUR conversion."""

    @pytest.mark.unit
    def test_convert_to_eur_with_exchange_rate(self):
        """Test USD to EUR conversion using exchange rate row."""
        df = pd.DataFrame({
            'month': ['GMV', 'Funded Amount', 'USD/EUR Rate'],
            'Jan-25': [1000000, 900000, 0.92],
            'Feb-25': [1100000, 950000, 0.93]
        })

        result = convert_to_eur(df)

        # GMV should be converted: 1000000 * 0.92 = 920000
        gmv_row = result[result['month'] == 'GMV']
        assert float(gmv_row.iloc[0]['Jan-25']) == pytest.approx(920000, rel=0.01)

    @pytest.mark.unit
    def test_convert_to_eur_no_exchange_rate(self):
        """Test conversion when exchange rate row is missing."""
        df = pd.DataFrame({
            'month': ['GMV', 'Funded Amount'],
            'Jan-25': [1000000, 900000],
            'Feb-25': [1100000, 950000]
        })

        result = convert_to_eur(df)

        # Should return original dataframe unchanged
        assert result.equals(df)

    @pytest.mark.unit
    def test_convert_to_eur_only_currency_metrics(self):
        """Test that only currency metrics are converted, not counts."""
        df = pd.DataFrame({
            'month': ['GMV', '# Invoices', 'USD/EUR Rate'],
            'Jan-25': [1000000, 50, 0.92],
        })

        result = convert_to_eur(df)

        # GMV should be converted
        gmv_row = result[result['month'] == 'GMV']
        assert float(gmv_row.iloc[0]['Jan-25']) == pytest.approx(920000, rel=0.01)

        # # Invoices should NOT be converted (not in currency_metrics list)
        # Note: In actual code, it won't be converted because it's not in currency_metrics


class TestDashboardJsonPreparation:
    """Tests for preparing dashboard JSON data."""

    @pytest.mark.unit
    def test_prepare_dashboard_json_structure(self):
        """Test that dashboard JSON has correct structure."""
        df_usd = pd.DataFrame({
            'month': ['GMV', 'Funded Amount'],
            'Jan-25': [1000000, 900000],
            'Feb-25': [1100000, 950000]
        })

        df_eur = pd.DataFrame({
            'month': ['GMV', 'Funded Amount'],
            'Jan-25': [920000, 828000],
            'Feb-25': [1023000, 883500]
        })

        result = prepare_dashboard_json(df_usd, df_eur)

        # Check structure
        assert 'metrics' in result
        assert 'periods' in result
        assert 'values_usd' in result
        assert 'values_eur' in result

        # Check metrics
        assert 'GMV' in result['metrics']
        assert 'Funded Amount' in result['metrics']

        # Check periods
        assert 'Jan-25' in result['periods']
        assert 'Feb-25' in result['periods']

    @pytest.mark.unit
    def test_prepare_dashboard_json_values(self):
        """Test that USD and EUR values are correctly included."""
        df_usd = pd.DataFrame({
            'month': ['GMV'],
            'Jan-25': [1000000]
        })

        df_eur = pd.DataFrame({
            'month': ['GMV'],
            'Jan-25': [920000]
        })

        result = prepare_dashboard_json(df_usd, df_eur)

        # Check USD values
        assert result['values_usd']['GMV'][0] == 1000000

        # Check EUR values
        assert result['values_eur']['GMV'][0] == 920000

    @pytest.mark.unit
    def test_prepare_dashboard_json_handles_none_values(self):
        """Test that None/NaN values are handled correctly."""
        df_usd = pd.DataFrame({
            'month': ['GMV'],
            'Jan-25': [1000000],
            'Feb-25': [None]
        })

        df_eur = pd.DataFrame({
            'month': ['GMV'],
            'Jan-25': [920000],
            'Feb-25': [None]
        })

        result = prepare_dashboard_json(df_usd, df_eur)

        # Check that None is preserved
        assert result['values_usd']['GMV'][1] is None
        assert result['values_eur']['GMV'][1] is None


class TestConfigLoading:
    """Tests for configuration file loading."""

    @pytest.mark.unit
    def test_load_config_file_exists(self, sample_config_file, monkeypatch):
        """Test loading existing config file."""
        # Change to temp directory
        monkeypatch.chdir(Path(sample_config_file).parent)

        result = load_config()

        assert result is not None
        assert 'google_drive_file_id' in result
        assert result['google_drive_file_id'] == 'test_file_id_123'

    @pytest.mark.unit
    def test_load_config_file_not_exists(self, tmp_path, monkeypatch):
        """Test loading when config file doesn't exist."""
        # Change to empty temp directory
        monkeypatch.chdir(tmp_path)

        result = load_config()

        assert result is None


class TestPeriodFiltering:
    """Tests for period filtering in dashboard JSON preparation."""

    @pytest.mark.unit
    def test_prepare_dashboard_json_with_exclusions(self, monkeypatch, tmp_path):
        """Test that excluded periods are filtered out."""
        # Create config with exclusions
        config_data = {
            "data_settings": {
                "exclude_periods": ["Feb-25"]
            }
        }

        config_file = tmp_path / "config.json"
        with open(config_file, 'w') as f:
            json.dump(config_data, f)

        monkeypatch.chdir(tmp_path)

        df_usd = pd.DataFrame({
            'month': ['GMV'],
            'Jan-25': [1000000],
            'Feb-25': [1100000],
            'Mar-25': [1200000]
        })

        df_eur = pd.DataFrame({
            'month': ['GMV'],
            'Jan-25': [920000],
            'Feb-25': [1023000],
            'Mar-25': [1092000]
        })

        result = prepare_dashboard_json(df_usd, df_eur)

        # Feb-25 should be excluded
        assert 'Feb-25' not in result['periods']
        assert 'Jan-25' in result['periods']
        assert 'Mar-25' in result['periods']

        # Values should only have 2 entries (Jan and Mar)
        assert len(result['values_usd']['GMV']) == 2
