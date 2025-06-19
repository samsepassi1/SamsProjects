# JSearch SMS Reporter

This repository contains various scripts. The `jsearch_to_sheet.py` script fetches job listings from the JSearch API and sends a summarized report via SMS using Twilio.

## Environment Variables

Set the following variables before running the script:

- `JSEARCH_API_KEY` – API key for the JSearch API.
- `TWILIO_ACCOUNT_SID` – Twilio account SID.
- `TWILIO_AUTH_TOKEN` – Twilio authentication token.
- `TWILIO_FROM_NUMBER` – Twilio phone number that sends messages.
- `SMS_TO_NUMBER` – Destination phone number for the SMS report.
- `JOB_QUERY` (optional) – Search query for JSearch. Defaults to `"software engineer"`.

## Running

Install dependencies:

```bash
pip install -r requirements.txt
```

Run the script manually:

```bash
python jsearch_to_sheet.py
```

The script is scheduled internally to run every three hours using APScheduler. Ensure it remains running if you rely on the scheduler.

