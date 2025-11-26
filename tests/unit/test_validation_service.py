"""
Unit tests for ValidationService data quality checks.

Tests cover:
- Missing values detection
- Negative values detection
- Period continuity checks
- Currency rate validation
- Report storage and retrieval
"""
import pytest
import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from scripts.validation_service import ValidationService
from scripts.database import Base
from scripts.models.validation_report import ValidationReport
from scripts.exceptions import ValidationError, DashboardError


@pytest.fixture
def test_db_session():
    """Create an in-memory SQLite database session for testing."""
    # Import all models to register them with Base.metadata
    from scripts.models.user import User
    from scripts.models.audit_log import AuditLog
    from scripts.models.validation_report import ValidationReport

    engine = create_engine('sqlite:///:memory:', echo=False)
    Base.metadata.create_all(engine)
    TestSessionFactory = sessionmaker(bind=engine)
    session = TestSessionFactory()

    yield session

    session.close()
    Base.metadata.drop_all(engine)


@pytest.fixture
def validation_service(test_db_session):
    """Create ValidationService instance with test database session."""
    return ValidationService(test_db_session)


@pytest.fixture
def valid_data():
    """Create valid dashboard data for testing."""
    return pd.DataFrame({
        'month': ['GMV', 'Funded Amount', '# Invoices', 'USD/EUR Rate'],
        'Jan-25': [10000000, 9000000, 50, 0.92],
        'Feb-25': [11000000, 9800000, 55, 0.93],
        'Mar-25': [12000000, 10500000, 60, 0.91]
    })


@pytest.fixture
def data_with_missing_values():
    """Create data with missing values."""
    return pd.DataFrame({
        'month': ['GMV', 'Funded Amount', '# Invoices', 'USD/EUR Rate'],
        'Jan-25': [10000000, 9000000, None, 0.92],  # Missing invoice count
        'Feb-25': [11000000, None, 55, 0.93],  # Missing funded amount
        'Mar-25': [12000000, 10500000, 60, None]  # Missing currency rate
    })


@pytest.fixture
def data_with_negative_values():
    """Create data with negative values."""
    return pd.DataFrame({
        'month': ['GMV', 'Funded Amount', '# Invoices', 'USD/EUR Rate'],
        'Jan-25': [-10000000, 9000000, 50, 0.92],  # Negative GMV
        'Feb-25': [11000000, -9800000, 55, 0.93],  # Negative funded amount
        'Mar-25': [12000000, 10500000, -5, 0.91]  # Negative invoice count
    })


@pytest.fixture
def data_with_invalid_rates():
    """Create data with invalid currency rates."""
    return pd.DataFrame({
        'month': ['GMV', 'Funded Amount', '# Invoices', 'USD/EUR Rate'],
        'Jan-25': [10000000, 9000000, 50, 0.5],  # Rate too low
        'Feb-25': [11000000, 9800000, 55, 1.5],  # Rate too high
        'Mar-25': [12000000, 10500000, 60, 0]  # Rate is zero
    })


# Task 36: Test check_missing_values

class TestCheckMissingValues:
    """Test missing values detection."""

    def test_no_missing_values(self, validation_service, valid_data):
        """Test that valid data has no missing value issues."""
        issues = validation_service.check_missing_values(valid_data)

        assert len(issues) == 0

    def test_empty_dataframe(self, validation_service):
        """Test that empty DataFrame is flagged as critical."""
        empty_data = pd.DataFrame()
        issues = validation_service.check_missing_values(empty_data)

        assert len(issues) == 1
        assert issues[0]['severity'] == 'critical'
        assert 'empty' in issues[0]['message'].lower()

    def test_missing_kpi_values(self, validation_service, data_with_missing_values):
        """Test detection of missing KPI values."""
        issues = validation_service.check_missing_values(data_with_missing_values)

        # Should find missing values in Jan-25, Feb-25, and Mar-25
        assert len(issues) > 0

    def test_missing_currency_rate_critical(self, validation_service, data_with_missing_values):
        """Test that missing currency rate is flagged as critical."""
        issues = validation_service.check_missing_values(data_with_missing_values)

        # Find the currency rate issue
        rate_issues = [i for i in issues if 'rate' in i['message'].lower() or 'mar-25' in i['message'].lower()]
        assert len(rate_issues) > 0
        # Currency rate issues should be critical
        assert any(i['severity'] == 'critical' for i in rate_issues)


# Task 37: Test check_negative_values

class TestCheckNegativeValues:
    """Test negative values detection."""

    def test_no_negative_values(self, validation_service, valid_data):
        """Test that valid data has no negative value issues."""
        issues = validation_service.check_negative_values(valid_data)

        assert len(issues) == 0

    def test_negative_gmv(self, validation_service, data_with_negative_values):
        """Test detection of negative GMV."""
        issues = validation_service.check_negative_values(data_with_negative_values)

        gmv_issues = [i for i in issues if 'GMV' in i['message']]
        assert len(gmv_issues) > 0
        assert gmv_issues[0]['category'] == 'negative_values'

    def test_negative_funded_amount(self, validation_service, data_with_negative_values):
        """Test detection of negative funded amount."""
        issues = validation_service.check_negative_values(data_with_negative_values)

        funded_issues = [i for i in issues if 'Funded Amount' in i['message']]
        assert len(funded_issues) > 0

    def test_negative_invoice_count(self, validation_service, data_with_negative_values):
        """Test detection of negative invoice count."""
        issues = validation_service.check_negative_values(data_with_negative_values)

        invoice_issues = [i for i in issues if '# Invoices' in i['message'] or 'Invoices' in i['message']]
        assert len(invoice_issues) > 0

    def test_empty_dataframe(self, validation_service):
        """Test that empty DataFrame returns no issues."""
        empty_data = pd.DataFrame()
        issues = validation_service.check_negative_values(empty_data)

        assert len(issues) == 0


# Task 38: Test check_period_continuity

class TestCheckPeriodContinuity:
    """Test period continuity checks."""

    def test_continuous_periods(self, validation_service, valid_data):
        """Test that consecutive months have no continuity issues."""
        issues = validation_service.check_period_continuity(valid_data)

        # Should have no continuity issues (Jan-Feb-Mar are consecutive)
        assert len(issues) == 0

    def test_non_continuous_periods(self, validation_service):
        """Test detection of non-consecutive periods."""
        data = pd.DataFrame({
            'month': ['GMV', 'Funded Amount'],
            'Jan-25': [10000000, 9000000],
            'Mar-25': [12000000, 10500000],  # Skipped Feb
            'May-25': [13000000, 11000000]  # Skipped Apr
        })

        issues = validation_service.check_period_continuity(data)

        # Should detect gaps
        gap_issues = [i for i in issues if 'Non-consecutive' in i['message']]
        assert len(gap_issues) > 0

    def test_year_transition(self, validation_service):
        """Test proper handling of year transitions."""
        data = pd.DataFrame({
            'month': ['GMV', 'Funded Amount'],
            'Nov-24': [10000000, 9000000],
            'Dec-24': [11000000, 9800000],
            'Jan-25': [12000000, 10500000]
        })

        issues = validation_service.check_period_continuity(data)

        # Should have no issues with year transition
        continuity_issues = [i for i in issues if 'Non-consecutive' in i['message']]
        assert len(continuity_issues) == 0

    def test_invalid_period_format(self, validation_service):
        """Test detection of invalid period format."""
        data = pd.DataFrame({
            'month': ['GMV'],
            'January-2025': [10000000],  # Wrong format
            'Feb25': [11000000]  # Wrong format
        })

        issues = validation_service.check_period_continuity(data)

        # Should detect format issues
        format_issues = [i for i in issues if 'format' in i['message'].lower()]
        assert len(format_issues) > 0

    def test_single_period(self, validation_service):
        """Test that single period returns info message."""
        data = pd.DataFrame({
            'month': ['GMV'],
            'Jan-25': [10000000]
        })

        issues = validation_service.check_period_continuity(data)

        # Should have info message about not enough periods
        assert len(issues) == 1
        assert issues[0]['severity'] == 'info'


# Task 39: Test check_currency_rates

class TestCheckCurrencyRates:
    """Test currency rate validation."""

    def test_valid_currency_rates(self, validation_service, valid_data):
        """Test that valid currency rates have no issues."""
        issues = validation_service.check_currency_rates(valid_data)

        assert len(issues) == 0

    def test_missing_rate_row(self, validation_service):
        """Test detection of missing USD/EUR Rate row."""
        data = pd.DataFrame({
            'month': ['GMV', 'Funded Amount'],
            'Jan-25': [10000000, 9000000]
        })

        issues = validation_service.check_currency_rates(data)

        assert len(issues) == 1
        assert issues[0]['severity'] == 'critical'
        assert 'not found' in issues[0]['message'].lower()

    def test_rate_out_of_range(self, validation_service, data_with_invalid_rates):
        """Test detection of rates outside reasonable range."""
        issues = validation_service.check_currency_rates(data_with_invalid_rates)

        # Should find issues with too low, too high, and zero rates
        range_issues = [i for i in issues if 'range' in i['message'].lower() or 'zero' in i['message'].lower()]
        assert len(range_issues) > 0

    def test_zero_rate_critical(self, validation_service, data_with_invalid_rates):
        """Test that zero rate is flagged as critical."""
        issues = validation_service.check_currency_rates(data_with_invalid_rates)

        zero_issues = [i for i in issues if 'zero' in i['message'].lower()]
        assert len(zero_issues) > 0
        assert zero_issues[0]['severity'] == 'critical'

    def test_rate_exactly_one(self, validation_service):
        """Test that rate of 1.0 is flagged as info."""
        data = pd.DataFrame({
            'month': ['USD/EUR Rate'],
            'Jan-25': [1.0]
        })

        issues = validation_service.check_currency_rates(data)

        # Should have info message about rate being 1.0
        one_issues = [i for i in issues if '1.0' in i['message']]
        assert len(one_issues) > 0
        assert one_issues[0]['severity'] == 'info'


# Task 40: Test categorize_issues

class TestCategorizeIssues:
    """Test issue categorization."""

    def test_categorize_mixed_issues(self, validation_service):
        """Test categorization of issues by severity."""
        issues = [
            {'severity': 'critical', 'message': 'Critical issue 1'},
            {'severity': 'critical', 'message': 'Critical issue 2'},
            {'severity': 'warning', 'message': 'Warning issue 1'},
            {'severity': 'info', 'message': 'Info issue 1'}
        ]

        summary = validation_service.categorize_issues(issues)

        assert summary['critical'] == 2
        assert summary['warning'] == 1
        assert summary['info'] == 1

    def test_categorize_empty_issues(self, validation_service):
        """Test categorization with no issues."""
        summary = validation_service.categorize_issues([])

        assert summary['critical'] == 0
        assert summary['warning'] == 0
        assert summary['info'] == 0

    def test_categorize_only_warnings(self, validation_service):
        """Test categorization with only warnings."""
        issues = [
            {'severity': 'warning', 'message': 'Warning 1'},
            {'severity': 'warning', 'message': 'Warning 2'},
            {'severity': 'warning', 'message': 'Warning 3'}
        ]

        summary = validation_service.categorize_issues(issues)

        assert summary['critical'] == 0
        assert summary['warning'] == 3
        assert summary['info'] == 0


# Task 35: Test validate_data_quality

class TestValidateDataQuality:
    """Test comprehensive data validation."""

    def test_validate_valid_data(self, validation_service, valid_data):
        """Test validation of clean data."""
        report = validation_service.validate_data_quality(valid_data, 'test_data.csv')

        assert report['status'] == 'pass'
        assert report['summary']['critical'] == 0
        assert report['summary']['warning'] == 0

    def test_validate_data_with_warnings(self, validation_service, data_with_negative_values):
        """Test validation returns warning status."""
        report = validation_service.validate_data_quality(data_with_negative_values)

        assert report['status'] == 'warning'
        assert report['summary']['warning'] > 0

    def test_validate_data_with_critical_issues(self, validation_service, data_with_missing_values):
        """Test validation returns critical status."""
        report = validation_service.validate_data_quality(data_with_missing_values)

        # Missing currency rate should trigger critical status
        assert report['status'] == 'critical'
        assert report['summary']['critical'] > 0

    def test_validate_includes_all_checks(self, validation_service, valid_data):
        """Test that validation runs all check types."""
        report = validation_service.validate_data_quality(valid_data)

        # Report should have structure with all required fields
        assert 'status' in report
        assert 'summary' in report
        assert 'issues' in report
        assert 'timestamp' in report


# Task 41: Test save_validation_report

class TestSaveValidationReport:
    """Test validation report persistence."""

    def test_save_report(self, validation_service, valid_data, test_db_session):
        """Test saving validation report to database."""
        report = validation_service.validate_data_quality(valid_data, 'test.csv')
        saved_report = validation_service.save_validation_report(report)

        assert saved_report.id is not None
        assert saved_report.status == 'pass'
        assert saved_report.data_file == 'test.csv'

    def test_saved_report_retrievable(self, validation_service, valid_data, test_db_session):
        """Test that saved report can be retrieved from database."""
        report = validation_service.validate_data_quality(valid_data)
        saved_report = validation_service.save_validation_report(report)

        # Query database directly
        retrieved = test_db_session.query(ValidationReport).filter(
            ValidationReport.id == saved_report.id
        ).first()

        assert retrieved is not None
        assert retrieved.status == saved_report.status


# Task 42: Test get_validation_reports

class TestGetValidationReports:
    """Test validation report retrieval."""

    def test_get_reports_empty_database(self, validation_service):
        """Test retrieving reports from empty database."""
        reports = validation_service.get_validation_reports()

        assert len(reports) == 0

    def test_get_reports_with_limit(self, validation_service, valid_data):
        """Test retrieving reports with limit."""
        # Create 5 reports
        for i in range(5):
            report = validation_service.validate_data_quality(valid_data, f'file{i}.csv')
            validation_service.save_validation_report(report)

        # Retrieve with limit of 3
        reports = validation_service.get_validation_reports(limit=3)

        assert len(reports) == 3

    def test_get_reports_ordered_by_timestamp(self, validation_service, valid_data):
        """Test that reports are ordered by timestamp (most recent first)."""
        # Create 3 reports
        saved_reports = []
        for i in range(3):
            report = validation_service.validate_data_quality(valid_data, f'file{i}.csv')
            saved = validation_service.save_validation_report(report)
            saved_reports.append(saved)

        # Retrieve reports
        reports = validation_service.get_validation_reports()

        # Should be in reverse order (most recent first)
        assert reports[0].id == saved_reports[-1].id
        assert reports[-1].id == saved_reports[0].id

    def test_get_reports_with_status_filter(self, validation_service, valid_data, data_with_negative_values):
        """Test filtering reports by status."""
        # Create pass and warning reports
        pass_report = validation_service.validate_data_quality(valid_data)
        validation_service.save_validation_report(pass_report)

        warning_report = validation_service.validate_data_quality(data_with_negative_values)
        validation_service.save_validation_report(warning_report)

        # Filter by warning status
        warning_reports = validation_service.get_validation_reports(status_filter='warning')

        assert len(warning_reports) == 1
        assert warning_reports[0].status == 'warning'

    def test_get_reports_invalid_status_filter(self, validation_service):
        """Test that invalid status filter raises ValidationError."""
        with pytest.raises(ValidationError, match='Invalid status filter'):
            validation_service.get_validation_reports(status_filter='invalid')


# Task 43: Test get_latest_validation_report

class TestGetLatestValidationReport:
    """Test latest validation report retrieval."""

    def test_get_latest_empty_database(self, validation_service):
        """Test getting latest report from empty database."""
        report = validation_service.get_latest_validation_report()

        assert report is None

    def test_get_latest_report(self, validation_service, valid_data):
        """Test retrieving the most recent report."""
        # Create 3 reports
        for i in range(3):
            report = validation_service.validate_data_quality(valid_data, f'file{i}.csv')
            validation_service.save_validation_report(report)

        latest = validation_service.get_latest_validation_report()

        assert latest is not None
        assert latest.data_file == 'file2.csv'  # Last one created

    def test_get_latest_returns_most_recent(self, validation_service, valid_data):
        """Test that latest report is truly the most recent."""
        # Create first report
        report1 = validation_service.validate_data_quality(valid_data, 'first.csv')
        saved1 = validation_service.save_validation_report(report1)

        # Create second report
        report2 = validation_service.validate_data_quality(valid_data, 'second.csv')
        saved2 = validation_service.save_validation_report(report2)

        latest = validation_service.get_latest_validation_report()

        assert latest.id == saved2.id
        assert latest.data_file == 'second.csv'
