"""
Data validation service for quality checks and reporting.

Validates dashboard data for missing values, negative amounts,
period continuity, currency rates, and other quality issues.
"""
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
import pandas as pd
from sqlalchemy.orm import Session

from scripts.models.validation_report import ValidationReport
from scripts.exceptions import ValidationError, DashboardError
from scripts.logger_config import get_logger

logger = get_logger(__name__)


class ValidationService:
    """
    Data validation service for quality checks and reporting.

    Performs comprehensive data quality checks on dashboard data
    and stores validation reports in the database.

    Args:
        db_session: SQLAlchemy database session
    """

    def __init__(self, db_session: Session):
        self.db_session = db_session

    def validate_data_quality(
        self,
        data: pd.DataFrame,
        data_file: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Run comprehensive data quality checks on dashboard data.

        Performs all validation checks:
        - Missing values
        - Negative values (for amount fields)
        - Period continuity
        - Currency rates validity

        Args:
            data: DataFrame with dashboard data (wide format)
            data_file: Optional filename for tracking

        Returns:
            dict: Validation report with status, summary, and issues
                {
                    'status': 'pass' | 'warning' | 'critical',
                    'summary': {'critical': 0, 'warning': 2, 'info': 1},
                    'issues': [{'severity': 'warning', 'category': '...', 'message': '...'}]
                }
        """
        issues = []

        # Run all validation checks
        issues.extend(self.check_missing_values(data))
        issues.extend(self.check_negative_values(data))
        issues.extend(self.check_period_continuity(data))
        issues.extend(self.check_currency_rates(data))

        # Categorize issues by severity
        summary = self.categorize_issues(issues)

        # Determine overall status
        if summary['critical'] > 0:
            status = 'critical'
        elif summary['warning'] > 0:
            status = 'warning'
        else:
            status = 'pass'

        report = {
            'status': status,
            'summary': summary,
            'issues': issues,
            'data_file': data_file,
            'timestamp': datetime.utcnow().isoformat()
        }

        logger.info(
            f"Data validation complete: {status} "
            f"(critical={summary['critical']}, warning={summary['warning']}, info={summary['info']})"
        )

        return report

    def check_missing_values(self, data: pd.DataFrame) -> List[Dict[str, str]]:
        """
        Check for missing values in critical fields.

        Args:
            data: DataFrame with dashboard data

        Returns:
            List of issue dictionaries
        """
        issues = []

        # Check if DataFrame is empty
        if data.empty:
            issues.append({
                'severity': 'critical',
                'category': 'missing_data',
                'message': 'Dataset is completely empty'
            })
            return issues

        # Check for missing KPI rows (first column should be KPI names)
        if 'month' in data.columns:
            missing_kpis = data[data['month'].isna()]
            if not missing_kpis.empty:
                issues.append({
                    'severity': 'critical',
                    'category': 'missing_data',
                    'message': f'Found {len(missing_kpis)} rows with missing KPI names'
                })

        # Check for missing values in period columns (all columns except 'month')
        period_columns = [col for col in data.columns if col != 'month']

        # Check for missing currency rates (critical)
        rate_row = data[data['month'] == 'USD/EUR Rate']
        if not rate_row.empty:
            for col in period_columns:
                value = rate_row[col].values[0]
                if pd.isna(value):
                    issues.append({
                        'severity': 'critical',
                        'category': 'missing_data',
                        'message': f'Missing currency rate data in column {col}'
                    })

        # Check for missing KPI values in other rows (warnings)
        for col in period_columns:
            missing_count = data[col].isna().sum()
            # Only count missing values not in the currency rate row (already checked above)
            if missing_count > 0:
                # Count missing values excluding currency rate row
                non_rate_missing = data[(data['month'] != 'USD/EUR Rate') & (data[col].isna())]
                if not non_rate_missing.empty:
                    issues.append({
                        'severity': 'warning',
                        'category': 'missing_data',
                        'message': f'Missing values in column {col}: {len(non_rate_missing)} values'
                    })

        if not issues:
            logger.debug("No missing values found")

        return issues

    def check_negative_values(self, data: pd.DataFrame) -> List[Dict[str, str]]:
        """
        Check for negative values in amount fields where they shouldn't exist.

        Args:
            data: DataFrame with dashboard data

        Returns:
            List of issue dictionaries
        """
        issues = []

        if data.empty:
            return issues

        # Fields that should not have negative values
        positive_only_fields = [
            'GMV', 'Funded Amount', '# Invoices', '# Boxes',
            'USD/EUR Rate'
        ]

        # Get KPI names from 'month' column (first column)
        if 'month' not in data.columns:
            return issues

        for field in positive_only_fields:
            # Find row for this KPI
            kpi_row = data[data['month'] == field]

            if kpi_row.empty:
                continue

            # Check all period columns for negative values
            period_columns = [col for col in data.columns if col != 'month']

            for col in period_columns:
                value = kpi_row[col].values[0]

                # Skip NaN values
                if pd.isna(value):
                    continue

                # Check if value is numeric and negative
                try:
                    numeric_value = float(value)
                    if numeric_value < 0:
                        issues.append({
                            'severity': 'warning',
                            'category': 'negative_values',
                            'message': f'Negative value for {field} in {col}: {numeric_value}'
                        })
                except (ValueError, TypeError):
                    # Non-numeric value
                    issues.append({
                        'severity': 'warning',
                        'category': 'data_type',
                        'message': f'Non-numeric value for {field} in {col}: {value}'
                    })

        if not issues:
            logger.debug("No negative value issues found")

        return issues

    def check_period_continuity(self, data: pd.DataFrame) -> List[Dict[str, str]]:
        """
        Check for gaps or discontinuities in period columns.

        Args:
            data: DataFrame with dashboard data

        Returns:
            List of issue dictionaries
        """
        issues = []

        if data.empty:
            return issues

        # Get period columns (all except 'month')
        period_columns = [col for col in data.columns if col != 'month']

        if len(period_columns) < 2:
            issues.append({
                'severity': 'info',
                'category': 'period_continuity',
                'message': f'Only {len(period_columns)} period(s) found, cannot check continuity'
            })
            return issues

        # Expected format: "Jan-25", "Feb-25", etc.
        # Check if periods follow expected monthly pattern
        month_order = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                       'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

        parsed_periods = []
        for col in period_columns:
            try:
                # Expected format: "MMM-YY"
                if '-' in col:
                    month_part, year_part = col.split('-')
                    if month_part in month_order:
                        parsed_periods.append((month_part, year_part, col))
                    else:
                        issues.append({
                            'severity': 'warning',
                            'category': 'period_continuity',
                            'message': f'Unrecognized month format: {col}'
                        })
                else:
                    issues.append({
                        'severity': 'warning',
                        'category': 'period_continuity',
                        'message': f'Period column does not match expected format (MMM-YY): {col}'
                    })
            except Exception as e:
                issues.append({
                    'severity': 'warning',
                    'category': 'period_continuity',
                    'message': f'Error parsing period column {col}: {str(e)}'
                })

        # Check for proper month sequence (allowing year transitions)
        if len(parsed_periods) > 1:
            for i in range(len(parsed_periods) - 1):
                current_month, current_year, current_col = parsed_periods[i]
                next_month, next_year, next_col = parsed_periods[i + 1]

                current_idx = month_order.index(current_month)
                next_idx = month_order.index(next_month)

                # Check if months are consecutive
                expected_next_idx = (current_idx + 1) % 12
                expected_next_year = current_year if current_idx < 11 else str(int(current_year) + 1)

                if next_idx != expected_next_idx or next_year != expected_next_year:
                    issues.append({
                        'severity': 'info',
                        'category': 'period_continuity',
                        'message': f'Non-consecutive periods: {current_col} -> {next_col}'
                    })

        if not issues:
            logger.debug("No period continuity issues found")

        return issues

    def check_currency_rates(self, data: pd.DataFrame) -> List[Dict[str, str]]:
        """
        Check currency rates for validity (reasonable ranges).

        Args:
            data: DataFrame with dashboard data

        Returns:
            List of issue dictionaries
        """
        issues = []

        if data.empty or 'month' not in data.columns:
            return issues

        # Find USD/EUR rate row
        rate_row = data[data['month'] == 'USD/EUR Rate']

        if rate_row.empty:
            issues.append({
                'severity': 'critical',
                'category': 'currency_rates',
                'message': 'USD/EUR Rate row not found in data'
            })
            return issues

        # Check all period columns
        period_columns = [col for col in data.columns if col != 'month']

        # Reasonable range for USD/EUR rate (last 10 years: ~0.7 to ~1.3)
        MIN_RATE = 0.7
        MAX_RATE = 1.3

        for col in period_columns:
            value = rate_row[col].values[0]

            # Skip NaN values (already caught by missing values check)
            if pd.isna(value):
                continue

            try:
                numeric_value = float(value)

                # Check if rate is in reasonable range
                if numeric_value < MIN_RATE or numeric_value > MAX_RATE:
                    issues.append({
                        'severity': 'warning',
                        'category': 'currency_rates',
                        'message': f'USD/EUR rate out of expected range ({MIN_RATE}-{MAX_RATE}) in {col}: {numeric_value}'
                    })

                # Check if rate is exactly 0 or 1 (likely error)
                if numeric_value == 0:
                    issues.append({
                        'severity': 'critical',
                        'category': 'currency_rates',
                        'message': f'USD/EUR rate is zero in {col}'
                    })
                elif numeric_value == 1.0:
                    issues.append({
                        'severity': 'info',
                        'category': 'currency_rates',
                        'message': f'USD/EUR rate is exactly 1.0 in {col} (verify if correct)'
                    })

            except (ValueError, TypeError):
                issues.append({
                    'severity': 'critical',
                    'category': 'currency_rates',
                    'message': f'Non-numeric currency rate in {col}: {value}'
                })

        if not issues:
            logger.debug("No currency rate issues found")

        return issues

    def categorize_issues(self, issues: List[Dict[str, str]]) -> Dict[str, int]:
        """
        Categorize issues by severity level.

        Args:
            issues: List of issue dictionaries with 'severity' key

        Returns:
            dict: Count of issues by severity {'critical': 0, 'warning': 2, 'info': 1}
        """
        summary = {
            'critical': 0,
            'warning': 0,
            'info': 0
        }

        for issue in issues:
            severity = issue.get('severity', 'info')
            if severity in summary:
                summary[severity] += 1

        return summary

    def save_validation_report(self, report: Dict[str, Any]) -> ValidationReport:
        """
        Save validation report to database.

        Args:
            report: Validation report dictionary from validate_data_quality

        Returns:
            ValidationReport: Saved report object

        Raises:
            DashboardError: If database operation fails
        """
        try:
            validation_report = ValidationReport(
                status=report['status'],
                summary=json.dumps(report['summary']),
                issues=json.dumps(report['issues']),
                data_file=report.get('data_file')
            )

            self.db_session.add(validation_report)
            self.db_session.commit()
            self.db_session.refresh(validation_report)

            logger.info(f"Validation report saved: ID={validation_report.id}, status={report['status']}")
            return validation_report

        except Exception as e:
            self.db_session.rollback()
            logger.error(f"Failed to save validation report: {e}")
            raise DashboardError(f'Failed to save validation report: {str(e)}')

    def get_validation_reports(
        self,
        limit: int = 10,
        status_filter: Optional[str] = None
    ) -> List[ValidationReport]:
        """
        Retrieve validation reports from database.

        Args:
            limit: Maximum number of reports to return (default: 10)
            status_filter: Filter by status ('pass', 'warning', 'critical')

        Returns:
            List of ValidationReport objects (most recent first)

        Raises:
            DashboardError: If database operation fails
        """
        try:
            query = self.db_session.query(ValidationReport)

            # Filter by status if provided
            if status_filter:
                if status_filter not in ['pass', 'warning', 'critical']:
                    raise ValidationError(f'Invalid status filter: {status_filter}')
                query = query.filter(ValidationReport.status == status_filter)

            # Order by timestamp (most recent first) and limit
            reports = query.order_by(ValidationReport.timestamp.desc()).limit(limit).all()

            logger.debug(f"Retrieved {len(reports)} validation reports")
            return reports

        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Failed to retrieve validation reports: {e}")
            raise DashboardError(f'Failed to retrieve validation reports: {str(e)}')

    def get_latest_validation_report(self) -> Optional[ValidationReport]:
        """
        Get the most recent validation report.

        Returns:
            ValidationReport object or None if no reports exist

        Raises:
            DashboardError: If database operation fails
        """
        try:
            report = (
                self.db_session.query(ValidationReport)
                .order_by(ValidationReport.timestamp.desc())
                .first()
            )

            if report:
                logger.debug(f"Retrieved latest validation report: ID={report.id}")
            else:
                logger.debug("No validation reports found")

            return report

        except Exception as e:
            logger.error(f"Failed to retrieve latest validation report: {e}")
            raise DashboardError(f'Failed to retrieve latest validation report: {str(e)}')
