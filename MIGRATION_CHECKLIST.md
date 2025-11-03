# Security Migration Checklist

Use this checklist to migrate from legacy hardcoded credentials to secure environment-based configuration.

## Pre-Migration Checklist

- [ ] I have read [SECURITY.md](SECURITY.md)
- [ ] I understand the security risks of hardcoded credentials
- [ ] I have a backup of my current working setup
- [ ] I am prepared to rotate credentials if they were committed to git

## Step 1: Identify Current Credentials

**Check what credentials you currently have:**

```bash
# Check config.json for sensitive data
grep -E "(google_drive_file_id|credentials_file)" dashboard/config.json

# Check docker-compose.yml for passwords
grep "PASSWORD" dashboard/docker-compose.yml

# Check if credentials were ever committed to git (CRITICAL!)
git log --all --full-history -- dashboard/credentials/
```

**Record your findings:**

- [ ] Google Drive File ID: `___________________________`
- [ ] Credentials file path: `___________________________`
- [ ] N8N password: `___________________________`
- [ ] Were credentials in git history? YES / NO

## Step 2: Assess Security Risk

**If credentials were found in git history:**

- [ ] **STOP**: Do NOT proceed until you rotate credentials
- [ ] Follow [Credential Rotation Guide](#credential-rotation-guide) below
- [ ] Verify old credentials are revoked
- [ ] Only then proceed to Step 3

**If credentials were never committed:**

- [ ] Good! Your exposure is limited to local filesystem
- [ ] Proceed to Step 3

## Step 3: Create .env File

```bash
# Copy the template
cp dashboard/.env.example dashboard/.env

# Verify it's created
ls -la dashboard/.env
```

**Fill in your values:**

```bash
# Edit the file
cd dashboard
nano .env  # or your preferred editor
```

**Checklist:**
- [ ] Set `GOOGLE_CREDENTIALS_FILE=credentials/your-service-account.json`
- [ ] Set `GOOGLE_DRIVE_FILE_ID=your_actual_file_id`
- [ ] Set `GOOGLE_SHEET_NAME=dashboard` (or your sheet name)
- [ ] Generate and set strong `N8N_BASIC_AUTH_PASSWORD`
- [ ] Verify no placeholder values remain

## Step 4: Test New Configuration

**Test each component:**

```bash
# 1. Test fetching data from Google Sheets/Drive
cd dashboard
python scripts/fetch_from_sheets.py

# Expected output: "Using file ID from environment variable"
# If you see "[LEGACY]", your .env is not being read correctly
```

**Verification checklist:**
- [ ] Script runs without errors
- [ ] No "[LEGACY]" warnings in output
- [ ] Data is fetched successfully
- [ ] Output files created in `data/processed/`

```bash
# 2. Test n8n with new password
docker-compose up -d

# 3. Try logging into n8n
# Open http://localhost:5678
# Username: admin
# Password: (from your .env file)
```

**Verification checklist:**
- [ ] n8n starts without errors
- [ ] Can login with new password
- [ ] Old password no longer works

```bash
# 4. Test webhook server
python webhook_server.py

# In another terminal:
curl -X POST http://localhost:5000/update-dashboard

# Expected: {"status": "success", ...}
```

**Verification checklist:**
- [ ] Webhook server starts successfully
- [ ] Webhook trigger works
- [ ] Data is updated

## Step 5: Clean Up Old Configuration

**Update config.json to use placeholders:**

```json
{
  "_comment": "SECURITY: Set sensitive values in .env file, not here!",
  "google_drive_file_id": "YOUR_FILE_ID_HERE",
  "credentials_file": "credentials/your-service-account.json",
  "data_settings": {
    "include_periods_through": "Sep-25",
    "exclude_periods": ["Oct-25", "Nov-25", "Dec-25"]
  }
}
```

**Checklist:**
- [ ] Replaced real file ID with `"YOUR_FILE_ID_HERE"`
- [ ] Replaced real credentials path with placeholder
- [ ] Kept non-sensitive settings (data_settings, chart_settings)
- [ ] Saved the file

## Step 6: Verify Git Safety

**Ensure sensitive files are ignored:**

```bash
cd dashboard

# These should all be listed (ignored):
git check-ignore .env .env.local credentials/

# These should NOT be ignored (we want to track them):
git check-ignore .env.example config.json
```

**Checklist:**
- [ ] `.env` is ignored
- [ ] `credentials/` is ignored
- [ ] `.env.example` is NOT ignored (should be empty output)
- [ ] `config.json` is NOT ignored

## Step 7: Commit Changes (Safe Files Only)

**Review what will be committed:**

```bash
git status
```

**Should be staging:**
- ✅ `.env.example` (template, no secrets)
- ✅ `config.json` (with placeholders only)
- ✅ `docker-compose.yml` (using env vars)
- ✅ `SECURITY.md` (documentation)
- ✅ `scripts/fetch_from_sheets.py` (updated logic)
- ✅ `webhook_server.py` (updated logic)
- ✅ `.gitignore` (updated patterns)

**Should NOT be staging:**
- ❌ `.env` (actual credentials)
- ❌ `credentials/*.json` (service account keys)

**Commit if safe:**

```bash
# Only if the above checks pass!
git add .env.example config.json docker-compose.yml SECURITY.md
git add scripts/fetch_from_sheets.py webhook_server.py .gitignore
git commit -m "Security: Migrate to environment-based credential management

- Add .env.example template for secure credential setup
- Update scripts to read from environment variables first
- Sanitize config.json with placeholder values
- Update docker-compose.yml to require env password
- Add comprehensive security documentation
- Improve .gitignore for better protection"

git push
```

**Final checklist:**
- [ ] Reviewed changes with `git diff --cached`
- [ ] No sensitive data in commit
- [ ] Commit message is descriptive
- [ ] Pushed to remote successfully

## Step 8: Post-Migration Verification

**Final tests:**

```bash
# 1. Fresh clone test (optional but recommended)
cd /tmp
git clone <your-repo-url> test-clone
cd test-clone/dashboard

# Should fail (no .env yet):
python scripts/fetch_from_sheets.py

# Copy your .env
cp <original-location>/.env .env

# Should work now:
python scripts/fetch_from_sheets.py
```

**Checklist:**
- [ ] Fresh clone doesn't contain `.env` or credentials
- [ ] Setup instructions in SECURITY.md are clear
- [ ] All functionality works with `.env` configuration
- [ ] No [LEGACY] warnings in logs

## Credential Rotation Guide

**If credentials were committed to git, follow these steps:**

### 1. Revoke Google Service Account

```bash
# 1. Go to Google Cloud Console
# https://console.cloud.google.com/

# 2. Navigate to: IAM & Admin → Service Accounts

# 3. Find your service account (e.g., kpi-dashboard-bot@...)

# 4. Click on it → Keys tab

# 5. Delete ALL keys

# 6. OR delete the entire service account
```

**Verification:**
- [ ] All keys deleted from service account
- [ ] Service account access revoked
- [ ] Tested that old credentials no longer work

### 2. Create New Service Account

```bash
# Follow the guide in SECURITY.md to create a new service account
# with a DIFFERENT name
```

**Checklist:**
- [ ] New service account created
- [ ] New JSON key downloaded
- [ ] Saved to `credentials/` directory with new filename
- [ ] Updated `.env` with new credentials path

### 3. Update Sharing Permissions

```bash
# 1. Open your Google Sheet/Drive file
# 2. Remove OLD service account email from sharing
# 3. Add NEW service account email
# 4. Grant "Viewer" permissions
```

**Checklist:**
- [ ] Old service account removed from sharing
- [ ] New service account added
- [ ] Permissions verified (can access file)

### 4. Change N8N Password

```bash
# Generate new password
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Update .env file
# Restart n8n
docker-compose restart
```

**Checklist:**
- [ ] New password generated
- [ ] Updated in `.env` file
- [ ] n8n restarted successfully
- [ ] Can login with new password

### 5. Clean Git History (Advanced - DANGEROUS!)

**⚠️ WARNING:** This rewrites git history. Coordinate with your team!

```bash
# Backup first!
git clone <repo> backup-before-history-rewrite

# Remove credentials from all history
git filter-branch --force --index-filter \
  "git rm --cached --ignore-unmatch dashboard/credentials/*.json \
                                    dashboard/config.json" \
  --prune-empty --tag-name-filter cat -- --all

# Verify credentials are gone
git log --all --full-history -- dashboard/credentials/

# Force push (TEAM MUST RECLONE!)
git push origin --force --all
git push origin --force --tags

# Notify team: Everyone must delete and reclone repository
```

**Checklist:**
- [ ] Team notified of history rewrite
- [ ] Everyone has committed their work
- [ ] Backup created
- [ ] History rewritten
- [ ] Verified credentials removed
- [ ] Force pushed successfully
- [ ] All team members have recloned

### 6. Audit Logs

**Check for unauthorized access:**

```bash
# 1. Google Workspace Admin Console
# https://admin.google.com/

# 2. Reporting → Audit → Drive

# 3. Search for your file name

# 4. Review access logs for suspicious activity
```

**Checklist:**
- [ ] Reviewed audit logs
- [ ] No suspicious access detected
- [ ] Documented timeline of exposure
- [ ] Recorded any unauthorized access

---

## Migration Complete! 🎉

Once you've completed all steps:

- [ ] All credentials are in `.env` file
- [ ] No sensitive data in git repository
- [ ] All scripts work with new configuration
- [ ] Team members trained on new process
- [ ] Documentation updated
- [ ] `.env.example` committed as template

**Security posture:**
- ✅ Credentials never committed to git
- ✅ Environment-based configuration
- ✅ Strong passwords in use
- ✅ Minimal service account permissions
- ✅ Regular rotation schedule planned

---

## Troubleshooting

**Issue: "Using file ID from [LEGACY] config.json"**

**Solution:**
```bash
# Check .env file exists
ls -la dashboard/.env

# Check values are set (should show variable names, not values)
grep GOOGLE_DRIVE_FILE_ID dashboard/.env

# Try setting environment variable manually
export GOOGLE_DRIVE_FILE_ID="your_id_here"
python scripts/fetch_from_sheets.py
```

**Issue: "No Google Drive file ID found!"**

**Solution:**
```bash
# Verify .env file has no typos
cat dashboard/.env | grep GOOGLE_DRIVE_FILE_ID

# Check for extra spaces or quotes
# Should be: GOOGLE_DRIVE_FILE_ID=abc123xyz
# NOT: GOOGLE_DRIVE_FILE_ID = "abc123xyz"
```

**Issue: "FileNotFoundError: credentials/..."**

**Solution:**
```bash
# Check credentials file exists
ls -la dashboard/credentials/

# Verify path in .env matches actual file
cat dashboard/.env | grep GOOGLE_CREDENTIALS_FILE

# Test from correct directory
cd dashboard
python scripts/fetch_from_sheets.py
```

**Issue: n8n login fails with new password**

**Solution:**
```bash
# Stop and remove container
docker-compose down -v

# Verify .env file is being read
cat .env | grep N8N_BASIC_AUTH_PASSWORD

# Start fresh
docker-compose up -d

# Check logs
docker-compose logs n8n
```

---

**Need Help?**

See [SECURITY.md](SECURITY.md) for complete documentation or create an issue in the repository.

**Last Updated:** 2025-11-03
