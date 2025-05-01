# DeloitteSmart™ Client Portal Setup — End-to-End Workflow Platform

# STEP 1: Install Required Libraries
# requirements.txt
streamlit
openai
fpdf

# STEP 2: Create main app.py with chatbot, scoring, and PDF report

# app.py
import streamlit as st
import openai
from datetime import datetime
from fpdf import FPDF

st.set_page_config(page_title="DeloitteSmart™ Portal", page_icon=":moneybag:", layout="wide")

# Sidebar
with st.sidebar:
    st.image("deloitte_logo.png", width=200)
    openai_api_key = st.secrets["OPENAI_API_KEY"]
    st.markdown("DeloitteSmart™ Client Portal")
    st.markdown("Secure | Intelligent | Personalized")

st.title("Welcome to the DeloitteSmart™ AI Assistant")
st.caption("Get insights on your subsidy eligibility and receive tailored advice.")

mode = st.radio("Choose Mode:", ["Client Chatbot", "Scoring Self-Check"])

# Chat History
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if mode == "Client Chatbot":
    user_question = st.text_input("Ask a question about subsidy programs")
    if st.button("Submit Question"):
        if user_question:
            openai.api_key = openai_api_key
            prompt = f"""
            You are SubsidySmart™, an AI assistant trained to guide clients on subsidy program eligibility.
            Answer clearly based only on:
            1. SME Expansion (5-100 employees, <$50M revenue)
            2. R&D Innovation (AI, Biotech, ≥3 yrs, ≥$200K budget)
            3. Export Assistance ($500K+ domestic sales)

            Question: {user_question}
            """
            with st.spinner("AI is responding..."):
                response = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "You are a professional and concise government subsidy advisor."},
                        {"role": "user", "content": prompt}
                    ]
                )
                reply = response['choices'][0]['message']['content']
                st.session_state.chat_history.append((user_question, reply))
        else:
            st.warning("Please type a question first.")

    for q, a in reversed(st.session_state.chat_history):
        st.markdown(f"**You:** {q}")
        st.markdown(f"**AI:** {a}")
        st.markdown("---")

elif mode == "Scoring Self-Check":
    st.subheader("Eligibility Self-Check Form")
    company_name = st.text_input("Company Name")
    email = st.text_input("Your Email")
    age = st.radio("Company age?", ["< 3 years", "≥ 3 years"])
    industry = st.multiselect("Industry?", ["AI", "IoT", "Biotech", "Green Energy", "Other"])
    rd_budget = st.radio("R&D budget per year?", ["< $200K", "≥ $200K"])
    export_ready = st.radio("Exporting or planning to export?", ["No", "Yes"])
    revenue = st.radio("Annual revenue?", ["< $500K", "≥ $500K"])
    employees = st.slider("Number of employees?", 1, 200, 10)
    documents = st.multiselect("Documents provided", ["Business Plan", "Org Chart", "Budget", "Export Plan", "Pitch Deck"])

    if st.button("Calculate Score and Generate Report"):
        score = 0
        if age == "≥ 3 years": score += 15
        if any(i in ["AI", "IoT", "Biotech", "Green Energy"] for i in industry): score += 20
        if rd_budget == "≥ $200K": score += 20
        if export_ready == "Yes": score += 15
        if revenue == "≥ $500K": score += 10
        if 5 <= employees <= 100: score += 10
        score += len(documents) * 2

        status = "🟢 Highly Eligible" if score >= 85 else "🟡 Needs Review" if score >= 65 else "🔴 Not Eligible"

        st.metric("Eligibility Score", f"{score}%")
        st.markdown(f"**Result:** {status}")

        st.markdown("### Generating PDF Report...")
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        pdf.cell(200, 10, txt="DeloitteSmart™ Subsidy Eligibility Report", ln=1, align='C')
        pdf.cell(200, 10, txt=f"Company: {company_name}", ln=2)
        pdf.cell(200, 10, txt=f"Email: {email}", ln=3)
        pdf.cell(200, 10, txt=f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}", ln=4)
        pdf.ln(10)

        pdf.multi_cell(0, 10, f"Eligibility Score: {score}%\nStatus: {status}")
        pdf.ln()

        pdf.multi_cell(0, 10, "Answers:\n" + \
            f"Age: {age}\nIndustry: {', '.join(industry)}\nR&D Budget: {rd_budget}\n" + \
            f"Export Ready: {export_ready}\nRevenue: {revenue}\nEmployees: {employees}\n" + \
            f"Documents: {', '.join(documents)}")

        output_path = f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        pdf.output(output_path)
        with open(output_path, "rb") as file:
            st.download_button("Download PDF Report", data=file, file_name=output_path)

# STEP 3: Optional: configure .streamlit/config.toml
# [theme]
# base="light"

# STEP 4: Set Streamlit Secrets (OPENAI_API_KEY)
# Go to Streamlit Cloud → Settings → Secrets
# OPENAI_API_KEY = "sk-..."

# STEP 5: Deploy on https://streamlit.io/cloud
# Upload this to GitHub, connect, and set main file = app.py
