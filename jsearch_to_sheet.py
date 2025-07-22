import os
import requests
from twilio.rest import Client
from apscheduler.schedulers.blocking import BlockingScheduler

JSEARCH_API_KEY = os.environ.get("JSEARCH_API_KEY")
JSEARCH_API_HOST = "jsearch.p.rapidapi.com"

TWILIO_ACCOUNT_SID = os.environ.get("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.environ.get("TWILIO_AUTH_TOKEN")
TWILIO_FROM_NUMBER = os.environ.get("TWILIO_FROM_NUMBER")
SMS_TO_NUMBER = os.environ.get("SMS_TO_NUMBER")


def fetch_jsearch_jobs():
    url = f"https://{JSEARCH_API_HOST}/search"
    params = {
        "query": os.environ.get("JOB_QUERY", "software engineer"),
        "page": "1",
        "num_pages": "1",
    }
    headers = {
        "X-RapidAPI-Key": JSEARCH_API_KEY,
        "X-RapidAPI-Host": JSEARCH_API_HOST,
    }
    response = requests.get(url, headers=headers, params=params, timeout=30)
    response.raise_for_status()
    data = response.json()
    return data.get("data", [])


def send_sms_report(jobs):
    client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
    lines = [
        f"{job.get('job_title')} - {job.get('employer_name')} (Fit: {job.get('fit_score', 'N/A')})"
        for job in jobs
    ]
    if not lines:
        return
    text = "\n".join(lines)
    max_length = 1500
    for i in range(0, len(text), max_length):
        client.messages.create(
            body=text[i : i + max_length],
            from_=TWILIO_FROM_NUMBER,
            to=SMS_TO_NUMBER,
        )


def main():
    jobs = fetch_jsearch_jobs()
    send_sms_report(jobs)


if __name__ == "__main__":
    scheduler = BlockingScheduler()
    scheduler.add_job(main, "cron", hour="*/3")
    scheduler.start()
