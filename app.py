import streamlit as st
import openai
from datetime import datetime
from fpdf import FPDF
import re
from streamlit_lottie import st_lottie
import requests

# --- CONFIGURATION ---
st.set_page_config(
    page_title="DeloitteSmart™ Client Portal",
    page_icon=":moneybag:",
    layout="wide",
    initial_sidebar_state="expanded"
)

openai.api_key = st.secrets["OPENAI_API_KEY"]

# --- LOAD LOTTIE ANIMATION ---
def load_lottie_url(url):
    r = requests.get(url)
    if r.status_code != 200:
        return None
    return r.json()

lottie_ai = load_lottie_url("https://assets10.lottiefiles.com/packages/lf20_touohxv0.json")

# --- PDF CLEANING ---
def safe_text(txt: str) -> str:
    reps = {'™': '(TM)', '–': '-', '≥': '>=', '✓': 'v', '✔': 'v'}
    for k, v in reps.items():
        txt = txt.replace(k, v)
    return txt.encode('latin1', 'ignore').decode('latin1')

# --- SESSION DEFAULTS ---
if "registered" not in st.session_state:
    st.session_state.registered = False
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "feedback_entries" not in st.session_state:
    st.session_state.feedback_entries = []

# --- REGISTRATION ---
if not st.session_state.registered:
    st.title("Welcome to DeloitteSmart™ Client Portal")
    st.subheader("Register to Get Started")
    name = st.text_input("Your Name (In-charge)", key="name")
    company = st.text_input("Company Name", key="company")
    address = st.text_area("Company Address (Japanese Format)", placeholder="〒100-0005 東京都千代田区丸の内1丁目1-1 パレスビル")
    email = st.text_input("Your Email (Optional)", key="email")

    if st.button("Register and Continue"):
        if not (name and company):
            st.error("Please fill in all required fields: Name and Company.")
        else:
            st.session_state.registered = True
            st.session_state.user_name = name
            st.session_state.user_email = email
            st.session_state.company_name = company
            st.session_state.address = address
            st.success(f"Registered as {name} from {company}. Please proceed.")
            st.stop()
    st.stop()

# --- SIDEBAR ---
with st.sidebar:
    st.markdown(f"### {st.session_state.user_name}")
    st.markdown(f"#### {st.session_state.company_name}")
    st.markdown("---")
    st.markdown("Secure | Intelligent | Personalized")

# --- MAIN APP ---
st.title(f"Hello {st.session_state.user_name}, welcome back!")
mode = st.radio("Mode:", ["Chat with AI", "Eligibility Self-Check"], index=0)

if mode == "Chat with AI":
    st.subheader("Ask a question about subsidies")
    q = st.text_input("Your question:")

    if st.button("Send") and q:
        prompt = f"You are SubsidySmart™, an expert subsidy advisor. Question: {q}"
        with st.spinner("🤖 Thinking like an AI consultant..."):
            st_lottie(lottie_ai, height=200)
            try:
                resp = openai.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "You are a professional subsidy advisor."},
                        {"role": "user", "content": prompt}
                    ]
                )
                answer = resp.choices[0].message.content
                st.session_state.chat_history.append((q, answer))
            except Exception as e:
                st.error(f"Error: {e}")

    for idx, (qq, aa) in enumerate(reversed(st.session_state.chat_history)):
        st.markdown(f"**You:** {qq}")
        st.markdown(f"**AI:** {aa}")
        c1, c2 = st.columns([1, 1])
        if c1.button("👍", key=f"yes{idx}"):
            st.session_state.feedback_entries.append({"helpful": True, "timestamp": datetime.now().isoformat()})
        if c2.button("👎", key=f"no{idx}"):
            st.session_state.feedback_entries.append({"helpful": False, "timestamp": datetime.now().isoformat()})
        st.markdown("---")

else:
    st.subheader("Eligibility Self-Check & Report")
    recipient = st.text_input("Your Email:", value=st.session_state.user_email)
    age = st.radio("Company age?", ["<3 years", "≥3 years"])
    industry = st.multiselect("Industry", ["AI", "IoT", "Biotech", "Green Energy", "Other"])
    rd = st.radio("R&D Budget?", ["<200K", "≥200K"])
    exp = st.radio("Export involvement?", ["No", "Yes"])
    rev = st.radio("Annual Revenue?", ["<500K", "≥500K"])
    emp = st.slider("Number of Employees", 1, 200, 10)
    docs = st.multiselect(
        "Documents you have / お持ちの書類",
        [
            "Business Plan / 事業計画書",
            "Org Chart / 組織図",
            "Budget / 予算書",
            "Export Plan / 輸出計画書",
            "Pitch Deck / ピッチ資料",
            "Trial Balance / 残高計算表",
            "Tax Return / 税務申告書",
            "Tohon / 登記簿謝本"
        ]
    )

    if st.button("Calculate & Download Report"):
        score = 0
        score += 15 if age == "≥3 years" else 0
        score += 20 if any(i in industry for i in ["AI", "IoT", "Biotech", "Green Energy"]) else 0
        score += 20 if rd == "≥200K" else 0
        score += 15 if exp == "Yes" else 0
        score += 10 if rev == "≥500K" else 0
        score += 10 if 5 <= emp <= 100 else 0
        score += len(docs) * 2

        status = "🟢 Highly Eligible" if score >= 85 else ("🟡 Needs Review" if score >= 65 else "🔴 Not Eligible")

        st.metric("Eligibility Score", f"{score}%")
        st.markdown(f"**{status}**")

        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        pdf.cell(0, 10, safe_text("DeloitteSmart™ Subsidy Report"), ln=1, align='C')
        pdf.ln(5)
        info = (
            f"Name: {st.session_state.user_name}\n"
            f"Company: {st.session_state.company_name}\n"
            f"Address: {st.session_state.address}\n"
            f"Email: {recipient}\n"
            f"Score: {score}% - {status}"
        )
        pdf.multi_cell(0, 8, safe_text(info))
        pdf.ln(5)
        details = (
            f"Age: {age}\n"
            f"Industry: {', '.join(industry)}\n"
            f"R&D Budget: {rd}\n"
            f"Export: {exp}\n"
            f"Revenue: {rev}\n"
            f"Employees: {emp}\n"
            f"Documents: {', '.join(docs)}"
        )
        pdf.multi_cell(0, 8, safe_text(details))

        data = pdf.output(dest="S").encode("latin-1")
        fname = f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        st.download_button("Download PDF Report", data=data, file_name=fname, mime="application/pdf")

# --- END OF DeloitteSmart™ CLIENT PORTAL CODE ---
