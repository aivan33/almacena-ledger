# Security Guide

This guide covers secure credential management, setup instructions, and migration from legacy hardcoded credentials.

## 🔒 Security Overview

As of the latest update, this project uses **environment variable-based credential management** to prevent accidental exposure of sensitive data. All credentials are stored in a `.env` file that is **never committed to git**.

### What Changed?

**Before (Insecure):**
- ❌ Credentials hardcoded in `config.json`
- ❌ Weak passwords in `docker-compose.yml`
- ❌ Risk of accidentally committing secrets

**After (Secure):**
- ✅ Credentials in `.env` file (gitignored)
- ✅ Environment variable-based configuration
- ✅ Secure defaults with mandatory password setup
- ✅ Clear separation of sensitive and non-sensitive config

## 🚀 Quick Setup (New Users)

### Step 1: Copy Environment Template

```bash
# From the dashboard directory
cp .env.example .env
```

### Step 2: Configure Your Credentials

Edit the `.env` file with your actual values:

```bash
# Open in your editor
notepad .env      # Windows
nano .env         # Linux/macOS
```

**Required settings:**

```bash
# Google Service Account credentials file
GOOGLE_CREDENTIALS_FILE=credentials/your-service-account.json

# Google Drive file ID (extract from URL)
GOOGLE_DRIVE_FILE_ID=1ABC123xyz...

# N8N password (generate a strong one!)
N8N_BASIC_AUTH_PASSWORD=your_secure_password_here
```

### Step 3: Set Up Google Credentials

1. **Create a Google Cloud Project** (if you don't have one)
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project or select existing

2. **Enable Required APIs**
   - Enable Google Sheets API
   - Enable Google Drive API

3. **Create Service Account**
   - Go to IAM & Admin → Service Accounts
   - Click "Create Service Account"
   - Name: `kpi-dashboard-bot` (or your choice)
   - Click "Create and Continue"
   - Skip roles (we'll set permissions in Sheets)
   - Click "Done"

4. **Generate JSON Key**
   - Click on your service account
   - Go to "Keys" tab
   - Click "Add Key" → "Create new key"
   - Choose JSON format
   - Download the file

5. **Place Credentials File**
   ```bash
   # Create credentials directory if it doesn't exist
   mkdir -p credentials

   # Move your downloaded JSON file
   mv ~/Downloads/your-service-account-key.json credentials/your-service-account.json

   # Verify it's gitignored
   git check-ignore credentials/your-service-account.json
   # Should output: credentials/your-service-account.json
   ```

6. **Share Your Google Sheet/Drive File**
   - Open your Google Sheet or Drive file
   - Click "Share"
   - Add your service account email (e.g., `kpi-dashboard-bot@your-project.iam.gserviceaccount.com`)
   - Give "Viewer" or "Editor" access (Viewer is recommended for security)

### Step 4: Generate Strong N8N Password

```bash
# Generate a secure random password (run in terminal)
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Copy the output to your .env file
```

### Step 5: Verify Setup

```bash
# Test fetching data (should not error)
python scripts/fetch_from_sheets.py

# Start n8n with your secure password
docker-compose up -d

# Check n8n is running
curl http://localhost:5678
```

---

## 🔄 Migration Guide (Existing Users)

If you previously had credentials in `config.json` or `docker-compose.yml`, follow these steps:

### Step 1: Identify Your Current Credentials

Check what you have currently:

```bash
# Check config.json
cat config.json | grep -E "(google_drive_file_id|credentials_file)"

# Check docker-compose.yml
cat docker-compose.yml | grep PASSWORD
```

### Step 2: Rotate Compromised Credentials

**IMPORTANT:** If your credentials were previously committed to git, they are compromised and MUST be rotated:

1. **Google Service Account - REVOKE IMMEDIATELY**
   ```
   # Check if credentials were in git history
   git log --all --full-history -- credentials/

   # If found, REVOKE the service account:
   # 1. Go to Google Cloud Console
   # 2. IAM & Admin → Service Accounts
   # 3. Find your service account
   # 4. Delete it or disable all keys
   # 5. Create a NEW service account following Step 3 above
   ```

2. **N8N Password - Change It**
   ```bash
   # Generate new secure password
   python -c "import secrets; print(secrets.token_urlsafe(32))"

   # Add to .env file
   echo "N8N_BASIC_AUTH_PASSWORD=your_new_password" >> .env
   ```

3. **Audit Access Logs**
   - Check Google Workspace audit logs for unauthorized access
   - Review Google Drive file access history
   - Look for suspicious activity

### Step 3: Migrate to .env

Create your `.env` file with the migrated values:

```bash
# Copy template
cp .env.example .env

# Edit with your migrated values
nano .env
```

**Migration mapping:**

| Old Location | New Location | Example |
|-------------|--------------|---------|
| `config.json` → `google_drive_file_id` | `.env` → `GOOGLE_DRIVE_FILE_ID` | `1ABC123xyz` |
| `config.json` → `credentials_file` | `.env` → `GOOGLE_CREDENTIALS_FILE` | `credentials/your-sa.json` |
| `docker-compose.yml` → `N8N_BASIC_AUTH_PASSWORD` | `.env` → `N8N_BASIC_AUTH_PASSWORD` | Generate new! |

### Step 4: Clean Up Old Config

The `config.json` now only stores non-sensitive settings:

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

Leave placeholder values in `config.json`. Real values go in `.env`.

### Step 5: Verify Migration

```bash
# Should use environment variables (no [LEGACY] warning)
python scripts/fetch_from_sheets.py

# Check output - should say "Using file ID from environment variable"
# If it says "[LEGACY] Using file ID from config.json", check your .env
```

---

## 🛡️ Security Best Practices

### 1. Never Commit Sensitive Files

**Already protected by `.gitignore`:**
```
.env
.env.local
credentials/
*.json (except config.json, package.json, workflows)
```

**Always verify before committing:**
```bash
# Check what would be committed
git status

# Verify sensitive files are ignored
git check-ignore .env credentials/
```

### 2. Use Minimal Permissions

**Google Service Account:**
- Grant **read-only** access to Google Sheets/Drive (not Editor)
- Only share specific files needed, not entire folders
- Regularly audit who has access to your files

**N8N:**
- Change default credentials immediately
- Use strong, unique passwords
- Consider IP restrictions if exposed to internet
- Keep n8n updated to latest version

### 3. Rotate Credentials Regularly

**Recommended schedule:**
- Service account keys: Every 90 days
- N8N password: Every 180 days
- After team member departure: Immediately

**Rotation process:**
```bash
# 1. Create new service account key in Google Cloud Console
# 2. Download new JSON file
# 3. Update .env file
# 4. Test with: python scripts/fetch_from_sheets.py
# 5. Delete old key from Google Cloud Console
```

### 4. Environment-Specific Configuration

Use different `.env` files for different environments:

```bash
# Development
.env.dev

# Production
.env.prod

# Load specific environment
export $(cat .env.dev | xargs)
python scripts/fetch_from_sheets.py
```

### 5. Credential Storage

**For personal use:**
- Keep `.env` file secure on your local machine
- Use disk encryption (BitLocker, FileVault, LUKS)
- Don't store credentials in cloud sync folders (Dropbox, OneDrive)

**For team use:**
- Use a password manager (1Password, LastPass, Bitwarden)
- Share credentials securely (not via Slack/email)
- Document who has access

### 6. Security Monitoring

**Set up alerts:**
```bash
# Google Cloud - Set up audit logging alerts
# 1. Go to Google Cloud Console
# 2. Logging → Logs Explorer
# 3. Create alert for service account usage
# 4. Get notified of unusual activity
```

**Regular audits:**
- Review Google Workspace audit logs monthly
- Check n8n execution logs for failures
- Monitor for unauthorized file access

---

## 🚨 Incident Response

### If Credentials Are Compromised

**IMMEDIATE ACTIONS:**

1. **Revoke access**
   ```bash
   # Google Service Account
   # Go to Cloud Console → IAM → Service Accounts → Delete Key

   # N8N
   # Stop container: docker-compose down
   ```

2. **Change all passwords**
   - Generate new N8N password
   - Create new service account with new key

3. **Audit access logs**
   - Check Google Workspace logs for unauthorized access
   - Review what data may have been accessed

4. **Notify stakeholders**
   - Inform team members
   - Document the incident
   - Update security procedures

5. **Clean git history** (if committed)
   ```bash
   # Remove from git history (DANGER: rewrites history!)
   git filter-branch --force --index-filter \
     'git rm --cached --ignore-unmatch credentials/*.json' \
     --prune-empty --tag-name-filter cat -- --all

   # Force push (coordinate with team!)
   git push origin --force --all

   # Everyone must reclone: git clone <repo>
   ```

### Prevention Checklist

Before making public or sharing:

- [ ] All credentials in `.env` file (not config.json)
- [ ] `.env` is in `.gitignore`
- [ ] No credentials in git history
- [ ] Strong, unique N8N password set
- [ ] Service account has minimal permissions
- [ ] All team members trained on security practices
- [ ] Audit logging enabled
- [ ] Incident response plan documented

---

## 📚 Additional Resources

- [Google Cloud Security Best Practices](https://cloud.google.com/security/best-practices)
- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [n8n Security Documentation](https://docs.n8n.io/hosting/security/)
- [Git Secrets Prevention](https://github.com/awslabs/git-secrets)

---

## ❓ FAQ

**Q: Can I still use config.json for credentials?**
A: Yes, but it's **not recommended**. The scripts will show a `[LEGACY]` warning if you do. Migrate to `.env` for better security.

**Q: What if I forget my N8N password?**
A: Update the password in `.env` and restart n8n: `docker-compose restart`

**Q: How do I check if my credentials are secure?**
A: Run: `git check-ignore .env credentials/` - both should be listed. Also check: `git log --all -- credentials/` should show nothing.

**Q: Can I commit .env.example?**
A: Yes! `.env.example` contains NO sensitive data and should be committed as a template.

**Q: What's the difference between .env and config.json?**
A: `.env` stores **secrets** (never committed), `config.json` stores **non-sensitive settings** (committed to git).

---

## 📞 Support

If you discover a security vulnerability, please email security@[yourdomain] or create a private GitHub security advisory. Do not create public issues for security problems.

---

**Last Updated:** 2025-11-03
**Version:** 2.0 (Environment-based security)
