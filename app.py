import streamlit as st
import openai
from datetime import datetime
from fpdf import FPDF
import yagmail
import os
import csv
import gspread
from google.oauth2.service_account import Credentials
# --- APP CONFIGURATION ---
PAGE_TITLE = "DeloitteSmart™ Client Portal"
PAGE_ICON = ":moneybag:"
LAYOUT = "wide"
INITIAL_SIDEBAR_STATE = "expanded"
REGISTRATIONS_FILE = "registrations.csv"
DELOITTE_LOGO = "deloitte_logo.png"

st.set_page_config(
    page_title=PAGE_TITLE,
    page_icon=PAGE_ICON,
    layout=LAYOUT,
    initial_sidebar_state=INITIAL_SIDEBAR_STATE
)

# --- HELPER: Clean text for PDF ---
def safe_text(txt: str) -> str:
    replacements = {'™': '(TM)', '–': '-', '≥': '>=', '✓': 'v', '✔': 'v'}
    for k, v in replacements.items():
        txt = txt.replace(k, v)
    return txt.encode('latin1', 'ignore').decode('latin1')

# --- SECRETS & GOOGLE SHEETS SETUP ---
openai_api_key = st.secrets["OPENAI_API_KEY"]
email_user = st.secrets["EMAIL_USER"]
email_pass = st.secrets["EMAIL_PASS"]
gsheet_credentials = st.secrets["GSHEET_CREDENTIALS"]
gsheet_id = st.secrets["GSHEET_ID"]

creds = Credentials.from_service_account_info(
    gsheet_credentials,
    scopes=["https://www.googleapis.com/auth/spreadsheets"]
)
gc = gspread.Client(auth=creds)
sheet = gc.open_by_key(gsheet_id).sheet1

# Ensure header row exists
if not sheet.get_all_records():
    sheet.append_row([
        "timestamp", "name", "email", "company",
        "score", "status", "report_recipient", "internal_cc"
    ])

# --- REGISTRATION FLOW ---
if "registered" not in st.session_state:
    st.session_state.registered = False

if not st.session_state.registered:
    st.title(PAGE_TITLE)
    st.subheader("Please register to continue")
    name = st.text_input("Your Name")
    mail = st.text_input("Your Email")
    comp = st.text_input("Company Name")
    if st.button("Register"):
        if not (name and mail and comp):
            st.error("All fields are required.")
        else:
            timestamp = datetime.now().isoformat()
            registration_data = [timestamp, name, mail, comp]

            # Save to CSV
            new_file = not os.path.exists(REGISTRATIONS_FILE)
            with open(REGISTRATIONS_FILE, "a", newline="") as f:
                writer = csv.writer(f)
                if new_file:
                    writer.writerow(["timestamp", "name", "email", "company"])
                writer.writerow(registration_data)

            # Log to Google Sheet
            sheet.append_row(registration_data)

            # Update session
            st.session_state.registered = True
            st.session_state.user_name = name
            st.session_state.user_email = mail
            st.session_state.company = comp
            st.success(f"Registered as {name} ({comp})!")
    st.stop()

# --- SIDEBAR ---
with st.sidebar:
    if os.path.exists(DELOITTE_LOGO):
        st.image(DELOITTE_LOGO, width=200)
    st.markdown(f"### User: {st.session_state.user_name}")
    st.markdown(f"#### Company: {st.session_state.company}")
    st.markdown("---")
    st.markdown("Secure | Intelligent | Personalized")

# --- MAIN LAYOUT ---
st.title(f"Hello {st.session_state.user_name}, welcome back!")
st.caption("Your subsidy assistant is ready.")
mode = st.radio("Mode:", ["Chat with AI", "Eligibility Self-Check"], index=0)

# --- CHAT WITH AI ---
if mode == "Chat with AI":
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    st.subheader("Ask a question about government subsidies")
    question = st.text_input("Your question:")
    if st.button("Send") and question:
        prompt = f"You are SubsidySmart(TM), an expert subsidy advisor. Question: {question}"
        with st.spinner("AI is responding..."):
            response = openai.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a professional subsidy advisor."},
                    {"role": "user", "content": prompt}
                ]
            )
            answer = response.choices[0].message.content
        st.session_state.chat_history.append((question, answer))
    for q, a in reversed(st.session_state.chat_history):
        st.markdown(f"**You:** {q}")
        st.markdown(f"**AI:** {a}")
        st.markdown("---")

# --- ELIGIBILITY SELF-CHECK & REPORT ---
else:
    st.subheader("Eligibility Self-Check & Report")
    report_recipient = st.text_input("Send report to Email:", value=st.session_state.user_email)
    company_age = st.radio("Company age?", ["<3 years", "≥3 years"])
    industries = st.multiselect("Industry(s)", ["AI", "IoT", "Biotech", "Green Energy", "Other"])
    rd_budget = st.radio("R&D Budget?", ["<200K", "≥200K"])
    export_status = st.radio("Export?", ["No", "Yes"])
    revenue = st.radio("Revenue?", ["<500K", "≥500K"])
    employees = st.slider("Employees", 1, 200, 10)
    provided_docs = st.multiselect("Documents Provided", ["Business Plan", "Org Chart", "Budget", "Export Plan", "Pitch Deck"])

    if st.button("Calculate & Send Report"):
        # Compute score
        score = 0
        score += 15 if company_age == "≥3 years" else 0
        score += 20 if any(i in industries for i in ["AI", "IoT", "Biotech", "Green Energy"]) else 0
        score += 20 if rd_budget == "≥200K" else 0
        score += 15 if export_status == "Yes" else 0
        score += 10 if revenue == "≥500K" else 0
        score += 10 if 5 <= employees <= 100 else 0
        score += len(provided_docs) * 2
        status = "Highly Eligible" if score >= 85 else ("Needs Review" if score >= 65 else "Not Eligible")

        st.metric("Eligibility Score", f"{score}%")
        st.markdown(f"**{status}**")

        # Log to sheet
        row_data = [
            datetime.now().isoformat(),
            st.session_state.user_name,
            st.session_state.user_email,
            st.session_state.company,
            score,
            status,
            report_recipient,
            "asif.baig@innov8.jp"
        ]
        sheet.append_row(row_data)

        # Generate PDF
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        pdf.cell(0, 10, safe_text("DeloitteSmart(TM) Subsidy Report"), ln=1, align='C')
        pdf.ln(5)
        report_info = (
            f"User: {st.session_state.user_name} | Company: {st.session_state.company} | "
            f"Email: {report_recipient} | Score: {score}% - {status}"
        )
        pdf.multi_cell(0, 8, safe_text(report_info))
        pdf.ln(5)
        detail_lines = [
            f"Age: {company_age}",
            f"Industry: {', '.join(industries)}",
            f"R&D: {rd_budget}",
            f"Export: {export_status}",
            f"Revenue: {revenue}",
            f"Employees: {employees}",
            f"Documents: {', '.join(provided_docs)}"
        ]
        pdf.multi_cell(0, 8, safe_text("\n".join(detail_lines)))
        pdf_bytes = pdf.output(dest='S').encode('latin-1')
        report_filename = f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        st.download_button("Download PDF Report", data=pdf_bytes, file_name=report_filename, mime='application/pdf')

        # Send email
        if email_user and email_pass and report_recipient:
            try:
                yag = yagmail.SMTP(email_user, email_pass)
                yag.send(
                    to=[report_recipient, "asif.baig@innov8.jp"],
                    subject="Your DeloitteSmart(TM) Subsidy Report",
                    contents=safe_text("Please see attached report."),
                    attachments={report_filename: pdf_bytes}
                )
                st.success("Emailed to client and Innov8.")
            except Exception as e:
                st.error(f"Error sending email: {e}")
