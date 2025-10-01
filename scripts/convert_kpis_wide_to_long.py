#!/usr/bin/env python3
"""
KPIs Wide-to-Long Converter
Converts KPI data from wide format (metrics as rows, months as columns)
to long format (month, metric, value) for pipeline processing.
"""

import pandas as pd
import numpy as np
import re
from pathlib import Path
import argparse

def clean_currency_value(value):
    """Clean currency values and convert to float"""
    if pd.isna(value) or value == '':
        return np.nan

    # Convert to string and clean
    value_str = str(value).strip()

    # Remove currency symbols, commas, spaces, and handle parentheses for negative values
    value_str = re.sub(r'[$,\s]', '', value_str)

    # Handle parentheses as negative values
    if value_str.startswith('(') and value_str.endswith(')'):
        value_str = '-' + value_str[1:-1]

    # Handle percentage values
    if value_str.endswith('%'):
        try:
            return float(value_str[:-1]) / 100
        except ValueError:
            return np.nan

    # Convert to float
    try:
        return float(value_str)
    except ValueError:
        return np.nan

def standardize_metric_name(metric_name):
    """Standardize metric names for consistency"""
    metric_mapping = {
        'GMV': 'gmv',
        'Funded Amount': 'funded_amount',
        'Avg Days Outstanding': 'avg_days_outstanding',
        '# Invoices': 'num_invoices',
        '# Boxes': 'num_boxes',
        '% GMV Insured': 'gmv_insured_pct',
        'Arrangement Fees': 'arrangement_fees',
        'Logistic Fees': 'logistic_fees',
        'Logistic Costs': 'logistic_costs',
        'Cargo Insurance Fees': 'cargo_insurance_fees',
        'Cargo Insurance Costs': 'cargo_insurance_costs',
        'Accrued Interests': 'accrued_interests',
        'Cost of Funds (Accrued)': 'cost_of_funds_accrued',
        'Docs Management Fees': 'docs_management_fees',
        'Costs of Docs Delivery': 'costs_docs_delivery',
        'Handling & Warehouse Destination Fees': 'handling_warehouse_fees',
        'Handling & Warehouse Destination Costs': 'handling_warehouse_costs',
        'Avg Portfolio Outstanding': 'avg_portfolio_outstanding',
        'Cash Drag': 'cash_drag',
        'USD to EUR historical Rates (EoM)': 'usd_eur_rate_eom'
    }

    return metric_mapping.get(metric_name, metric_name.lower().replace(' ', '_').replace('#', 'num'))

def convert_wide_to_long(input_file, output_file=None):
    """
    Convert KPIs from wide format to long format

    Args:
        input_file: Path to input CSV file in wide format
        output_file: Path to output CSV file (optional)

    Returns:
        DataFrame in long format
    """

    print(f"Loading KPIs data from: {input_file}")

    # Read the CSV file
    df = pd.read_csv(input_file)

    # Set the first column as the index (metric names)
    df.set_index(df.columns[0], inplace=True)

    # Remove any empty rows/columns
    df = df.dropna(how='all').loc[:, df.notna().any()]

    print(f"Found {len(df)} metrics across {len(df.columns)} months")

    # Prepare data for melting
    long_data = []

    for metric_name in df.index:
        if pd.isna(metric_name) or metric_name.strip() == '':
            continue

        metric_name_clean = standardize_metric_name(metric_name.strip())

        for month_col in df.columns:
            value = df.loc[metric_name, month_col]

            # Skip empty values
            if pd.isna(value) or str(value).strip() == '':
                continue

            # Clean and convert the value
            cleaned_value = clean_currency_value(value)

            # Only add if we have a valid value
            if not pd.isna(cleaned_value):
                long_data.append({
                    'month': month_col,
                    'metric': metric_name_clean,
                    'value': cleaned_value,
                    'original_metric': metric_name
                })

    # Create long format DataFrame
    df_long = pd.DataFrame(long_data)

    if len(df_long) == 0:
        raise ValueError("No valid data found in the input file")

    # Convert month to datetime if possible
    try:
        # Try date format first (M/D/YYYY)
        df_long['month_date'] = pd.to_datetime(df_long['month'], format='%m/%d/%Y', errors='coerce')

        if df_long['month_date'].isna().all():
            # Try month name formats
            df_long['month_date'] = pd.to_datetime(df_long['month'], format='%B', errors='coerce')
            if df_long['month_date'].isna().all():
                # If that doesn't work, try with year assumption (current year)
                current_year = pd.Timestamp.now().year
                df_long['month_date'] = pd.to_datetime(df_long['month'] + f' {current_year}', format='%B %Y', errors='coerce')
    except:
        print("Warning: Could not parse month dates automatically")
        df_long['month_date'] = pd.NaT

    # Sort by month chronologically (using parsed date) and metric for consistent output
    if not df_long['month_date'].isna().all():
        df_long = df_long.sort_values(['month_date', 'metric']).reset_index(drop=True)
    else:
        df_long = df_long.sort_values(['month', 'metric']).reset_index(drop=True)

    print(f"Converted to long format: {len(df_long)} rows with {df_long['metric'].nunique()} unique metrics")

    # Save if output file specified
    if output_file:
        Path(output_file).parent.mkdir(parents=True, exist_ok=True)
        df_long.to_csv(output_file, index=False)
        print(f"Saved long format data to: {output_file}")

    return df_long

def convert_usd_to_eur(df_pivot):
    """
    Convert USD values to EUR using historical exchange rates

    Args:
        df_pivot: DataFrame with pivoted data including usd_eur_rate_eom column

    Returns:
        DataFrame with USD values converted to EUR
    """

    # Define which columns contain USD values that need conversion
    usd_columns = [
        'gmv', 'funded_amount', 'accrued_interests', 'arrangement_fees',
        'avg_portfolio_outstanding', 'cargo_insurance_costs', 'cargo_insurance_fees',
        'cost_of_funds_accrued', 'costs_docs_delivery', 'docs_management_fees',
        'handling_warehouse_costs', 'handling_warehouse_fees', 'logistic_costs', 'logistic_fees'
    ]

    # Check if we have the exchange rate column
    if 'usd_eur_rate_eom' not in df_pivot.columns:
        print("Warning: No USD to EUR exchange rates found. Skipping currency conversion.")
        return df_pivot

    converted_count = 0

    for col in usd_columns:
        if col in df_pivot.columns:
            # Convert USD to EUR: USD * exchange_rate = EUR
            df_pivot[col] = df_pivot[col] * df_pivot['usd_eur_rate_eom']
            converted_count += 1

    print(f"Converted {converted_count} USD columns to EUR using historical exchange rates")
    return df_pivot

def create_pipeline_compatible_format(df_long, output_file=None, convert_currency=True):
    """
    Create a format compatible with the existing KPI pipeline

    Args:
        df_long: DataFrame in long format
        output_file: Path to output CSV file
        convert_currency: Whether to convert USD values to EUR (default: True)

    Returns:
        DataFrame in pipeline-compatible format
    """

    # Pivot to get metrics as columns, months as rows
    df_pivot = df_long.pivot(index='month', columns='metric', values='value')

    # Reset index to make month a column
    df_pivot = df_pivot.reset_index()

    # Ensure we have the core metrics expected by the pipeline
    required_columns = ['month', 'gmv', 'funded_amount', 'avg_days_outstanding', 'num_invoices', 'num_boxes']

    # Add missing columns with NaN values
    for col in required_columns:
        if col not in df_pivot.columns:
            df_pivot[col] = np.nan

    # Convert USD to EUR if requested
    if convert_currency:
        df_pivot = convert_usd_to_eur(df_pivot)

    # Reorder columns to match pipeline expectations
    available_required = [col for col in required_columns if col in df_pivot.columns]
    other_columns = [col for col in df_pivot.columns if col not in required_columns]
    df_pivot = df_pivot[available_required + other_columns]

    print(f"Created pipeline-compatible format with {len(df_pivot)} rows and {len(df_pivot.columns)} columns")

    # Save if output file specified
    if output_file:
        Path(output_file).parent.mkdir(parents=True, exist_ok=True)
        df_pivot.to_csv(output_file, index=False)
        print(f"Saved pipeline-compatible data to: {output_file}")

    return df_pivot

def main():
    parser = argparse.ArgumentParser(description='Convert KPIs from wide to long format')
    parser.add_argument('input', help='Input CSV file in wide format')
    parser.add_argument('-o', '--output', help='Output CSV file in long format')
    parser.add_argument('--pipeline-format', help='Output file for pipeline-compatible format')
    parser.add_argument('--both', action='store_true', help='Generate both long and pipeline formats')
    parser.add_argument('--no-conversion', action='store_true', help='Skip USD to EUR currency conversion')

    args = parser.parse_args()

    if not Path(args.input).exists():
        print(f"Error: Input file not found: {args.input}")
        return 1

    try:
        # Convert to long format
        df_long = convert_wide_to_long(args.input, args.output)

        # If requested, also create pipeline-compatible format
        if args.pipeline_format or args.both:
            pipeline_output = args.pipeline_format or args.input.replace('.csv', '_pipeline.csv')
            convert_currency = not args.no_conversion
            create_pipeline_compatible_format(df_long, pipeline_output, convert_currency=convert_currency)

        print("\n[OK] Conversion completed successfully!")
        return 0

    except Exception as e:
        print(f"\n[ERROR] Conversion failed: {str(e)}")
        return 1

if __name__ == "__main__":
    exit(main())