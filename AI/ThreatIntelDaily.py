import requests
import pandas as pd
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend for headless scripts
import matplotlib.pyplot as plt
from fpdf import FPDF
from datetime import datetime
from collections import Counter
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from apscheduler.schedulers.blocking import BlockingScheduler
import os

# OTX API Configuration
API_KEY = ""
BASE_URL = "https://otx.alienvault.com/api/v1"

# Email Configuration
EMAIL_USER = ""  # Sender's email address
EMAIL_PASSWORD = ""  # Email account password or app-specific password
RECEIVER_EMAIL = ""  # Recipient's email address

class PDF(FPDF):
    def header(self):
        self.set_font("Arial", "B", 12)
        self.cell(0, 10, "Threat Intelligence Dashboard", align="C", ln=True)

    def footer(self):
        self.set_y(-15)
        self.set_font("Arial", "I", 8)
        self.cell(0, 10, f"Page {self.page_no()}", align="C")

def fetch_data(endpoint):
    headers = {"X-OTX-API-KEY": API_KEY}
    try:
        response = requests.get(f"{BASE_URL}/{endpoint}", headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data: {e}")
        return None

def generate_table(data):
    df = pd.DataFrame(data)
    if df.empty:
        print("No data available to generate the table.")
        return None

    # Keep relevant columns and add a description placeholder
    columns_to_keep = ["id", "name", "author_name", "created", "modified", "tags", "description"]
    if "description" not in df.columns:
        df["description"] = "No description available"  # Placeholder if missing
    df = df[columns_to_keep]
    df["created"] = pd.to_datetime(df["created"]).dt.strftime("%Y-%m-%d %H:%M:%S")
    df["modified"] = pd.to_datetime(df["modified"]).dt.strftime("%Y-%m-%d %H:%M:%S")
    return df

def generate_bar_chart(df, column, output_image):
    chart_data = df[column].value_counts()
    plt.figure(figsize=(10, 6))
    chart_data.plot(kind="bar", color="skyblue", edgecolor="black")
    plt.title(f"Frequency of {column.capitalize()}", fontsize=16)
    plt.xlabel(column.capitalize(), fontsize=14)
    plt.ylabel("Count", fontsize=14)
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    plt.savefig(output_image)
    plt.close()
    print(f"Bar chart saved as {output_image}")

def generate_pie_chart(df, column, output_image):
    tags_list = df[column].explode().dropna().tolist()
    tag_counts = Counter(tags_list).most_common(5)
    labels, sizes = zip(*tag_counts)

    plt.figure(figsize=(8, 8))
    plt.pie(
        sizes,
        labels=labels,
        autopct="%1.1f%%",
        startangle=140,
        colors=["#66b3ff", "#99ff99", "#ffcc99", "#ff9999", "#c2c2f0"],
        textprops={"fontsize": 10},
    )
    plt.title(f"Top 5 Most Common Tags", fontsize=16)
    plt.tight_layout()
    plt.savefig(output_image)
    plt.close()
    print(f"Pie chart saved as {output_image}")

def add_pulse_to_pdf(pdf, pulse):
    pdf.add_page()
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, f"Pulse ID: {pulse['id']}", ln=True)

    pdf.set_font("Arial", "", 12)
    pdf.cell(0, 10, f"Name: {pulse['name']}", ln=True)
    pdf.cell(0, 10, f"Author: {pulse['author_name']}", ln=True)
    pdf.cell(0, 10, f"Created: {pulse['created']}", ln=True)
    pdf.cell(0, 10, f"Modified: {pulse['modified']}", ln=True)
    pdf.cell(0, 10, "Tags:", ln=True)
    pdf.set_font("Arial", "I", 10)
    pdf.multi_cell(0, 10, ", ".join(pulse['tags']) if pulse['tags'] else "No tags available")
    pdf.set_font("Arial", "", 12)
    pdf.cell(0, 10, "Description:", ln=True)
    pdf.set_font("Arial", "I", 10)
    pdf.multi_cell(0, 10, pulse['description'] if pulse['description'] else "No description available")

def generate_pdf_report(dataframe, bar_chart, pie_chart, output_pdf):
    pdf = PDF()
    pdf.set_auto_page_break(auto=True, margin=15)

    # Title Page
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(200, 10, "Threat Intelligence Dashboard", ln=True, align="C")
    pdf.set_font("Arial", "I", 12)
    pdf.cell(200, 10, f"Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", ln=True, align="C")
    pdf.ln(20)

    # Add Bar Chart Section
    pdf.add_page()
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, "1. Bar Chart - Frequency of Authors", ln=True)
    pdf.image(bar_chart, x=10, y=30, w=180)

    # Add Pie Chart Section
    pdf.add_page()
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, "2. Pie Chart - Distribution of Tags", ln=True)
    pdf.image(pie_chart, x=10, y=30, w=180)

    # Add Individual Pulse Pages
    for _, pulse in dataframe.iterrows():
        add_pulse_to_pdf(pdf, pulse)

    pdf.output(output_pdf)
    print(f"PDF report saved as {output_pdf}")

def send_email_with_attachment(subject, body, to_email, attachment_path):
    msg = MIMEMultipart()
    msg['From'] = EMAIL_USER
    msg['To'] = to_email
    msg['Subject'] = subject

    # Email body
    msg.attach(MIMEText(body, 'plain'))

    try:
        with open(attachment_path, "rb") as attachment:
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(attachment.read())
            encoders.encode_base64(part)
            part.add_header(
                "Content-Disposition",
                f"attachment; filename={os.path.basename(attachment_path)}",
            )
            msg.attach(part)

        print("Connecting to the SMTP server...")
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            print("Logging into the SMTP server...")
            server.login(EMAIL_USER, EMAIL_PASSWORD)
            print(f"Logged in successfully. Sending email to {to_email}...")
            server.send_message(msg)
            print(f"Email sent successfully to {to_email}")
    except Exception as e:
        print(f"Failed to send email: {e}")

def main():
    print("Fetching threat pulses...")
    pulses = fetch_data("pulses/subscribed")

    if not pulses or "results" not in pulses:
        print("No data available from the API.")
        return

    data = pulses["results"]

    df = generate_table(data)
    if df is None:
        return

    bar_chart_file = "author_frequency_chart.png"
    generate_bar_chart(df, "author_name", bar_chart_file)

    pie_chart_file = "tags_distribution_chart.png"
    generate_pie_chart(df, "tags", pie_chart_file)

    pdf_file = "individual_pulse_pages_report.pdf"
    generate_pdf_report(df, bar_chart_file, pie_chart_file, pdf_file)

    # Email the report
    send_email_with_attachment(
        subject="Daily Threat Intelligence Report",
        body="Please find the daily Threat Intelligence Report attached.",
        to_email=RECEIVER_EMAIL,
        attachment_path=pdf_file
    )

# Schedule the script to run daily at 4:00 PM
if __name__ == "__main__":
    scheduler = BlockingScheduler()
    scheduler.add_job(main, 'cron', hour=16, minute=0)  # 4:00 PM
    print("Scheduler started. The report will be sent daily at 4:00 PM.")
    scheduler.start()
