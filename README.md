# CBC Feed Monitor

Automated weekly Snowflake query that checks CBC live item feed status and writes results to a Google Sheet.

Runs every Friday at 9am ET via GitHub Actions.

## Setup

### 1. Google Cloud Service Account

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a project (or use an existing one)
3. Enable **Google Sheets API** and **Google Drive API**
4. Create a **Service Account** (IAM & Admin > Service Accounts)
5. Create a JSON key for the service account and download it
6. **Share the Google Sheet** with the service account email (e.g. `name@project.iam.gserviceaccount.com`) as **Editor**

### 2. GitHub Repository Secrets

Create a GitHub repo and add these secrets (Settings > Secrets > Actions):

| Secret | Value |
|--------|-------|
| `SNOWFLAKE_USER` | Your Snowflake username (e.g. `robbykhoutsaysana`) |
| `SNOWFLAKE_ACCOUNT` | `instacart-instacart` |
| `SNOWFLAKE_WAREHOUSE` | `developer_wh` |
| `SNOWFLAKE_ROLE` | `instacart_developer_role` |
| `SNOWFLAKE_PRIVATE_KEY_B64` | Base64-encoded RSA private key (see below) |
| `GOOGLE_SERVICE_ACCOUNT_B64` | Base64-encoded service account JSON (see below) |

#### Encoding secrets as base64

```bash
# Snowflake RSA key
base64 -i ~/.ssh/rsa_key.p8 | pbcopy

# Google service account JSON
base64 -i /path/to/service-account.json | pbcopy
```

Paste the clipboard contents as the secret value.

### 3. Local Testing (optional)

```bash
export SNOWFLAKE_USER="robbykhoutsaysana"
export SNOWFLAKE_PRIVATE_KEY_PATH="$HOME/.ssh/rsa_key.p8"
export GOOGLE_SERVICE_ACCOUNT_PATH="/path/to/service-account.json"

pip install -r requirements.txt
python update_sheet.py
```

## Manual Trigger

Go to Actions > "Weekly CBC Feed Monitor" > "Run workflow" to trigger manually.
