# Sentinel-2 passage notification

Checks the Copernicus Data Space every 15 minutes for new Sentinel-2 satellite
images over Vojvodina, and posts a Slack message when new ones appear.

Runs automatically on GitHub Actions — no computer needs to stay on.

## One-time setup

1. Go to this repo's **Settings → Secrets and variables → Actions → New repository secret**.
2. Name: `SLACK_WEBHOOK_URL`
3. Value: paste your Slack Incoming Webhook URL (starts with `https://hooks.slack.com/services/...`).
4. Click **Add secret**.

That's the only manual step. The workflow in `.github/workflows/check.yml` will
start running automatically every 15 minutes after this is added.

## Checking it's working

Go to the **Actions** tab of this repo — you'll see a run every 15 minutes
called "Check for new Sentinel-2 images". Green check = ran fine. Click any
run to see its log output.

## Running it manually

On the **Actions** tab, click "Check for new Sentinel-2 images" → **Run workflow**.
