rate = 0.8523218966
funded_eur = 7768471.87
funded_usd_reverse = funded_eur / rate

print(f"September 2025 Analysis:")
print(f"="*50)
print(f"Exchange Rate: {rate}")
print(f"Funded EUR (in our data): €{funded_eur:,.2f}")
print(f"Reverse calculation: €{funded_eur:,.2f} / {rate} = ${funded_usd_reverse:,.2f}")
print()
print(f"Your expected value: $9,470,029")
print(f"Difference: ${funded_usd_reverse - 9470029:,.2f}")
print()

# What should it be if your value is correct?
funded_from_your_value = 9470029 * rate
print(f"If your value is correct:")
print(f"  $9,470,029 * {rate} = €{funded_from_your_value:,.2f}")
print(f"But our data shows: €{funded_eur:,.2f}")
print(f"Difference: €{funded_eur - funded_from_your_value:,.2f}")
print()

# Let's check what the actual USD value in the sheet is
print("Let me check what's actually downloaded from Google Sheets...")

import pandas as pd
from google.oauth2 import service_account
from googleapiclient.discovery import build
import io
from googleapiclient.http import MediaIoBaseDownload

CREDENTIALS_FILE = 'credentials/genuine-ridge-473708-b9-1004a2f89ab7.json'
SCOPES = ['https://www.googleapis.com/auth/drive.readonly']

creds = service_account.Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=SCOPES)
drive_service = build('drive', 'v3', credentials=creds)

# Download file
request = drive_service.files().get_media(fileId='1PV11033oLV8OwRZY4hG9ils9IXk2qstu')
file_buffer = io.BytesIO()
downloader = MediaIoBaseDownload(file_buffer, request)

done = False
while not done:
    status, done = downloader.next_chunk()

file_buffer.seek(0)

# Read Excel file
excel_data = pd.read_excel(file_buffer, sheet_name='dashboard')

print(f"\nRaw data from Google Sheets:")
print(f"Columns: {list(excel_data.columns)[:5]}...")

# Find Funded Amount row
funded_row = excel_data[excel_data.iloc[:, 0] == 'Funded Amount']
if not funded_row.empty:
    sep_value = funded_row.iloc[0, 9]  # Column 9 should be September (columns 1-12 are months)
    print(f"Funded Amount September (raw): {sep_value}")
    print(f"Type: {type(sep_value)}")