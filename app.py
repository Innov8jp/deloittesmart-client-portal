# DeloitteSmart™ Client Portal — Full Workflow with Google Sheets Integration

import streamlit as st
import openai
from datetime import datetime
from fpdf import FPDF
import yagmail
import os
import csv
import json
import gspread
from google.oauth2.service_account import Credentials

# --- CONFIG ---
st.set_page_config(
    page_title="DeloitteSmart™ Client Portal",
    page_icon=":moneybag:",
    layout="wide"
)

# --- HELPER: Sanitize text for PDF ---
def safe_text(txt: str) -> str:
    replacements = {'™':'(TM)','–':'-','≥':'>=','✓':'v','✔':'v'}
    for k,v in replacements.items(): txt = txt.replace(k,v)
    return txt.encode('latin1','ignore').decode('latin1')

# --- SECRETS & Google Sheets Setup ---
openai.api_key = st.secrets["OPENAI_API_KEY"]
email_user = st.secrets["EMAIL_USER"]
email_pass = st.secrets["EMAIL_PASS"]
# GSHEET_CREDENTIALS: JSON string of service account key
# GSHEET_ID: the spreadsheet ID
creds_dict = json.loads(st.secrets["GSHEET_CREDENTIALS"])
creds = Credentials.from_service_account_info(creds_dict, scopes=[
    "https://www.googleapis.com/auth/spreadsheets"
])
gc = gspread.Client(auth=creds)
sheet = gc.open_by_key(st.secrets["GSHEET_ID"]).sheet1

# --- REGISTRATION with Persistence & Sheets ---
if "registered" not in st.session_state:
    st.session_state.registered = False
if not st.session_state.registered:
    st.title("Welcome to DeloitteSmart™ Client Portal")
    st.subheader("Register to get started")
    name = st.text_input("Your Name", key="reg_name")
    user_email = st.text_input("Your Email", key="reg_email")
    company = st.text_input("Company Name", key="reg_company")
    if st.button("Register"):
        if not name or not user_email or not company:
            st.error("Please complete all fields.")
        else:
            timestamp = datetime.now().isoformat()
            # Persist to CSV
            reg_file = "registrations.csv"
            header = ["timestamp","name","email","company"]
            row = [timestamp, name, user_email, company]
            write_header = not os.path.exists(reg_file)
            with open(reg_file, mode='a', newline='') as f:
                writer = csv.writer(f)
                if write_header: writer.writerow(header)
                writer.writerow(row)
            # Append to Google Sheet
            sheet.append_row(row)
            # Set session
            st.session_state.registered = True
            st.session_state.user_name = name
            st.session_state.user_email = user_email
            st.session_state.company = company
            st.success(f"Registered: {name} at {company}.")
    st.stop()

# --- SIDEBAR ---
with st.sidebar:
    logo = "deloitte_logo.png"
    if os.path.exists(logo): st.image(logo, width=200)
    st.markdown(f"# DeloitteSmart™ Client Portal")
    st.markdown(f"Logged in: {st.session_state.user_name} ({st.session_state.company})")
    st.markdown("Secure | Intelligent | Personalized")

# --- MAIN ---
st.title(f"Hello {st.session_state.user_name}, welcome back!")
st.caption("Your subsidy assistant is ready.")
mode = st.radio("Mode:", ["Client Chat","Eligibility Self-Check"], index=0)

# --- CLIENT CHAT MODE ---
if mode == "Client Chat":
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    q = st.text_input("Ask subsidy question:", key="chat_q")
    if st.button("Submit Question") and q:
        prompt = f"You are SubsidySmart(TM), an AI subsidy advisor. Question: {q}"
        with st.spinner("AI is responding..."):
            resp = openai.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a professional subsidy advisor."},
                    {"role": "user", "content": prompt}
                ]
            )
        ans = resp['choices'][0]['message']['content']
        st.session_state.chat_history.append((q, ans))
    for q,a in reversed(st.session_state.chat_history):
        st.markdown(f"**You:** {q}")
        st.markdown(f"**AI:** {a}")
        st.markdown("---")

# --- ELIGIBILITY SELF-CHECK MODE ---
else:
    st.subheader("Eligibility Self-Check")
    recipient = st.text_input("Your Email:", value=st.session_state.user_email)
    age = st.radio("Company age?", ["< 3 years", ">= 3 years"])
    industry = st.multiselect("Industry?", ["AI","IoT","Biotech","Green Energy","Other"])
    rd = st.radio("R&D budget?", ["< $200K", ">= $200K"])
    exp = st.radio("Export?", ["No","Yes"])
    rev = st.radio("Revenue?", ["< $500K", ">= $500K"])
    emp = st.slider("Employees?", 1, 200, 10)
    docs = st.multiselect("Docs?", ["Business Plan","Org Chart","Budget","Export Plan","Pitch Deck"])
    if st.button("Calculate & Send Report"):
        # Score calculation
        s = 0
        s += 15 if age == ">= 3 years" else 0
        s += 20 if any(i in ["AI","IoT","Biotech","Green Energy"] for i in industry) else 0
        s += 20 if rd == ">= $200K" else 0
        s += 15 if exp == "Yes" else 0
        s += 10 if rev == ">= $500K" else 0
        s += 10 if 5 <= emp <= 100 else 0
        s += len(docs) * 2
        status = "Highly Eligible" if s >= 85 else ("Needs Review" if s >= 65 else "Not Eligible")
        # Display
        st.metric("Score", f"{s}%")
        st.markdown(f"**{status}**")
        # Append to Google Sheet with report details
        report_row = [
            datetime.now().isoformat(),
            st.session_state.user_name,
            st.session_state.user_email,
            st.session_state.company,
            s,
            status,
            recipient
        ]
        sheet.append_row(report_row)
        # Generate PDF
        pdf = FPDF(); pdf.add_page(); pdf.set_font("Arial", 12)
        pdf.cell(0, 10, safe_text("DeloitteSmart(TM) Subsidy Eligibility Report"), ln=1, align='C')
        pdf.ln(5)
        info = f"User:{st.session_state.user_name}\nCompany:{st.session_state.company}\nEmail:{recipient}\nScore:{s}% - {status}"
        pdf.multi_cell(0, 8, safe_text(info)); pdf.ln(5)
        details = (
            f"Age:{age}\nIndustry:{','.join(industry)}\nR&D:{rd}\nExport:{exp}\nRevenue:{rev}\nEmployees:{emp}\nDocs:{','.join(docs)}"
        )
        pdf.multi_cell(0, 8, safe_text(details))
        b = pdf.output(dest='S').encode('latin-1')
        fn = f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        st.download_button("Download Report", data=b, file_name=fn, mime='application/pdf')
        # Email
        if email_user and email_pass and recipient:
            yag = yagmail.SMTP(email_user, email_pass)
            yag.send(
                to=[recipient, "asif.baig@innov8.jp"],
                subject="Your DeloitteSmart(TM) Subsidy Report",
                contents=safe_text("Attached is your personalized report."),
                attachments={fn: b}
            )
            st.success("Email sent to client and Innov8.")

# --- END ---
# Dependencies: streamlit, openai, fpdf, yagmail, gspread, google-auth
# To run: streamlit run app.py
