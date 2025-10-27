# Dashboard Automation with n8n

Complete guide for setting up automatic weekly updates for your Almacena dashboard using n8n and Docker.

## Overview

The automation system:
- Runs every **Monday at 9 AM** automatically (configurable)
- Provides **manual trigger** option for on-demand updates
- Fetches latest data from Google Sheets/Drive
- Updates dashboard files automatically
- Includes **Refresh Data button** in dashboard for instant updates

## Quick Start (3 Steps)

### 1. Start n8n with Docker

```bash
cd C:\Personal\code\almacena\dashboard
docker-compose up -d
```

### 2. Start Webhook Server

```bash
# In a separate terminal
python webhook_server.py
```

### 3. Import and Configure Workflow

1. Open http://localhost:5678
2. Login: `admin` / `changeme123`
3. Import workflow: **Workflows** → **Import from File** → `n8n_workflow_simple.json`
4. Activate: Toggle switch to **Active** (top-right)

**That's it!** The workflow will now run every Monday at 9 AM.

---

## Prerequisites

- Docker Desktop installed
- Python 3.x with dependencies (`pip install -r requirements.txt`)
- Google service account credentials (already configured in `config.json`)

---

## Understanding the System

### Architecture

```
┌────────────────────────────────────────────────────────┐
│  Google Sheets/Drive                                   │
│  (Source data)                                         │
└────────────────┬───────────────────────────────────────┘
                 │
                 │ On Schedule or Manual Trigger
                 ▼
┌────────────────────────────────────────────────────────┐
│  n8n (Docker Container)                                │
│  http://localhost:5678                                 │
│  - Schedule Trigger: Monday 9 AM                       │
│  - Manual Trigger: Click "Test workflow"               │
└────────────────┬───────────────────────────────────────┘
                 │
                 │ HTTP POST to webhook
                 ▼
┌────────────────────────────────────────────────────────┐
│  Webhook Server (webhook_server.py)                    │
│  http://localhost:5000/update-dashboard                │
│  - Loads config.json for credentials path              │
│  - Runs fetch_from_sheets.py                           │
└────────────────┬───────────────────────────────────────┘
                 │
                 │ Fetches data and updates files
                 ▼
┌────────────────────────────────────────────────────────┐
│  Dashboard Files                                       │
│  data/processed/dashboard_data.json                    │
└────────────────────────────────────────────────────────┘
```

### Docker Networking

From inside the n8n Docker container, `host.docker.internal` resolves to your host machine's IP. This allows n8n to call the webhook server running on your host:

```
Docker Container (n8n)  →  host.docker.internal:5000  →  Host Machine (webhook_server.py)
```

---

## Detailed Setup

### Step 1: Install Flask Dependency

```bash
pip install flask
```

This is already included in `requirements.txt` if you've run `pip install -r requirements.txt`.

### Step 2: Start n8n with Docker Compose

```bash
cd C:\Personal\code\almacena\dashboard

# Start n8n (runs in background)
docker-compose up -d

# Verify it's running
docker-compose ps
```

You should see:
```
NAME              IMAGE              STATUS
n8n-almacena      n8nio/n8n:latest   Up X seconds
```

**Change Default Password** (recommended):

Edit `docker-compose.yml` and update:
```yaml
- N8N_BASIC_AUTH_PASSWORD=YOUR_SECURE_PASSWORD
```

Then restart: `docker-compose restart`

### Step 3: Start Webhook Server

```bash
python webhook_server.py
```

**Keep this terminal running.** The webhook listens on `http://localhost:5000`.

The webhook automatically:
- Loads the correct credentials path from `config.json`
- Sets the `GOOGLE_CREDENTIALS_FILE` environment variable
- Runs `scripts/fetch_from_sheets.py` to update dashboard data

### Step 4: Access n8n and Import Workflow

1. Open browser: http://localhost:5678
2. Login:
   - Username: `admin`
   - Password: `changeme123` (or your custom password)
3. Click **Workflows** → **Import from File**
4. Select `n8n_workflow_simple.json`

### Step 5: Activate Workflow

1. In the workflow editor, find the toggle switch (top-right)
2. Switch to **Active**
3. Workflow will now run automatically every Monday at 9 AM

---

## Testing the System

### Test 1: Webhook Server

```powershell
# PowerShell (Windows)
Invoke-WebRequest -Uri http://localhost:5000/update-dashboard -Method POST

# Or use real curl
curl.exe -X POST http://localhost:5000/update-dashboard

# Or open in browser (supports GET requests)
# http://localhost:5000/update-dashboard
```

Expected output:
```json
{
  "status": "success",
  "message": "Dashboard updated successfully",
  "timestamp": "2025-10-27 14:30:45"
}
```

### Test 2: n8n Workflow

1. Open workflow in n8n: http://localhost:5678
2. Click **"Test workflow"** button (top-right)
3. Check for green checkmarks on all nodes
4. View execution details in **Executions** tab

### Test 3: Dashboard Refresh

1. Open `dashboard/index.html` in browser
2. Update a value in your Google Sheet
3. Click **"Test workflow"** in n8n (or wait for Monday 9 AM)
4. In dashboard, click **🔄 Refresh Data** button
5. Verify the value updated

---

## Manual Triggers

You have three ways to trigger an update manually:

### Option 1: n8n Manual Trigger (Easiest)

1. Open workflow: http://localhost:5678
2. Click **"Test workflow"** button
3. The workflow has a "Manual Trigger - Run Anytime" node built-in

### Option 2: Webhook

```powershell
# PowerShell
Invoke-WebRequest -Uri http://localhost:5000/update-dashboard -Method POST

# Real curl
curl.exe -X POST http://localhost:5000/update-dashboard
```

### Option 3: Direct Script

```bash
python scripts/fetch_from_sheets.py
```

Then click **🔄 Refresh Data** in dashboard.

---

## Dashboard Cache Improvements

The dashboard includes three layers of cache prevention:

### 1. HTTP Cache-Control Headers

All HTML files (`index.html`, `analysis.html`, `data-validation.html`, `debug.html`) include:
```html
<meta http-equiv="Cache-Control" content="no-cache, no-store, must-revalidate">
<meta http-equiv="Pragma" content="no-cache">
<meta http-equiv="Expires" content="0">
```

### 2. Timestamp-Based Data Loading

JSON data is loaded with timestamp parameters to force fresh data:
```javascript
fetch(`../data/processed/dashboard_data.json?t=${timestamp}`)
```

### 3. Manual Refresh Button

The main dashboard (`index.html`) includes a **🔄 Refresh Data** button:

**Features:**
- Click to reload data without page refresh
- Visual feedback: Loading → Refreshed! → Reset
- No need to press F5 or Ctrl+Shift+R anymore

**Usage:**
1. Update data in Google Sheets
2. Run n8n workflow (or wait for scheduled trigger)
3. Click **🔄 Refresh Data** button in dashboard
4. See updated data immediately!

---

## Configuration

### Change Schedule

Edit the **"Schedule Trigger"** node in n8n:

**Default:** Every Monday at 9:00 AM

**Change time:**
1. Click "Schedule Trigger - Every Monday 9 AM" node
2. Adjust hour/minute fields
3. Save workflow

**Change days:**
- Daily: Change interval to every 1 day
- Specific weekdays: Select days in the trigger settings
- Monthly: Change to monthly interval

### Change Timezone

Edit `docker-compose.yml`:
```yaml
- GENERIC_TIMEZONE=Europe/Madrid  # Change this
```

Common timezones:
- `America/New_York`
- `America/Los_Angeles`
- `Europe/London`
- `Asia/Tokyo`

Restart: `docker-compose restart`

### Change Google Drive File

Update `config.json`:
```json
{
  "google_drive_file_id": "YOUR_NEW_FILE_ID",
  "sheet_name": "dashboard"
}
```

Get file ID from Google Drive URL:
- Google Sheets: `https://docs.google.com/spreadsheets/d/FILE_ID_HERE/edit`
- Google Drive: Right-click file → "Get link" → Copy ID

---

## Docker Commands Reference

```bash
# Start n8n
docker-compose up -d

# Stop n8n
docker-compose down

# View logs
docker-compose logs -f n8n

# Restart n8n (after config changes)
docker-compose restart

# Check status
docker-compose ps

# Update to latest n8n version
docker-compose pull
docker-compose up -d

# Remove everything (WARNING: Deletes all workflows!)
docker-compose down -v
```

---

## Monitoring and Debugging

### View n8n Execution History

1. Open n8n: http://localhost:5678
2. Click **"Executions"** (left sidebar)
3. See all past runs with timestamps
4. Click any execution to see detailed logs

### Check Webhook Status

```powershell
# Health check
Invoke-WebRequest -Uri http://localhost:5000/health

# Expected: {"status":"healthy"}
```

### View Webhook Logs

The webhook server terminal shows real-time logs:
```
Starting webhook server on http://0.0.0.0:5000
[INFO] Update triggered via webhook
[INFO] Running: python scripts/fetch_from_sheets.py
[INFO] Dashboard update completed successfully
```

### Check Data File Timestamp

```powershell
Get-Item data/processed/dashboard_data.json | Select-Object LastWriteTime, Length
```

---

## Troubleshooting

### n8n Container Won't Start

```bash
# Check logs
docker-compose logs n8n

# Common issues:
# - Port 5678 already in use → Change port in docker-compose.yml
# - Docker not running → Start Docker Desktop
```

### Webhook Returns Error

**"Credentials file not found"**
- Check `config.json` has correct `credentials_file` path
- Verify file exists: `ls credentials/`

**"Permission denied"**
- Ensure Google Sheet is shared with service account email
- Service account needs "Viewer" permission

**Connection refused**
1. Is webhook_server.py running?
2. Test: http://localhost:5000/health
3. Check Windows Firewall isn't blocking port 5000

### Workflow Doesn't Trigger

1. Verify workflow is **Active** (green toggle in n8n)
2. Check **Executions** tab for errors
3. Verify timezone matches your location
4. Manually execute to test: Click "Test workflow"

### Dashboard Shows Stale Data

1. Run workflow manually: Click "Test workflow" in n8n
2. Check data file was updated: `ls -lh data/processed/dashboard_data.json`
3. In dashboard, click **🔄 Refresh Data** button (no hard refresh needed!)

---

## Production Deployment

### Run Webhook as Windows Service

Use NSSM to run webhook_server.py automatically on startup:

```bash
# Download NSSM: https://nssm.cc/download
nssm install AlmacenaDashboardWebhook "C:\Path\To\Python\python.exe" "C:\Personal\code\almacena\dashboard\webhook_server.py"
nssm set AlmacenaDashboardWebhook AppDirectory "C:\Personal\code\almacena\dashboard"
nssm start AlmacenaDashboardWebhook
```

### Backup n8n Data

n8n workflows are stored in a Docker volume:

```bash
# Stop n8n
docker-compose down

# Backup
docker run --rm -v n8n_data:/data -v C:\Backups:/backup alpine tar czf /backup/n8n-backup.tar.gz -C /data .

# Start n8n
docker-compose up -d
```

To restore:
```bash
docker-compose down
docker volume rm n8n_data
docker volume create n8n_data
docker run --rm -v n8n_data:/data -v C:\Backups:/backup alpine tar xzf /backup/n8n-backup.tar.gz -C /data
docker-compose up -d
```

---

## URLs Reference

| Service | URL | Description |
|---------|-----|-------------|
| n8n Web Interface | http://localhost:5678 | Workflow editor and monitoring |
| Webhook Endpoint | http://localhost:5000/update-dashboard | Triggers dashboard update |
| Webhook Health Check | http://localhost:5000/health | Verify webhook is running |
| Dashboard | `dashboard/index.html` | Open in browser |

---

## Files Reference

| File | Purpose |
|------|---------|
| `docker-compose.yml` | n8n Docker configuration |
| `webhook_server.py` | Webhook server for n8n triggers |
| `n8n_workflow_simple.json` | Pre-configured n8n workflow |
| `config.json` | Google Drive file ID and credentials path |
| `scripts/fetch_from_sheets.py` | Data fetcher script |

---

## Summary

**One-Time Setup:**
1. `docker-compose up -d` - Start n8n
2. `python webhook_server.py` - Start webhook
3. Import `n8n_workflow_simple.json` to n8n
4. Activate workflow

**Daily Operation:**
- n8n runs in background (Docker)
- Webhook must be running (`python webhook_server.py`)
- Workflow triggers every Monday at 9 AM
- Manual trigger: Click "Test workflow" button
- View dashboard updates: Click **🔄 Refresh Data** button

**Key Features:**
- ✅ Automated weekly updates (Monday 9 AM)
- ✅ Manual trigger on-demand
- ✅ Dashboard refresh button (no hard refresh needed)
- ✅ Three layers of cache prevention
- ✅ Dual-currency support (USD/EUR)
- ✅ Execution history and monitoring

For support, check:
- n8n docs: https://docs.n8n.io/
- Webhook logs in terminal
- n8n **Executions** tab for workflow history
