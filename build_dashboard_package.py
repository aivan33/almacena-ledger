"""
Build standalone dashboard package for client distribution.
Run this script after updating dashboard or data to regenerate the zip file.

Usage: python build_dashboard_package.py
"""
import json
import zipfile
import os
from pathlib import Path

def create_standalone_html():
    """Create standalone HTML with embedded data."""
    print("Step 1: Reading dashboard data...")

    # Read the dashboard data
    with open('data/processed/dashboard_data.json', 'r') as f:
        data = json.load(f)

    print("Step 2: Reading dashboard HTML template...")

    # Read the HTML file
    with open('dashboard/index.html', 'r', encoding='utf-8') as f:
        html = f.read()

    print("Step 3: Embedding data into HTML...")

    # Find the position to insert the inline data (after <script> tag opening)
    script_start = html.find('<script>')
    if script_start != -1:
        # Found <script>, now find the closing >
        script_start = html.find('>', script_start) + 1
    else:
        # Try <script with attributes
        script_start = html.find('<script ')
        if script_start != -1:
            script_start = html.find('>', script_start) + 1

    # Create the inline data declaration
    inline_data = f'''
    // ===== EMBEDDED DATA =====
    // Dashboard data embedded directly in HTML for standalone usage (no server required)
    const EMBEDDED_DATA = {json.dumps(data, indent=2)};
    // ========================
'''

    # Insert the inline data right after the script tag
    html_with_data = html[:script_start] + inline_data + html[script_start:]

    # Replace the fetch logic with direct data assignment
    old_load_function = '''        // Load dashboard data
        async function loadDashboardData() {
            try {
                const timestamp = new Date().getTime();
                const response = await fetch(`../data/processed/dashboard_data.json?t=${timestamp}`);
                if (!response.ok) throw new Error('Data file not found');

                dashboardData = await response.json();'''

    new_load_function = '''        // Load dashboard data
        async function loadDashboardData() {
            try {
                // Use embedded data (no fetch required for standalone version)
                dashboardData = EMBEDDED_DATA;'''

    html_with_data = html_with_data.replace(old_load_function, new_load_function)

    # Ensure package directory exists
    os.makedirs('dashboard-package', exist_ok=True)

    # Write the standalone version
    with open('dashboard-package/Almacena-Dashboard.html', 'w', encoding='utf-8') as f:
        f.write(html_with_data)

    print(f"   [OK] Created standalone HTML ({len(html_with_data) / 1024:.1f} KB)")
    return len(html_with_data)

def create_readme():
    """Create README file."""
    print("Step 4: Creating README...")

    readme_content = """================================================================================
                    ALMACENA FINANCIAL DASHBOARD
                      No Installation Required
================================================================================

QUICK START:
------------
Double-click "Almacena-Dashboard.html" to open the dashboard in your browser.

That's it! No installation, no Python, no server needed.


REQUIREMENTS:
-------------
- Modern web browser (Chrome, Firefox, Edge, Safari)
- No internet connection required (works fully offline)
- No software installation needed


FEATURES:
---------
- Interactive KPIs and performance metrics
- Multi-currency support (USD/EUR toggle)
- Period-over-period analysis
- Visual charts and data tables
- Fully self-contained (all data embedded)


CURRENCY TOGGLE:
----------------
Click the USD/EUR buttons in the filter bar (top right) to switch currencies.
- USD values are the original data from source
- EUR values are converted using historical exchange rates


TROUBLESHOOTING:
----------------
Problem: Dashboard shows blank page
Solution: Make sure JavaScript is enabled in your browser

Problem: Charts not showing
Solution: Try a different browser (Chrome or Firefox recommended)

Problem: File won't open
Solution: Right-click the HTML file → "Open with" → Choose your browser


UPDATING DATA:
--------------
To update the dashboard with new data, you'll need to regenerate this file
with the updated information. Contact your Almacena team for assistance.


SHARING:
--------
You can share this single HTML file via email or file sharing.
The recipient just needs to double-click it to view.


SUPPORT:
--------
For questions or support, contact your Almacena representative.


================================================================================
                         © 2025 Almacena
================================================================================
"""

    with open('dashboard-package/README.txt', 'w', encoding='utf-8') as f:
        f.write(readme_content)

    print("   [OK] Created README.txt")

def create_zip_package():
    """Create zip file from dashboard package."""
    print("Step 5: Creating zip package...")

    zip_file = 'almacena-dashboard.zip'
    source_dir = 'dashboard-package'

    with zipfile.ZipFile(zip_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
        # Only include the HTML file, not README
        html_path = os.path.join(source_dir, 'Almacena-Dashboard.html')
        arcname = os.path.relpath(html_path, os.path.dirname(source_dir))
        zipf.write(html_path, arcname)

    zip_size = os.path.getsize(zip_file)
    print(f"   [OK] Created {zip_file} ({zip_size / 1024:.1f} KB)")

    return zip_file, zip_size

def main():
    """Main build process."""
    print("=" * 70)
    print("  ALMACENA DASHBOARD - PACKAGE BUILDER")
    print("=" * 70)
    print()

    try:
        # Create standalone HTML with embedded data
        html_size = create_standalone_html()

        # Create README
        create_readme()

        # Create zip package
        zip_file, zip_size = create_zip_package()

        print()
        print("=" * 70)
        print("  BUILD COMPLETED SUCCESSFULLY!")
        print("=" * 70)
        print()
        print(f"Package: {zip_file}")
        print(f"Size: {zip_size / 1024:.1f} KB")
        print()
        print("Files included:")
        print("  - Almacena-Dashboard.html")
        print()
        print("Ready to share with client!")
        print()

    except Exception as e:
        print()
        print("=" * 70)
        print("  BUILD FAILED")
        print("=" * 70)
        print(f"Error: {e}")
        raise

if __name__ == '__main__':
    main()
