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
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

openai.api_key = st.secrets["OPENAI_API_KEY"]

# --- LOAD LOTTIE ---
def load_lottie_url(url):
    r = requests.get(url)
    if r.status_code != 200:
        return None
    return r.json()

lottie_ai = load_lottie_url("https://assets4.lottiefiles.com/packages/lf20_q5pk6p1k.json")

# --- UTILITY ---
def safe_text(txt: str) -> str:
    reps = {'™': '(TM)', '–': '-', '≥': '>=', '✓': 'v', '✔': 'v'}
    for k, v in reps.items():
        txt = txt.replace(k, v)
    return txt.encode('latin1', 'ignore').decode('latin1')

# --- SESSION DEFAULTS ---
for key in ["registered", "chat_history", "feedback_entries", "language"]:
    if key not in st.session_state:
        st.session_state[key] = False if key == "registered" else [] if "history" in key or "entries" in key else "English"

# --- LANGUAGE TOGGLE ---
st.session_state.language = st.sidebar.radio("🌐 Language / 言語", ["English", "日本語"], index=0)

# --- TRANSLATION ---
def t(en, jp):
    return jp if st.session_state.language == "日本語" else en

# --- REGISTRATION ---
if not st.session_state.registered:
    st.title("Welcome to DeloitteSmart™ Client Portal")
    st.subheader("Register to Get Started")

    name = st.text_input(t("Your Name (In-charge)", "担当者名"))
    company = st.text_input(t("Company Name", "会社名"))
    placeholder = (
        "e.g. 1-1-1 Marunouchi, Chiyoda-ku, Tokyo 100-0005"
        if st.session_state.language == "English"
        else "例: 〒100-0005 東京都千代田区丸の内1丁目1-1 パレスビル"
    )
    address = st.text_area(t("Company Address", "会社の住所"), placeholder=placeholder)
    email = st.text_input(t("Your Email (Optional)", "メールアドレス（任意）"))

    if st.button(t("Register and Continue", "登録して続行")):
        if not (name and company):
            st.error(t("Please fill in all required fields: Name and Company.", "担当者名と会社名を入力してください。"))
        else:
            st.session_state.registered = True
            st.session_state.user_name = name
            st.session_state.user_email = email
            st.session_state.company_name = company
            st.session_state.address = address
            st.success(t(f"Registered as {name} from {company}. Please proceed.", f"{company}の{name}として登録されました。"))
            st.stop()
    st.stop()

# --- SIDEBAR ---
with st.sidebar:
    st.markdown(f"### {st.session_state.user_name}")
    st.markdown(f"#### {st.session_state.company_name}")
    st.markdown("---")
    st.markdown("🔒 Secure | 🤖 Intelligent | 🎯 Personalized")

# --- MAIN APP ---
st.title(t("Hello", "こんにちは") + f" {st.session_state.user_name}, " + t("welcome back!", "おかえりなさい！"))
mode = st.radio("Mode:", [t("Chat with AI", "AIとチャット"), t("Eligibility Self-Check", "適格性の自己チェック")], index=0)

# --- CHAT MODE ---
if mode == t("Chat with AI", "AIとチャット"):
    st.subheader(t("Ask a question about subsidies", "補助金について質問する"))
    q = st.text_input(
        t("Your question:", "あなたの質問："),
        placeholder=t("e.g. What subsidies are available for AI startups?", "例：AIスタートアップ向けの補助金は？")
    )

    send_icon = st.button("🚀", key="send_btn")
    if send_icon and q:
        prompt = f"You are SubsidySmart™, an expert subsidy advisor. Question: {q}"
        with st.container():
            if lottie_ai:
                st_lottie(lottie_ai, height=180, key="ai-spinner")
            else:
                st.info("Preparing AI response...")

            try:
                resp = openai.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "You are a professional subsidy advisor."},
                        {"role": "user", "content": prompt}
                    ]
                )
                answer = resp.choices[0].message.content or t(
                    "I'm unable to answer that question at the moment. Please try again.",
                    "現在その質問には回答できません。もう一度お試しください。"
                )
            except Exception:
                answer = t(
                    "I'm unable to answer that question at the moment. Please try again.",
                    "現在その質問には回答できません。もう一度お試しください。"
                )

            st.session_state.chat_history.append((q, answer))

    for idx, (qq, aa) in enumerate(reversed(st.session_state.chat_history)):
        st.markdown(f"**You:** {qq}")
        st.markdown(f"**AI:** {aa}")
        c1, c2 = st.columns([1, 1])
        if c1.button("👍", key=f"yes{idx}"):
            st.session_state.feedback_entries.append({"helpful": True, "timestamp": datetime.now().isoformat()})
        if c2.button("👎", key=f"no{idx}"):
            st.session_state.feedback_entries.append({"helpful": False, "timestamp": datetime.now().isoformat()})
        st.markdown("---")

# --- END ---
