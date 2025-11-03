#!/usr/bin/env python3
"""
CSV to Dashboard Pipeline
Reads data from CSV files (later can be switched to Google Sheets)
"""

import pandas as pd
import json
from datetime import datetime
from typing import Dict, Any
import numpy as np
from pathlib import Path
from scripts.logger_config import get_logger

# Initialize logger
logger = get_logger(__name__)

class KPIPipeline:
    """Pipeline for processing KPI data from CSV/Google Sheets"""
    
    def __init__(self, data_source='csv'):
        """
        Initialize pipeline
        Args:
            data_source: 'csv' for local files, 'google_sheets' for online
        """
        self.data_source = data_source
        self.raw_data = None
        self.transformed_data = None
        
    def load_data(self, file_path='data/raw/kpi_data.csv', sheet_name=None):
        """
        Load data from CSV or Google Sheets
        Args:
            file_path: Path to CSV file (for CSV mode)
            sheet_name: Google Sheet name (for Google Sheets mode)
        """
        if self.data_source == 'csv':
            if not Path(file_path).exists():
                logger.error(f"Data file not found: {file_path}")
                raise FileNotFoundError(f"Data file not found: {file_path}")

            logger.info(f"Loading data from: {file_path}")
            self.raw_data = pd.read_csv(file_path)
            logger.info(f"Loaded {len(self.raw_data)} rows from CSV")

        elif self.data_source == 'google_sheets':
            # Future implementation for Google Sheets
            # import gspread
            # from google.oauth2.service_account import Credentials
            logger.warning("Google Sheets integration not yet implemented")
            return None
        
        return self.raw_data
    
    def clean_data(self):
        """Clean and standardize the data"""
        if self.raw_data is None:
            raise ValueError("No data loaded. Run load_data first.")
        
        df = self.raw_data.copy()
        
        # Remove completely empty rows
        df = df.dropna(how='all')
        
        # Standardize column names
        column_mapping = {
            'GMV': 'gmv',
            'Funded Amount': 'funded_amount',
            'Avg Days Outstanding': 'avg_days_outstanding',
            '# Invoices': 'num_invoices',
            '# Boxes': 'num_boxes',
            'month': 'month'
        }
        
        # Rename columns if they exist
        df.columns = [column_mapping.get(col, col) for col in df.columns]
        
        # Convert month to datetime - handle multiple formats
        if 'month' in df.columns and df['month'].dtype == 'object':
            # Get the month column values
            month_values = df['month'].copy()

            # Try date format first (M/D/YYYY)
            df['month'] = pd.to_datetime(month_values, format='%m/%d/%Y', errors='coerce')

            # If that fails, try month names (e.g., "January", "February")
            if df['month'].isna().all():
                df['month'] = pd.to_datetime(month_values + ' 2025', format='%B %Y', errors='coerce')

            # If that fails, try the original format (M/D/YY)
            if df['month'].isna().all():
                df['month'] = pd.to_datetime(month_values, format='%m/%d/%y', errors='coerce')

            # If all specific formats fail, try general parsing
            if df['month'].isna().all():
                df['month'] = pd.to_datetime(month_values, errors='coerce')
        elif 'month' in df.columns:
            # If already datetime, keep as is
            df['month'] = pd.to_datetime(df['month'], errors='coerce')
        
        # Convert numeric columns - include all potential KPI metrics
        numeric_cols = [
            'gmv', 'funded_amount', 'avg_days_outstanding', 'num_invoices', 'num_boxes',
            'accrued_interests', 'arrangement_fees', 'avg_portfolio_outstanding',
            'cargo_insurance_costs', 'cargo_insurance_fees', 'cost_of_funds_accrued',
            'costs_docs_delivery', 'docs_management_fees', 'gmv_insured_pct',
            'handling_warehouse_costs', 'handling_warehouse_fees', 'logistic_costs',
            'logistic_fees', 'cash_drag', 'usd_eur_rate_eom'
        ]
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # Keep only rows with valid month
        df = df[df['month'].notna()]

        logger.info(f"Cleaned data: {len(df)} valid rows")
        return df
    
    def calculate_metrics(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate derived metrics and KPIs"""
        # Operational efficiency
        df['boxes_per_invoice'] = (df['num_boxes'] / df['num_invoices']).round(2)
        
        # Growth metrics
        df['gmv_mom_growth'] = df['gmv'].pct_change() * 100
        df['funded_mom_growth'] = df['funded_amount'].pct_change() * 100
        
        # Moving averages
        df['gmv_ma3'] = df['gmv'].rolling(window=3, min_periods=1).mean()
        df['funded_ma3'] = df['funded_amount'].rolling(window=3, min_periods=1).mean()
        
        # Cumulative metrics
        df['cumulative_gmv'] = df['gmv'].cumsum()
        df['cumulative_funded'] = df['funded_amount'].cumsum()
        
        # Performance categories
        df['days_performance'] = df['avg_days_outstanding'].apply(
            lambda x: 'Excellent' if x <= 20 else ('Good' if x <= 25 else 'Needs Improvement') 
            if pd.notna(x) else None
        )
        
        # Time-based columns
        df['quarter'] = df['month'].dt.quarter
        df['year'] = df['month'].dt.year
        df['month_name'] = df['month'].dt.strftime('%B')

        logger.info(f"Calculated {len(df.columns) - 6} derived metrics")
        return df
    
    def transform_data(self):
        """Main transformation pipeline"""
        df_clean = self.clean_data()
        df_with_metrics = self.calculate_metrics(df_clean)
        self.transformed_data = df_with_metrics
        logger.info("Data transformation complete")
        return self.transformed_data
    
    def generate_summary_stats(self) -> Dict[str, Any]:
        """Generate summary statistics"""
        if self.transformed_data is None:
            raise ValueError("No transformed data available.")
        
        df = self.transformed_data
        df_valid = df[df['gmv'].notna()]
        
        if len(df_valid) == 0:
            return {"error": "No valid data to summarize"}
        
        summary = {
            'total_gmv': float(df_valid['gmv'].sum()),
            'total_funded': float(df_valid['funded_amount'].sum()),
            'total_invoices': int(df_valid['num_invoices'].sum()),
            'total_boxes': int(df_valid['num_boxes'].sum()),
            'avg_days_outstanding': float(df_valid['avg_days_outstanding'].mean()),
            'avg_cash_drag': float(df_valid['cash_drag'].mean()) if 'cash_drag' in df_valid.columns and not df_valid['cash_drag'].isna().all() else None,
            'period': {
                'start': df_valid['month'].min().strftime('%B %Y'),
                'end': df_valid['month'].max().strftime('%B %Y')
            },
            'data_points': len(df_valid)
        }
        
        return summary
    
    def export_for_dashboard(self, output_dir='data/processed'):
        """Export data for dashboard consumption"""
        if self.transformed_data is None:
            raise ValueError("No transformed data available.")
        
        df = self.transformed_data.copy()
        
        # Format data for dashboard
        df['month_label'] = df['month'].dt.strftime('%b %y')
        df['month'] = df['month'].dt.strftime('%Y-%m-%d')
        
        # Create export package
        export_data = {
            'data': json.loads(df.to_json(orient='records')),
            'summary': self.generate_summary_stats(),
            'last_updated': datetime.now().isoformat()
        }
        
        # Save to JSON
        output_path = Path(output_dir) / 'dashboard_data.json'
        with open(output_path, 'w') as f:
            json.dump(export_data, f, indent=2, default=str)

        logger.info(f"Exported dashboard data to {output_path}")

        # Also save processed CSV for reference
        csv_path = Path(output_dir) / 'processed_data.csv'
        df.to_csv(csv_path, index=False)
        logger.info(f"Saved processed CSV to {csv_path}")

        return output_path
    
    def run_pipeline(self, input_file='data/raw/kpi_data.csv'):
        """Run the complete pipeline"""
        logger.info("=" * 50)
        logger.info("Starting KPI Data Pipeline")
        logger.info("=" * 50)
        logger.info(f"Data source: {self.data_source.upper()}")
        logger.info(f"Input file: {input_file}")
        logger.info("-" * 50)

        try:
            # Load data
            self.load_data(input_file)

            # Transform
            self.transform_data()

            # Generate summary
            summary = self.generate_summary_stats()
            logger.info("Summary Statistics:")
            logger.info(f"  Total GMV: ${summary.get('total_gmv', 0):,.0f}")
            logger.info(f"  Total Funded: ${summary.get('total_funded', 0):,.0f}")
            logger.info(f"  Period: {summary.get('period', {}).get('start', 'N/A')} to {summary.get('period', {}).get('end', 'N/A')}")

            # Export
            output_file = self.export_for_dashboard()

            logger.info("=" * 50)
            logger.info("Pipeline completed successfully!")
            logger.info("=" * 50)

            return output_file

        except Exception as e:
            logger.error(f"Pipeline failed: {str(e)}", exc_info=True)
            raise

if __name__ == "__main__":
    # Check for KPIs v2 data first, then fall back to original data
    kpis_v2_file = 'data/processed/kpis_v2_pipeline.csv'
    original_data_file = 'data/raw/kpi_data.csv'

    if Path(kpis_v2_file).exists():
        logger.info(f"Using KPIs v2 data: {kpis_v2_file}")
        data_file = kpis_v2_file
    elif Path(original_data_file).exists():
        logger.info(f"Using original KPI data: {original_data_file}")
        data_file = original_data_file
    else:
        logger.warning("No data file found!")
        logger.warning(f"Please add your data to either:")
        logger.warning(f"  - {kpis_v2_file} (processed from kpis_v2.csv)")
        logger.warning(f"  - {original_data_file} (direct format)")
        logger.warning("Expected CSV format:")
        logger.warning("month,GMV,Funded Amount,Avg Days Outstanding,# Invoices,# Boxes")
        logger.warning("1/1/25,11352846,10107543,18,54,91")
        logger.warning("...")
        exit(1)

    # Run pipeline
    pipeline = KPIPipeline(data_source='csv')
    pipeline.run_pipeline(data_file)
