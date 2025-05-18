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

    send_clicked = st.button(t("Send", "送信"), key="send_btn")
    if send_clicked and q:
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

# --- ELIGIBILITY SELF-CHECK ---
else:
    st.subheader(t("Eligibility Self-Check", "適格性の自己チェック"))
    recipient = st.text_input(t("Email (Optional):", "メール（任意）："), value=st.session_state.user_email)
    age = st.radio(t("Company age:", "会社設立年数："), ["<3 years", "≥3 years"])
    industry = st.multiselect(t("Industry", "業種"), ["AI", "IoT", "Biotech", "Green Energy", "Other"])
    rd = st.radio(t("R&D Budget:", "研究開発予算："), ["<200K", "≥200K"])
    exp = st.radio(t("Export involvement:", "輸出の関与："), ["No", "Yes"])
    rev = st.radio(t("Annual Revenue:", "年間収益："), ["<500K", "≥500K"])
    emp = st.slider(t("Number of Employees", "従業員数"), 1, 200, 10)
    docs = st.multiselect(
        t("Documents you have", "お持ちの書類"),
        [
            "Business Plan / 事業計画書",
            "Org Chart / 組織図",
            "Budget / 予算書",
            "Export Plan / 輸出計画書",
            "Pitch Deck / ピッチ資料",
            "Trial Balance / 残高計算表",
            "Tax Return / 税務申告書",
            "Tohon / 登記簿謄本"
        ]
    )

    if st.button(t("Calculate & Download Report", "計算してレポートをダウンロード")):
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
        st.download_button(t("Download PDF Report", "PDFレポートをダウンロード"), data=data, file_name=fname, mime="application/pdf")

# --- END ---
