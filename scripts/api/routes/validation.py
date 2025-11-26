"""
Validation routes for data quality checks and reports.

Endpoints:
- GET /api/validation/reports - List validation reports
- GET /api/validation/reports/latest - Get latest validation report
- GET /api/validation/reports/<id> - Get specific validation report
"""
from flask import Blueprint, request, jsonify

from scripts.database import get_session
from scripts.validation_service import ValidationService
from scripts.api.app import require_auth
from scripts.logger_config import get_logger

logger = get_logger(__name__)

validation_bp = Blueprint('validation', __name__)


# Task 53: Validation routes
@validation_bp.route('/reports', methods=['GET'])
@require_auth
def list_validation_reports():
    """
    List validation reports.

    Query parameters:
        - limit: Maximum number of reports (default: 10)
        - status: Filter by status (pass, warning, critical)

    Response:
        {
            "reports": [
                {
                    "id": 1,
                    "timestamp": "2025-01-22T10:30:00Z",
                    "status": "pass",
                    "summary": {"critical": 0, "warning": 0, "info": 0},
                    "data_file": "dashboard_data.csv"
                }
            ]
        }
    """
    db_session = get_session()

    try:
        # Get query parameters
        limit = request.args.get('limit', 10, type=int)
        status_filter = request.args.get('status')

        # List reports
        validation_service = ValidationService(db_session)
        reports = validation_service.get_validation_reports(
            limit=limit,
            status_filter=status_filter
        )

        return jsonify({
            'reports': [report.to_dict() for report in reports]
        }), 200

    finally:
        db_session.close()


@validation_bp.route('/reports/latest', methods=['GET'])
@require_auth
def get_latest_validation_report():
    """
    Get the most recent validation report.

    Response:
        {
            "report": {
                "id": 5,
                "timestamp": "2025-01-22T15:00:00Z",
                "status": "warning",
                "summary": {"critical": 0, "warning": 2, "info": 1},
                "issues": [
                    {
                        "severity": "warning",
                        "category": "missing_data",
                        "message": "Missing values in column Mar-25: 1 values"
                    }
                ],
                "data_file": "dashboard_data.csv"
            }
        }
    """
    db_session = get_session()

    try:
        validation_service = ValidationService(db_session)
        report = validation_service.get_latest_validation_report()

        if not report:
            return jsonify({'error': 'No validation reports found'}), 404

        return jsonify({
            'report': report.to_dict()
        }), 200

    finally:
        db_session.close()


@validation_bp.route('/reports/<int:report_id>', methods=['GET'])
@require_auth
def get_validation_report(report_id: int):
    """
    Get specific validation report by ID.

    Response:
        {
            "report": {
                "id": 1,
                "timestamp": "2025-01-22T10:30:00Z",
                "status": "pass",
                "summary": {"critical": 0, "warning": 0, "info": 0},
                "issues": [],
                "data_file": "dashboard_data.csv"
            }
        }
    """
    db_session = get_session()

    try:
        from scripts.models.validation_report import ValidationReport

        report = db_session.query(ValidationReport).filter(
            ValidationReport.id == report_id
        ).first()

        if not report:
            return jsonify({'error': 'Validation report not found'}), 404

        return jsonify({
            'report': report.to_dict()
        }), 200

    finally:
        db_session.close()
