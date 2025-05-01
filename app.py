# DeloitteSmart™ Client Portal — End-to-End Prototype

# STEP 1: Install Required Libraries
# Add to requirements.txt:
# streamlit
# openai
# fpdf

# STEP 2: Create app.py with hardcoded API key, chat, scoring, and PDF export

import streamlit as st
import openai
from datetime import datetime
from fpdf import FPDF

# --- CONFIG ---
st.set_page_config(
    page_title="DeloitteSmart™ Client Portal",
    page_icon=":moneybag:",
    layout="wide"
)

# --- HARD-CODED API KEY ---
openai.api_key = "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"

# --- SIDEBAR ---
with st.sidebar:
    st.image("deloitte_logo.png", width=200)
    st.markdown("# DeloitteSmart™ Client Portal")
    st.markdown("Secure | Intelligent | Personalized")

# --- MAIN PAGE ---
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
            prompt = f"""
You are SubsidySmart™, an AI trained to advise on government subsidy eligibility.
Answer clearly based on these programs:
1. SME Expansion: 5–100 employees, <$50M revenue
2. R&D Innovation: ≥3 years, ≥$200K budget in AI/IoT/Biotech/Green Energy
3. Export Assistance: ≥$500K domestic sales

Question: {user_question}
"""
            with st.spinner("AI is responding..."):
                response = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "You are a professional government subsidy advisor."},
                        {"role": "user", "content": prompt}
                    ]
                )
                answer = response['choices'][0]['message']['content']
                st.session_state.chat_history.append((user_question, answer))

    # Display chat history
    for q, a in reversed(st.session_state.chat_history):
        st.markdown(f"**You:** {q}")
        st.markdown(f"**AI:** {a}")
        st.markdown("---")

# --- ELIGIBILITY SELF-CHECK MODE ---
else:
    st.subheader("Eligibility Self-Check Form")
    company_name = st.text_input("Company Name")
    email = st.text_input("Your Email (for report)")
    age = st.radio("Company age?", ["< 3 years", "≥ 3 years"])
    industry = st.multiselect("Industry?", ["AI", "IoT", "Biotech", "Green Energy", "Other"])
    rd_budget = st.radio("R&D budget per year?", ["< $200K", "≥ $200K"])
    export_ready = st.radio("Exporting or planning to export?", ["No", "Yes"])
    revenue = st.radio("Annual revenue?", ["< $500K", "≥ $500K"])
    employees = st.slider("Number of employees?", 1, 200, 10)
    documents = st.multiselect(
        "Documents provided", ["Business Plan", "Org Chart", "Budget", "Export Plan", "Pitch Deck"]
    )

    if st.button("Calculate Score & Download Report"):
        # Calculate score
        score = 0
        if age == "≥ 3 years":
            score += 15
        if any(i in ["AI", "IoT", "Biotech", "Green Energy"] for i in industry):
            score += 20
        if rd_budget == "≥ $200K":
            score += 20
        if export_ready == "Yes":
            score += 15
        if revenue == "≥ $500K":
            score += 10
        if 5 <= employees <= 100:
            score += 10
        score += len(documents) * 2
        status = ("🟢 Highly Eligible" if score >= 85 else
                  "🟡 Needs Review" if score >= 65 else
                  "🔴 Not Eligible")

        # Display score
        st.metric("Eligibility Score", f"{score}%")
        st.markdown(f"**Result:** {status}")

        # Generate PDF report
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        pdf.cell(0, 10, txt="DeloitteSmart™ Subsidy Eligibility Report", ln=1, align='C')
        pdf.ln(5)
        pdf.cell(0, 8, txt=f"Company: {company_name}", ln=1)
        pdf.cell(0, 8, txt=f"Email: {email}", ln=1)
        pdf.cell(0, 8, txt=f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}", ln=1)
        pdf.ln(5)
        pdf.multi_cell(0, 8, txt=f"Eligibility Score: {score}% - {status}")
        pdf.ln(5)
        pdf.multi_cell(0, 8, txt=(
            f"Age: {age}\n"
            f"Industry: {', '.join(industry)}\n"
            f"R&D Budget: {rd_budget}\n"
            f"Export Ready: {export_ready}\n"
            f"Revenue: {revenue}\n"
            f"Employees: {employees}\n"
            f"Documents: {', '.join(documents)}"
        ))

        # Provide download
        pdf_bytes = pdf.output(dest='S').encode('latin-1')
        report_filename = f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        st.download_button(
            "Download PDF Report",
            data=pdf_bytes,
            file_name=report_filename,
            mime='application/pdf'
        )

# --- END ---
# Run with: streamlit run app.py
