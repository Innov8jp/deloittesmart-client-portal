import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

st.set_page_config(
    page_title="DeloitteSmart™ Client Portal",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("DeloitteSmart™ Client Assistant Portal")
st.markdown("Better insights. Faster funding. Powered by Deloitte AI.")

# Step 1: Ask a Question
st.header("Step 1: Ask a Question")
user_q = st.text_input("Ask your business subsidy question here:")
if user_q:
    st.success(f"🤖 AI: Thank you for your question. Based on available programs, here's a summary reply for: '{user_q}'")

# Step 2: Provide Business Information
st.header("Step 2: Provide Business Information")
col1, col2 = st.columns(2)

with col1:
    age = st.selectbox("Company Age:", ["< 3 years", "3-5 years", "5+ years"])
    industry = st.multiselect("Industry:", ["AI", "IoT", "Biotech", "Green Energy", "Other"])
    rd_spend = st.selectbox("R&D Budget (Annual):", ["< $200K", "$200K - $1M", "$1M+"])

with col2:
    revenue = st.slider("Annual Revenue ($)", 0, 2000000, 500000, step=50000)
    export = st.radio("Exporting or planning to export?", ["Yes", "No"])
    documents = st.file_uploader("Upload business documents (multiple allowed)", accept_multiple_files=True)

# Google Sheets Integration
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("gcp_credentials.json", scope)
client = gspread.authorize(creds)
sheet = client.open("DeloitteSmart Client Sessions").sheet1

# Step 3: View Results
st.header("Step 3: Eligibility Preview")
if st.button("Check Eligibility"):
    score = 0
    if age in ["3-5 years", "5+ years"]:
        score += 15
    if any(i in ["AI", "IoT", "Biotech", "Green Energy"] for i in industry):
        score += 20
    if rd_spend != "< $200K":
        score += 20
    if export == "Yes":
        score += 15
    if revenue >= 500000:
        score += 10
    if len(documents) >= 1:
        score += min(10, len(documents) * 2)

    st.metric("Eligibility Score", f"{score}%")
    if score >= 85:
        st.success("🟢 Highly Eligible")
    elif score >= 65:
        st.warning("🟡 Potentially Eligible")
    else:
        st.error("🔴 Low Eligibility")

    st.markdown("---")
    st.subheader("Recommended Next Step")
    st.markdown("- Schedule a call with a Deloitte Advisor\n- Review missing documents\n- Receive prefilled application draft (Phase 3)")

    # Log to Google Sheet
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    sheet.append_row([timestamp, user_q, age, ", ".join(industry), rd_spend, revenue, export, len(documents), score])

# Optional Save Option
st.markdown("---")
st.caption("Optional: Save your session and receive results by email. Coming soon.")
