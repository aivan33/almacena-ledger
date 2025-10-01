import pandas as pd

# Read the processed CSV
df = pd.read_csv('data/processed/kpis_v2_pipeline.csv')

print("="*80)
print("CHECKING CONVERSION LOGIC")
print("="*80)

# Get exchange rate
exch_rate = df[df['month'].str.contains('exch', case=False, na=False)]
gmv = df[df['month'] == 'GMV']
funded = df[df['month'] == 'Funded Amount']

# Check Jan 2025 values
jan_col = '2025-01-01 00:00:00'

exch_rate_jan = float(exch_rate[jan_col].values[0])
gmv_eur_jan = float(gmv[jan_col].values[0])
funded_eur_jan = float(funded[jan_col].values[0])

print(f"\nJanuary 2025:")
print(f"Exchange Rate: {exch_rate_jan:.10f}")
print(f"GMV (EUR):     €{gmv_eur_jan:,.2f}")
print(f"Funded (EUR):  €{funded_eur_jan:,.2f}")

# Calculate what the USD values would have been
gmv_usd_calc = gmv_eur_jan / exch_rate_jan
funded_usd_calc = funded_eur_jan / exch_rate_jan

print(f"\nReverse calculation (EUR / rate = USD):")
print(f"GMV (USD):     ${gmv_usd_calc:,.2f}")
print(f"Funded (USD):  ${funded_usd_calc:,.2f}")

print(f"\nExpected from raw data:")
print(f"GMV (USD):     $11,763,388.25")
print(f"Funded (USD):  $10,473,052.71")

print("\n" + "="*80)
print("CHECKING ALL MONTHS")
print("="*80)

months = ['2025-01-01 00:00:00', '2025-02-01 00:00:00', '2025-03-01 00:00:00']
for month_col in months:
    try:
        rate = float(exch_rate[month_col].values[0])
        gmv_val = float(gmv[month_col].values[0])
        funded_val = float(funded[month_col].values[0])

        print(f"\n{month_col[:7]}:")
        print(f"  Rate: {rate:.4f}")
        print(f"  GMV EUR: €{gmv_val:,.0f}  -> USD: ${gmv_val/rate:,.0f}")
        print(f"  Funded EUR: €{funded_val:,.0f}  -> USD: ${funded_val/rate:,.0f}")
    except:
        pass