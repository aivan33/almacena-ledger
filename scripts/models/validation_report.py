"""Data validation report model for quality tracking."""

from sqlalchemy import Column, Integer, String, Text, DateTime
from scripts.database import Base
from datetime import datetime
import json


class ValidationReport(Base):
    """Data validation reports for tracking data quality issues."""

    __tablename__ = 'validation_reports'

    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    status = Column(String(20), nullable=False)  # pass, warning, critical
    summary = Column(Text, nullable=True)  # JSON: {critical: 2, warning: 5, info: 3}
    issues = Column(Text, nullable=True)  # JSON array of issue objects
    data_file = Column(String(255), nullable=True)

    def to_dict(self):
        """
        Convert validation report to dictionary.

        Returns:
            dict: Validation report with parsed JSON fields
        """
        return {
            'id': self.id,
            'timestamp': self.timestamp.isoformat(),
            'status': self.status,
            'summary': json.loads(self.summary) if self.summary else {},
            'issues': json.loads(self.issues) if self.issues else [],
            'data_file': self.data_file
        }
