import streamlit as st
import requests
import json

# -----------------------------
# CONFIGURATION
# -----------------------------
API_URL = "https://emea.snaplogic.com/api/1/rest/slsched/feed/ConnectFasterInc/projects/Tejasri%20Reddy%20Beeram/Oncology%20Task"
API_KEY = st.secrets.get("API_KEY", "TfPcaLIqmQtm6rWSegetxXVYulQf8WY0")

st.set_page_config(
    page_title="NBA for Oncology in England",
    page_icon="💬",
    layout="centered"
)

# -----------------------------
# SESSION STATE
# -----------------------------
if "prompt" not in st.session_state:
    st.session_state.prompt = ""

if "role" not in st.session_state:
    st.session_state.role = "Key Account Manager"

# -----------------------------
# MODERN UI CSS
# -----------------------------
st.markdown("""
<style>
html, body, [data-testid="stAppViewContainer"] {
    background: linear-gradient(180deg, #f9fafb 0%, #ffffff 100%);
    color: #111827;
    font-family: 'Inter', sans-serif;
}

.block-container {
    max-width: 700px;
    padding-top: 2rem;
    padding-bottom: 2rem;
}

.quick-title {
    font-size: 28px;
    font-weight: 700;
    margin-bottom: 10px;
}

.quick-sub {
    color: #000000;
    font-size: 18px;
    font-weight: 700;
    margin-bottom: 8px;
}

.quick-card button {
    width: 100%;
    border-radius: 12px;
    border: 1px solid #e5e7eb;
    padding: 14px;
    background: #f9fafb;
    font-weight: 600;
    text-align: left;
}

.quick-card button:hover {
    background: #eef2ff;
}

[data-testid="stForm"] {
    background: #ffffff;
    padding: 25px;
    border-radius: 16px;
    border: 1px solid #e5e7eb;
    box-shadow: 0 4px 20px rgba(0,0,0,0.05);
}

.stTextArea textarea {
    background-color: #ffffff !important;
    border-radius: 12px !important;
    border: 1px solid #d1d5db !important;
    padding: 12px !important;
    font-size: 15px !important;
}

button[data-testid="baseButton-primary"] {
    background: linear-gradient(90deg, #2563eb, #1d4ed8);
    color: white;
    border-radius: 10px;
    padding: 0.7em 1.4em;
    font-weight: 600;
    border: none;
}

button[data-testid="baseButton-primary"]:hover {
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(37,99,235,0.3);
}

footer {
    visibility: hidden;
}
</style>
""", unsafe_allow_html=True)

# -----------------------------
# HEADER
# -----------------------------
st.markdown("""
<div style="text-align:center; margin-top:20px;">
    <img src="https://allot.123-web.uk/wp-content/uploads/2018/12/logo-2.png" width="240">
    <br><br>
    <a href="https://www.allotltd.com/"
        style="text-decoration:none; font-size:20px; color:#2563eb;">
        www.allotltd.com
    </a>
</div>
<hr style="margin-top: 2em; opacity:0.3;">
""", unsafe_allow_html=True)

# -----------------------------
# HERO
# -----------------------------
st.markdown("""
<div style="
    text-align:center;
    padding:30px 20px;
    background: linear-gradient(90deg, #2563eb, #1e40af);
    border-radius:16px;
    color:white;
    margin-bottom:20px;
">
    <h1>💬 NBA for Oncology</h1>
    <p>Next Best Actions for Healthcare</p>
</div>
""", unsafe_allow_html=True)

# -----------------------------
# OVERVIEW (VISIBLE)
# -----------------------------
st.markdown("### 📘 Overview")

st.markdown("""
This application delivers Next Best Actions (NBAs) to support pharmaceutical commercial, sales, market access, and medical field teams. It is tailored to the lung cancer oncology landscape in England, providing actionable recommendations that help teams prioritise engagement and strategic initiatives.

The insights are generated through the integration of healthcare and market data, combined with clinical guidance from organisations such as the National Institute for Health and Care Excellence (NICE). All recommendations are governed by predefined business rules to ensure consistency, relevance, and compliance.
""")

# -----------------------------
# DATA SCOPE (EXPANDER)
# -----------------------------
with st.expander("🎯 Data Scope"):
    st.markdown("""
The analysis is based on oncology data in England, specifically focused on lung cancer, and includes the following sources:
- Call Notes Data – Internal
- Sales Data – Internal
- Call Activity Data – Internal
- HCO & HCP Data – NHS sources
- Healthcare System Assessment Data – Internal and external
- NICE Guidelines – External
- Treatment Pathways – Derived from NICE guidelines
- Formulary Data – Oxfordshire, Northeast London, and NHS England
""")

# -----------------------------
# SAMPLE QUESTIONS (EXPANDER)
# -----------------------------
with st.expander("💡 Sample Questions"):

    st.markdown('<div class="quick-title">💡 Sample Questions</div>', unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        st.markdown('<div class="quick-sub">Key Account Manager</div>', unsafe_allow_html=True)
        if st.button("📈 Top-performing accounts"):
            st.session_state.prompt = "What are the top-performing accounts and what behaviours are driving success?"
            st.session_state.role = "Key Account Manager"

        if st.button("🧬 High patient potential"):
            st.session_state.prompt = "Which HCPs or HCOs show high patient potential but low engagement based on call activity and sales data?"
            st.session_state.role = "Key Account Manager"

        st.markdown('<div class="quick-sub">Medical Science Liaison (MSL)</div>', unsafe_allow_html=True)
        if st.button("🤝❌ Low engagement HCPs"):
            st.session_state.prompt = "Which HCPs show high patient potential but low engagement?"
            st.session_state.role = "Medical Science Liaison (MSL)"

        if st.button("🚀 vs 🐢 Treatment Pathways"):
            st.session_state.prompt = "Which centres are early adopters vs laggards in new treatment pathways?"
            st.session_state.role = "Medical Science Liaison (MSL)"

    with col2:
        st.markdown('<div class="quick-sub">Market Access Representative</div>', unsafe_allow_html=True)
        if st.button("📋 Formulary uptake issues"):
            st.session_state.prompt = "Which regions show delayed formulary uptake despite NICE guidance?"
            st.session_state.role = "Market Access Representative"

        if st.button("🏥 Formulary comparison"):
            st.session_state.prompt = "How do formulary inclusions in Oxfordshire vs Northeast London vs NHS England differ in terms of uptake?"
            st.session_state.role = "Market Access Representative"

        st.markdown('<div class="quick-sub">Commercial Director</div>', unsafe_allow_html=True)
        if st.button("📘 NICE alignment"):
            st.session_state.prompt = "Which HCPs show low alignment with NICE guidelines?"
            st.session_state.role = "Commercial Director"

        if st.button("🧪 Adopters vs Laggards"):
            st.session_state.prompt = "Which centres are early adopters vs laggards in new treatment pathways?"
            st.session_state.role = "Commercial Director"

# -----------------------------
# INPUT FORM
# -----------------------------
with st.form("chat_form", clear_on_submit=False):

    st.subheader("💬 Ask a question")

    prompt = st.text_area(
        "",
        value=st.session_state.prompt,
        placeholder="Type your question here...",
        height=120
    )

    st.subheader("👤 Select your role")

    roles = [
        "Key Account Manager",
        "Market Access Representative",
        "Medical Science Liaison (MSL)",
        "Commercial Director"
    ]

    role_index = roles.index(st.session_state.role) if st.session_state.role in roles else 0
    role = st.radio("", roles, index=role_index)

    submitted = st.form_submit_button("🚀 Get Insight")

# -----------------------------
# API CALL
# -----------------------------
if submitted:

    if not prompt.strip():
        st.warning("Please enter a question before sending.")
    else:
        with st.spinner("🔍 Analysing oncology data..."):

            payload = [{"question_type": role, "prompt": prompt}]
            headers = {
                "Authorization": f"Bearer {API_KEY}",
                "Content-Type": "application/json"
            }

            try:
                response = requests.post(
                    API_URL,
                    headers=headers,
                    json=payload,
                    timeout=30
                )
                response.raise_for_status()

                try:
                    data = response.json()
                except Exception:
                    data = {}

                if isinstance(data, list) and len(data) > 0:
                    reply = data[0].get("Customer_Story", "No insight returned.")
                else:
                    reply = f"Unexpected API response format: {data}"

            except requests.exceptions.Timeout:
                reply = "⚠️ Request timed out. Please try again."
            except requests.exceptions.RequestException as e:
                reply = f"⚠️ API Error: {str(e)}"
            except Exception as e:
                reply = f"⚠️ Unexpected Error: {str(e)}"

        st.markdown("### 💡 Insight")

        st.markdown(f"""
        <div style="
            background:#ffffff;
            padding:20px;
            border-radius:14px;
            border:1px solid #e5e7eb;
            box-shadow:0 4px 12px rgba(0,0,0,0.04);
            margin-top:10px;
        ">
            <p style="line-height:1.6;">
                {reply}
            </p>
        </div>
        """, unsafe_allow_html=True)

# -----------------------------
# FOOTER
# -----------------------------
st.markdown("""
<hr style="margin-top: 3em; opacity:0.2;">
<p style="text-align:center; font-size: 0.85em; color: #9ca3af;">
© 2026 NBA Oncology | Powered by Allot Ltd
</p>
""", unsafe_allow_html=True)
