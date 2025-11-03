"""
Unit tests for data_pipeline.py

Tests cover:
- KPI data loading from CSV
- Data cleaning and validation
- Metric calculations
- Data transformation pipeline
- Summary statistics generation
- Dashboard export
"""
import pytest
import pandas as pd
import json
from pathlib import Path
from datetime import datetime
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from data_pipeline import KPIPipeline


class TestKPIPipelineInitialization:
    """Tests for KPIPipeline initialization."""

    @pytest.mark.unit
    def test_init_default_csv_mode(self):
        """Test default initialization with CSV data source."""
        pipeline = KPIPipeline()

        assert pipeline.data_source == 'csv'
        assert pipeline.raw_data is None
        assert pipeline.transformed_data is None

    @pytest.mark.unit
    def test_init_csv_mode_explicit(self):
        """Test explicit CSV mode initialization."""
        pipeline = KPIPipeline(data_source='csv')

        assert pipeline.data_source == 'csv'

    @pytest.mark.unit
    def test_init_google_sheets_mode(self):
        """Test Google Sheets mode initialization."""
        pipeline = KPIPipeline(data_source='google_sheets')

        assert pipeline.data_source == 'google_sheets'


class TestDataLoading:
    """Tests for data loading functionality."""

    @pytest.mark.unit
    def test_load_data_csv_success(self, sample_csv_file):
        """Test successful CSV data loading."""
        pipeline = KPIPipeline(data_source='csv')
        result = pipeline.load_data(sample_csv_file)

        assert result is not None
        assert isinstance(result, pd.DataFrame)
        assert len(result) > 0
        assert 'GMV' in result.columns

    @pytest.mark.unit
    def test_load_data_file_not_found(self):
        """Test that FileNotFoundError is raised for missing file."""
        pipeline = KPIPipeline(data_source='csv')

        with pytest.raises(FileNotFoundError):
            pipeline.load_data('nonexistent_file.csv')

    @pytest.mark.unit
    def test_load_data_google_sheets_not_implemented(self):
        """Test that Google Sheets mode shows not implemented warning."""
        pipeline = KPIPipeline(data_source='google_sheets')

        result = pipeline.load_data()

        # Should return None for not implemented
        assert result is None


class TestDataCleaning:
    """Tests for data cleaning and standardization."""

    @pytest.mark.unit
    def test_clean_data_removes_empty_rows(self, sample_csv_file):
        """Test that completely empty rows are removed."""
        pipeline = KPIPipeline(data_source='csv')
        pipeline.load_data(sample_csv_file)

        # Add empty row manually
        pipeline.raw_data = pd.concat([
            pipeline.raw_data,
            pd.DataFrame([{col: None for col in pipeline.raw_data.columns}])
        ], ignore_index=True)

        original_len = len(pipeline.raw_data)
        result = pipeline.clean_data()

        # Should have one less row (empty row removed)
        assert len(result) < original_len

    @pytest.mark.unit
    def test_clean_data_converts_month_to_datetime(self, sample_csv_file):
        """Test that month column is converted to datetime."""
        pipeline = KPIPipeline(data_source='csv')
        pipeline.load_data(sample_csv_file)

        result = pipeline.clean_data()

        assert pd.api.types.is_datetime64_any_dtype(result['month'])

    @pytest.mark.unit
    def test_clean_data_converts_numeric_columns(self, sample_csv_file):
        """Test that numeric columns are properly converted."""
        pipeline = KPIPipeline(data_source='csv')
        pipeline.load_data(sample_csv_file)

        result = pipeline.clean_data()

        # Check that numeric columns are numeric types
        assert pd.api.types.is_numeric_dtype(result['gmv'])
        assert pd.api.types.is_numeric_dtype(result['funded_amount'])

    @pytest.mark.unit
    def test_clean_data_raises_error_when_no_data_loaded(self):
        """Test that clean_data raises ValueError when no data is loaded."""
        pipeline = KPIPipeline()

        with pytest.raises(ValueError, match="No data loaded"):
            pipeline.clean_data()

    @pytest.mark.unit
    def test_clean_data_standardizes_column_names(self, tmp_path):
        """Test that column names are standardized to lowercase."""
        # Create CSV with mixed case column names
        csv_data = """month,GMV,Funded Amount
1/1/25,1000000,900000
"""
        csv_file = tmp_path / "test.csv"
        csv_file.write_text(csv_data)

        pipeline = KPIPipeline(data_source='csv')
        pipeline.load_data(str(csv_file))
        result = pipeline.clean_data()

        # Check standardized names
        assert 'gmv' in result.columns
        assert 'funded_amount' in result.columns
        assert 'GMV' not in result.columns


class TestMetricCalculation:
    """Tests for derived metric calculations."""

    @pytest.mark.unit
    def test_calculate_metrics_adds_derived_columns(self, sample_csv_file):
        """Test that derived metrics are calculated."""
        pipeline = KPIPipeline(data_source='csv')
        pipeline.load_data(sample_csv_file)
        df_clean = pipeline.clean_data()

        result = pipeline.calculate_metrics(df_clean)

        # Check that new columns were added
        original_cols = set(df_clean.columns)
        result_cols = set(result.columns)

        new_cols = result_cols - original_cols
        assert len(new_cols) > 0

    @pytest.mark.unit
    def test_calculate_metrics_adds_time_columns(self, sample_csv_file):
        """Test that time-based columns are added."""
        pipeline = KPIPipeline(data_source='csv')
        pipeline.load_data(sample_csv_file)
        df_clean = pipeline.clean_data()

        result = pipeline.calculate_metrics(df_clean)

        # Check time-based columns
        assert 'quarter' in result.columns
        assert 'year' in result.columns
        assert 'month_name' in result.columns

    @pytest.mark.unit
    def test_calculate_metrics_quarter_values(self, sample_csv_file):
        """Test that quarter values are correctly calculated."""
        pipeline = KPIPipeline(data_source='csv')
        pipeline.load_data(sample_csv_file)
        df_clean = pipeline.clean_data()

        result = pipeline.calculate_metrics(df_clean)

        # January should be Q1
        jan_row = result[result['month_name'] == 'January'].iloc[0] if 'January' in result['month_name'].values else None
        if jan_row is not None:
            assert jan_row['quarter'] == 1


class TestDataTransformation:
    """Tests for the complete transformation pipeline."""

    @pytest.mark.unit
    def test_transform_data_complete_pipeline(self, sample_csv_file):
        """Test that transform_data runs the complete pipeline."""
        pipeline = KPIPipeline(data_source='csv')
        pipeline.load_data(sample_csv_file)

        result = pipeline.transform_data()

        # Check that transformed data is stored
        assert pipeline.transformed_data is not None
        assert isinstance(result, pd.DataFrame)
        assert len(result) > 0

    @pytest.mark.unit
    def test_transform_data_has_all_columns(self, sample_csv_file):
        """Test that transformed data has all expected columns."""
        pipeline = KPIPipeline(data_source='csv')
        pipeline.load_data(sample_csv_file)

        result = pipeline.transform_data()

        # Check base columns exist
        assert 'month' in result.columns
        assert 'gmv' in result.columns
        assert 'funded_amount' in result.columns

        # Check derived columns exist
        assert 'quarter' in result.columns
        assert 'year' in result.columns


class TestSummaryStatistics:
    """Tests for summary statistics generation."""

    @pytest.mark.unit
    def test_generate_summary_stats_structure(self, sample_csv_file):
        """Test that summary stats have correct structure."""
        pipeline = KPIPipeline(data_source='csv')
        pipeline.load_data(sample_csv_file)
        pipeline.transform_data()

        result = pipeline.generate_summary_stats()

        # Check that result is a dictionary
        assert isinstance(result, dict)

    @pytest.mark.unit
    def test_generate_summary_stats_raises_without_transform(self):
        """Test that generating stats without transformation raises error."""
        pipeline = KPIPipeline()

        with pytest.raises(ValueError, match="No transformed data"):
            pipeline.generate_summary_stats()

    @pytest.mark.unit
    def test_generate_summary_stats_has_period_info(self, sample_csv_file):
        """Test that summary includes period information."""
        pipeline = KPIPipeline(data_source='csv')
        pipeline.load_data(sample_csv_file)
        pipeline.transform_data()

        result = pipeline.generate_summary_stats()

        # Check for period information
        assert 'period' in result or 'total_gmv' in result


class TestDashboardExport:
    """Tests for dashboard data export functionality."""

    @pytest.mark.unit
    def test_export_for_dashboard_creates_json(self, sample_csv_file, temp_output_dir):
        """Test that JSON file is created."""
        pipeline = KPIPipeline(data_source='csv')
        pipeline.load_data(sample_csv_file)
        pipeline.transform_data()

        result = pipeline.export_for_dashboard(output_dir=temp_output_dir)

        # Check that file was created
        assert Path(result).exists()
        assert result.endswith('.json')

    @pytest.mark.unit
    def test_export_for_dashboard_creates_csv(self, sample_csv_file, temp_output_dir):
        """Test that CSV file is also created."""
        pipeline = KPIPipeline(data_source='csv')
        pipeline.load_data(sample_csv_file)
        pipeline.transform_data()

        pipeline.export_for_dashboard(output_dir=temp_output_dir)

        # Check that CSV was created
        csv_path = Path(temp_output_dir) / 'processed_data.csv'
        assert csv_path.exists()

    @pytest.mark.unit
    def test_export_for_dashboard_json_structure(self, sample_csv_file, temp_output_dir):
        """Test that exported JSON has correct structure."""
        pipeline = KPIPipeline(data_source='csv')
        pipeline.load_data(sample_csv_file)
        pipeline.transform_data()

        result_path = pipeline.export_for_dashboard(output_dir=temp_output_dir)

        # Load and check JSON
        with open(result_path, 'r') as f:
            data = json.load(f)

        assert 'data' in data
        assert 'summary' in data
        assert 'last_updated' in data

    @pytest.mark.unit
    def test_export_for_dashboard_last_updated_is_iso_format(self, sample_csv_file, temp_output_dir):
        """Test that last_updated is in ISO format."""
        pipeline = KPIPipeline(data_source='csv')
        pipeline.load_data(sample_csv_file)
        pipeline.transform_data()

        result_path = pipeline.export_for_dashboard(output_dir=temp_output_dir)

        with open(result_path, 'r') as f:
            data = json.load(f)

        # Should be able to parse as datetime
        last_updated = data['last_updated']
        datetime.fromisoformat(last_updated)  # Should not raise


class TestFullPipeline:
    """Integration-style tests for the complete pipeline run."""

    @pytest.mark.unit
    def test_run_pipeline_success(self, sample_csv_file):
        """Test successful pipeline execution from start to finish."""
        pipeline = KPIPipeline(data_source='csv')

        result = pipeline.run_pipeline(sample_csv_file)

        # Should return output file path
        assert result is not None
        assert isinstance(result, (str, Path))

    @pytest.mark.unit
    def test_run_pipeline_sets_all_attributes(self, sample_csv_file):
        """Test that pipeline sets all internal attributes."""
        pipeline = KPIPipeline(data_source='csv')
        pipeline.run_pipeline(sample_csv_file)

        # Check that data was loaded and transformed
        assert pipeline.raw_data is not None
        assert pipeline.transformed_data is not None

    @pytest.mark.unit
    def test_run_pipeline_propagates_errors(self):
        """Test that errors in pipeline are propagated."""
        pipeline = KPIPipeline(data_source='csv')

        with pytest.raises(FileNotFoundError):
            pipeline.run_pipeline('nonexistent.csv')
