# CBC Feed Monitor

Automated weekly Snowflake query that checks CBC live item feed status and writes results to a Google Sheet.

Runs every Friday at 9am ET via GitHub Actions.

## How It Works

1. **GitHub Actions** runs a Snowflake query every Friday and commits results as a CSV to this repo.
2. **Google Apps Script** (time-triggered) fetches the CSV and creates a new tab in the Google Sheet.

## Setup

### 1. GitHub Repository Secrets

Add these secrets (Settings > Secrets > Actions):

| Secret | Value |
|--------|-------|
| `SNOWFLAKE_USER` | Your Snowflake username |
| `SNOWFLAKE_ACCOUNT` | Your Snowflake account identifier |
| `SNOWFLAKE_WAREHOUSE` | Your Snowflake warehouse |
| `SNOWFLAKE_ROLE` | Your Snowflake role |
| `SNOWFLAKE_PRIVATE_KEY_B64` | Base64-encoded RSA private key (see below) |

#### Encoding the RSA key

```bash
base64 -i /path/to/rsa_key.p8 | pbcopy
```

Paste the clipboard contents as the secret value.

### 2. Apps Script

1. Open the target Google Sheet
2. Extensions > Apps Script
3. Paste the code from `apps_script.js`
4. Update `GITHUB_CSV_URL` with this repo's raw URL for `results/latest.csv`
5. Run `test` to authorize
6. Add a time-driven trigger for `importLatestCSV` (weekly, Friday, 9am)

### 3. Local Testing (optional)

```bash
export SNOWFLAKE_USER="your_username"
export SNOWFLAKE_PRIVATE_KEY_PATH="/path/to/rsa_key.p8"

pip install -r requirements.txt
python update_sheet.py
```

## Updating the Item List

Edit `CBC_ITEM_LIST.csv` in this repo. The next scheduled run will use the updated list.

## Manual Trigger

Go to Actions > "Weekly CBC Feed Monitor" > "Run workflow" to trigger manually.
