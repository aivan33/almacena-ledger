#!/usr/bin/env python3
"""
KPI Dashboard Pipeline - Setup Script with CSV Data Import
Run this in an empty directory to create the entire project structure
"""

import os
import json
from pathlib import Path
from datetime import datetime

def create_directory_structure():
    """Create all necessary directories"""
    directories = [
        'data/raw',
        'data/processed',
        'data/archive',
        'dashboard',
        'scripts',
        'logs'
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
    
    print("[OK] Directory structure created")

def create_data_pipeline():
    """Create the main data pipeline script that works with CSV files"""
    content = '''#!/usr/bin/env python3
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
                raise FileNotFoundError(f"Data file not found: {file_path}")
            
            print(f"Loading data from: {file_path}")
            self.raw_data = pd.read_csv(file_path)
            print(f"[OK] Loaded {len(self.raw_data)} rows from CSV")
            
        elif self.data_source == 'google_sheets':
            # Future implementation for Google Sheets
            # import gspread
            # from google.oauth2.service_account import Credentials
            print("Google Sheets integration not yet implemented")
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
        
        # Convert month to datetime
        df['month'] = pd.to_datetime(df['month'], format='%m/%d/%y', errors='coerce')
        
        # Convert numeric columns
        numeric_cols = ['gmv', 'funded_amount', 'avg_days_outstanding', 'num_invoices', 'num_boxes']
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # Keep only rows with valid month
        df = df[df['month'].notna()]
        
        print(f"[OK] Cleaned data: {len(df)} valid rows")
        return df
    
    def calculate_metrics(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate derived metrics and KPIs"""
        # Funding rate
        df['funding_rate'] = (df['funded_amount'] / df['gmv'] * 100).round(2)
        
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
        
        print(f"[OK] Calculated {len(df.columns) - 6} derived metrics")
        return df
    
    def transform_data(self):
        """Main transformation pipeline"""
        df_clean = self.clean_data()
        df_with_metrics = self.calculate_metrics(df_clean)
        self.transformed_data = df_with_metrics
        print("[OK] Data transformation complete")
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
            'avg_funding_rate': float(df_valid['funding_rate'].mean()),
            'total_invoices': int(df_valid['num_invoices'].sum()),
            'total_boxes': int(df_valid['num_boxes'].sum()),
            'avg_days_outstanding': float(df_valid['avg_days_outstanding'].mean()),
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
        
        print(f"[OK] Exported dashboard data to {output_path}")
        
        # Also save processed CSV for reference
        csv_path = Path(output_dir) / 'processed_data.csv'
        df.to_csv(csv_path, index=False)
        print(f"[OK] Saved processed CSV to {csv_path}")
        
        return output_path
    
    def run_pipeline(self, input_file='data/raw/kpi_data.csv'):
        """Run the complete pipeline"""
        print("=" * 50)
        print("Starting KPI Data Pipeline")
        print("=" * 50)
        print(f"Data source: {self.data_source.upper()}")
        print(f"Input file: {input_file}")
        print("-" * 50)
        
        try:
            # Load data
            self.load_data(input_file)
            
            # Transform
            self.transform_data()
            
            # Generate summary
            summary = self.generate_summary_stats()
            print("\\nSummary Statistics:")
            print(f"  Total GMV: ${summary.get('total_gmv', 0):,.0f}")
            print(f"  Total Funded: ${summary.get('total_funded', 0):,.0f}")
            print(f"  Avg Funding Rate: {summary.get('avg_funding_rate', 0):.1f}%")
            print(f"  Period: {summary.get('period', {}).get('start', 'N/A')} to {summary.get('period', {}).get('end', 'N/A')}")
            
            # Export
            output_file = self.export_for_dashboard()
            
            print("\\n" + "=" * 50)
            print("[OK] Pipeline completed successfully!")
            print("=" * 50)
            
            return output_file
            
        except Exception as e:
            print(f"\\n[ERROR] Pipeline failed: {str(e)}")
            raise

if __name__ == "__main__":
    # Check if data file exists
    data_file = 'data/raw/kpi_data.csv'
    
    if not Path(data_file).exists():
        print("\\n[WARNING] No data file found!")
        print(f"Please add your data to: {data_file}")
        print("\\nExpected CSV format:")
        print("month,GMV,Funded Amount,Avg Days Outstanding,# Invoices,# Boxes")
        print("1/1/25,11352846,10107543,18,54,91")
        print("...")
    else:
        # Run pipeline
        pipeline = KPIPipeline(data_source='csv')
        pipeline.run_pipeline(data_file)
'''
    
    with open('data_pipeline.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print("[OK] Created data_pipeline.py")

def create_dashboard():
    """Create the HTML dashboard"""
    content = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>KPI Dashboard</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.0/chart.umd.min.js"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        .container {
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            overflow: hidden;
        }
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }
        .kpi-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            padding: 30px;
            background: #f8f9fa;
        }
        .kpi-card {
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        .kpi-label {
            font-size: 12px;
            color: #666;
            text-transform: uppercase;
            margin-bottom: 5px;
        }
        .kpi-value {
            font-size: 24px;
            font-weight: bold;
            color: #333;
        }
        .charts {
            padding: 30px;
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
            gap: 30px;
        }
        .chart-container {
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        .chart-title {
            font-size: 18px;
            margin-bottom: 15px;
            color: #333;
        }
        #dataStatus {
            padding: 10px 30px;
            background: #f0f0f0;
            text-align: center;
            font-size: 14px;
            color: #666;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Executive KPI Dashboard</h1>
            <p style="margin-top: 10px; opacity: 0.9;">Real-time Performance Metrics</p>
        </div>
        
        <div id="dataStatus">Loading dashboard data...</div>
        
        <div class="kpi-grid" id="kpiGrid"></div>
        
        <div class="charts">
            <div class="chart-container">
                <div class="chart-title">Revenue Trend</div>
                <canvas id="revenueChart"></canvas>
            </div>
            <div class="chart-container">
                <div class="chart-title">Operational Metrics</div>
                <canvas id="operationalChart"></canvas>
            </div>
        </div>
    </div>

    <script>
        // Load dashboard data
        async function loadDashboardData() {
            try {
                const response = await fetch('../data/processed/dashboard_data.json');
                if (!response.ok) throw new Error('Data file not found');
                
                const dashboardData = await response.json();
                
                // Update status
                document.getElementById('dataStatus').innerHTML = 
                    'Last updated: ' + new Date(dashboardData.last_updated).toLocaleString();
                
                // Render KPIs
                renderKPIs(dashboardData.summary);
                
                // Render charts
                renderCharts(dashboardData.data);
                
            } catch (error) {
                console.error('Error loading data:', error);
                document.getElementById('dataStatus').innerHTML = 
                    '[WARNING] Error loading data. Please run: python data_pipeline.py';
            }
        }
        
        function renderKPIs(summary) {
            const kpiGrid = document.getElementById('kpiGrid');
            const gmv = (summary.total_gmv / 1000000).toFixed(2);
            const funded = (summary.total_funded / 1000000).toFixed(2);
            const rate = summary.avg_funding_rate.toFixed(1);
            const days = summary.avg_days_outstanding.toFixed(0);
            
            kpiGrid.innerHTML = 
                '<div class="kpi-card">' +
                    '<div class="kpi-label">Total GMV</div>' +
                    '<div class="kpi-value">$' + gmv + 'M</div>' +
                '</div>' +
                '<div class="kpi-card">' +
                    '<div class="kpi-label">Total Funded</div>' +
                    '<div class="kpi-value">$' + funded + 'M</div>' +
                '</div>' +
                '<div class="kpi-card">' +
                    '<div class="kpi-label">Funding Rate</div>' +
                    '<div class="kpi-value">' + rate + '%</div>' +
                '</div>' +
                '<div class="kpi-card">' +
                    '<div class="kpi-label">Avg Days Outstanding</div>' +
                    '<div class="kpi-value">' + days + ' days</div>' +
                '</div>';
        }
        
        function renderCharts(data) {
            // Revenue Chart
            new Chart(document.getElementById('revenueChart'), {
                type: 'line',
                data: {
                    labels: data.map(d => d.month_label),
                    datasets: [{
                        label: 'GMV',
                        data: data.map(d => d.gmv),
                        borderColor: '#667eea',
                        tension: 0.3
                    }, {
                        label: 'Funded Amount',
                        data: data.map(d => d.funded_amount),
                        borderColor: '#764ba2',
                        tension: 0.3
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false
                }
            });
            
            // Operational Chart
            new Chart(document.getElementById('operationalChart'), {
                type: 'bar',
                data: {
                    labels: data.map(d => d.month_label),
                    datasets: [{
                        label: 'Invoices',
                        data: data.map(d => d.num_invoices),
                        backgroundColor: '#10b981'
                    }, {
                        label: 'Boxes',
                        data: data.map(d => d.num_boxes),
                        backgroundColor: '#3b82f6'
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false
                }
            });
        }
        
        // Load data on page load
        loadDashboardData();
    </script>
</body>
</html>'''
    
    with open('dashboard/index.html', 'w', encoding='utf-8') as f:
        f.write(content)
    print("[OK] Created dashboard/index.html")

def create_requirements():
    """Create requirements.txt"""
    content = '''pandas==2.0.3
numpy==1.24.3

# For Excel support (optional)
# openpyxl==3.1.2

# For Google Sheets (when ready to integrate)
# gspread==5.12.0
# google-auth==2.23.0
'''
    
    with open('requirements.txt', 'w', encoding='utf-8') as f:
        f.write(content)
    print("[OK] Created requirements.txt")

def create_readme():
    """Create README with instructions"""
    content = '''# KPI Dashboard Pipeline

## Quick Start

1. **Install dependencies**:
   ```bash
   pip install pandas numpy
   ```

2. **Add your data**:
   - Place your CSV file in `data/raw/kpi_data.csv`
   - Use this format:
   ```csv
   month,GMV,Funded Amount,Avg Days Outstanding,# Invoices,# Boxes
   1/1/25,11352846,10107543,18,54,91
   2/1/25,12671553,11641505,18,51,97
   ...
   ```

3. **Run the pipeline**:
   ```bash
   python data_pipeline.py
   ```

4. **View dashboard**:
   - Open `dashboard/index.html` in your browser

## Data Format

Your CSV should have these columns:
- `month`: Date in M/D/YY format
- `GMV`: Gross Merchandise Value
- `Funded Amount`: Amount funded
- `Avg Days Outstanding`: Average days (can be empty)
- `# Invoices`: Number of invoices
- `# Boxes`: Number of boxes

## Files
- `data/raw/` - Place your raw CSV data here
- `data/processed/` - Processed data will be saved here
- `dashboard/` - Dashboard HTML file
'''
    
    with open('README.md', 'w', encoding='utf-8') as f:
        f.write(content)
    print("[OK] Created README.md")

def create_sample_csv_with_data():
    """Create a sample CSV with your data"""
    content = '''month,GMV,Funded Amount,Avg Days Outstanding,# Invoices,# Boxes
1/1/25,11352846,10107543,18,54,91
2/1/25,12671553,11641505,18,51,97
3/1/25,6510477,5718486,27,25,47
4/1/25,8216884,6967251,19,41,65
5/1/25,11979156,10706095,18,55,90
6/1/25,9305385,8230163,22,43,71
7/1/25,10884442,9348478,18,53,88
8/1/25,5525524,4148346,33,41,57
9/1/25,7027419,7792881,,44,64'''
    
    with open('data/raw/kpi_data.csv', 'w', encoding='utf-8') as f:
        f.write(content)
    print("[OK] Created data/raw/kpi_data.csv with sample data")

def main():
    """Main setup function"""
    print("=" * 60)
    print("KPI Dashboard Pipeline - Setup (CSV Version)")
    print("=" * 60)
    print("\nCreating project structure...\n")
    
    # Create all components
    create_directory_structure()
    create_data_pipeline()
    create_dashboard()
    create_requirements()
    create_readme()
    create_sample_csv_with_data()
    
    print("\n" + "=" * 60)
    print("[OK] Setup complete!")
    print("=" * 60)
    print("\n[NEXT STEPS]:")
    print("1. Install: pip install pandas numpy")
    print("2. Run: python data_pipeline.py")
    print("3. Open: dashboard/index.html")
    print("\n[NOTE] Sample data already added to data/raw/kpi_data.csv")
    print("=" * 60)

if __name__ == "__main__":
    main()