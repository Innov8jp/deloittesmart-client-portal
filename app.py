# DeloitteSmart™ Client Portal — End-to-End Prototype with Safe PDF & Email Integration

import streamlit as st
import openai
from datetime import datetime
from fpdf import FPDF
import yagmail
import os

# --- CONFIG ---
st.set_page_config(
    page_title="DeloitteSmart™ Client Portal",
    page_icon=":moneybag:",
    layout="wide"
)

# --- HELPER: Sanitize text for Latin-1 PDF output ---
def safe_text(txt: str) -> str:
    # Replace problematic characters and drop non-Latin-1
    replacements = {
        '™': '(TM)',
        '–': '-',
        '≥': '>=',
        '✓': 'v',
        '✔': 'v',
    }
    for orig, repl in replacements.items():
        txt = txt.replace(orig, repl)
    return txt.encode('latin1', 'ignore').decode('latin1')

# --- SECRETS ---
openai.api_key = st.secrets.get("OPENAI_API_KEY", "")
email_user = st.secrets.get("EMAIL_USER", "")
email_pass = st.secrets.get("EMAIL_PASS", "")

# --- SIDEBAR ---
with st.sidebar:
    logo_path = "deloitte_logo.png"
    if os.path.exists(logo_path):
        st.image(logo_path, width=200)
    st.markdown("# DeloitteSmart™ Client Portal")
    st.markdown("Secure | Intelligent | Personalized")

# --- MAIN PAGE HEADER ---
st.title("Welcome to the DeloitteSmart™ AI Assistant")
st.caption("Get insights on your subsidy eligibility and receive tailored advice.")

# --- MODE TOGGLE ---
mode = st.radio("Choose Mode:", ["Client Chat", "Eligibility Self-Check"], index=0)

# --- CLIENT CHAT MODE ---
if mode == "Client Chat":
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    st.subheader("Ask a question about subsidy programs")
    user_question = st.text_input("Your question:", key="client_q")
    if st.button("Submit Question"):
        if not user_question:
            st.warning("Please type a question first.")
        else:
            prompt = ("You are SubsidySmart(TM), an AI trained to advise on government subsidy eligibility. "
                      "Answer based on: SME Expansion (5-100 employees, <$50M revenue), "
                      "R&D Innovation (>=3 yrs, >=$200K budget), Export Assistance (>= $500K sales). "
                      f"Question: {user_question}")
            with st.spinner("AI is responding..."):
                try:
                    response = openai.ChatCompletion.create(
                        model="gpt-3.5-turbo",
                        messages=[
                            {"role": "system", "content": "You are a professional government subsidy advisor."},
                            {"role": "user", "content": prompt}
                        ]
                    )
                    answer = response['choices'][0]['message']['content']
                except Exception as e:
                    answer = f"Error: {e}"
                st.session_state.chat_history.append((user_question, answer))

    for q, a in reversed(st.session_state.chat_history):
        st.markdown(f"**You:** {q}")
        st.markdown(f"**AI:** {a}")
        st.markdown("---")

# --- ELIGIBILITY SELF-CHECK MODE ---
else:
    st.subheader("Eligibility Self-Check Form")
    company_name = st.text_input("Company Name")
    recipient_email = st.text_input("Your Email (for report)")
    age = st.radio("Company age?", ["< 3 years", ">= 3 years"])
    industry = st.multiselect("Industry?", ["AI", "IoT", "Biotech", "Green Energy", "Other"])
    rd_budget = st.radio("R&D budget per year?", ["< $200K", ">= $200K"])
    export_ready = st.radio("Exporting or planning to export?", ["No", "Yes"])
    revenue = st.radio("Annual revenue?", ["< $500K", ">= $500K"])
    employees = st.slider("Number of employees?", 1, 200, 10)
    documents = st.multiselect(
        "Documents provided", ["Business Plan", "Org Chart", "Budget", "Export Plan", "Pitch Deck"]
    )

    if st.button("Calculate Score & Send Report"):
        # Calculate score
        score = 0
        if age == ">= 3 years": score += 15
        if any(i in ["AI","IoT","Biotech","Green Energy"] for i in industry): score += 20
        if rd_budget == ">= $200K": score += 20
        if export_ready == "Yes": score += 15
        if revenue == ">= $500K": score += 10
        if 5 <= employees <= 100: score += 10
        score += len(documents) * 2
        status = ("🟢 Highly Eligible" if score >= 85 else "🟡 Needs Review" if score >= 65 else "🔴 Not Eligible")

        # Display score
        st.metric("Eligibility Score", f"{score}%")
        st.markdown(f"**Result:** {status}")

        # Generate PDF report
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        pdf.cell(0, 10, safe_text("DeloitteSmart(TM) Subsidy Eligibility Report"), ln=1, align="C")
        pdf.ln(5)
        pdf.multi_cell(0, 8, safe_text(
            f"Company: {company_name}\nEmail: {recipient_email}\nDate: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
            f"Eligibility Score: {score}% - {status}"))
        pdf.ln(5)
        details = (
            f"Age: {age}\n"
            f"Industry: {', '.join(industry)}\n"
            f"R&D Budget: {rd_budget}\n"
            f"Export Ready: {export_ready}\n"
            f"Revenue: {revenue}\n"
            f"Employees: {employees}\n"
            f"Documents: {', '.join(documents)}"
        )
        pdf.multi_cell(0, 8, safe_text(details))

        # Prepare PDF bytes
        pdf_bytes = pdf.output(dest="S").encode("latin-1")
        report_filename = f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        st.download_button(
            "Download PDF Report",
            data=pdf_bytes,
            file_name=report_filename,
            mime="application/pdf"
        )

        # Send email via Gmail
        if email_user and email_pass and recipient_email:
            try:
                yag = yagmail.SMTP(email_user, email_pass)
                yag.send(
                    to=recipient_email,
                    subject="Your DeloitteSmart(TM) Subsidy Report",
                    contents=safe_text("Attached is your personalized subsidy eligibility report."),
                    attachments={report_filename: pdf_bytes}
                )
                st.success("📧 Report emailed successfully!")
            except Exception as e:
                st.error(f"Email failed: {e}")
        else:
            st.info("Email credentials or recipient missing; skipped email send.")

# --- END ---
# Run with: streamlit run app.py
