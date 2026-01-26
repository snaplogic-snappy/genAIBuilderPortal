import streamlit as st
import requests
import json

# -----------------------------
# CONFIGURATION
# -----------------------------
API_URL = "https://emea.snaplogic.com/api/1/rest/slsched/feed/ConnectFasterInc/projects/Tejasri%20Reddy%20Beeram/Diabetes_v4%20Task"
API_KEY = "HqGDBWRAfiuTp9ZD4Fn0iElfGizveHOX"

st.set_page_config(
    page_title="Content Intelligence for Field & Medical Teams",
    page_icon="💬",
    layout="centered"
)

# -----------------------------
# LIGHT THEME CSS (WHITE BACKGROUND)
# -----------------------------
st.markdown("""
<style>

/* Global background + text */
html, body, [data-testid="stAppViewContainer"] {
    background-color: #ffffff !important;   /* White */
    color: #000000 !important;              /* Black text */
}

/* Headings and normal text */
h1, h2, h3, h4, h5, h6, p, label, span {
    color: #000 !important;
}

/* Input container styling */
.stTextInput > div > div,
.stTextArea > div,
.stSelectbox > div,
.stRadio > div {
    background-color: #f8f9fa !important;  /* Light grey */
    border: 1px solid #ccc !important;
    border-radius: 10px !important;
}

/* Text inside inputs */
.stTextInput input {
    color: #000 !important;
}

/* TEXT AREA */
.stTextArea textarea {
    color: #000 !important;             
    background-color: #fff !important;  
    border-radius: 10px !important;
}

/* Placeholder styling */
.stTextInput input::placeholder,
.stTextArea textarea::placeholder {
    color: #777 !important;
}

/* Form container */
[data-testid="stForm"] {
    background-color: #f2f2f2 !important;
    padding: 20px !important;
    border-radius: 12px !important;
    border: 1px solid #ddd !important;
}

/* Primary button */
button[data-testid="baseButton-primary"] {
    background-color: #2563eb !important;
    color: white !important;
    border-radius: 8px !important;
    padding: 0.6em 1.2em !important;
    border: none !important;
    font-weight: 500 !important;
}

button[data-testid="baseButton-primary"]:hover {
    background-color: #1d4ed8 !important;
}

/* Info alert box */
.stAlert {
    background-color: #eef6ff !important;
    color: #000 !important;
    border-left: 4px solid #3b82f6 !important;
}

hr {
    border-color: #ccc !important;
}

</style>
""", unsafe_allow_html=True)

# -----------------------------
# HEADER
# -----------------------------
st.markdown(
    """
    <div style="text-align:center; margin-top:20px;">
        <img src="https://allot.123-web.uk/wp-content/uploads/2018/12/logo-2.png"
             alt="Allot Logo" width="260">
        <br><br>
        <a href="https://www.allotltd.com/"
            style="text-decoration:none; font-size:22px; color:#2563eb; font-weight:500;">
            www.allotltd.com
        </a>
    </div>
    <hr style="margin-top: 2em; opacity:0.3;">
    """,
    unsafe_allow_html=True
)

# -----------------------------
# PAGE TITLE
# -----------------------------
st.markdown("## 💬 **Content Intelligence for Field & Medical Teams**")
st.write("---")

# -----------------------------
# OVERVIEW
# -----------------------------
st.markdown(
    """
### 📘 Overview

Content Intelligence transforms raw scientific data into a strategic asset. Instead of relying on static slides, Field and Medical teams use AI-driven insights to deliver the right clinical evidence to the right Healthcare Professional (HCP) at the right moment. This application provides Content Intelligence and Next Best Actions (NBAs), offering a concise, evidence-based view of Type 2 diabetes management. It covers both established and emerging therapies—such as metformin and SGLT2 inhibitors—along with their clinical benefits, safety considerations, and patient guidance.

**Core benefits:**
* **Precision:** Tailor complex data to address specific HCP knowledge gaps.
* **Compliance:** Update and distribute approved materials globally, instantly.
* **Impact:** Use engagement analytics to identify which scientific narratives actually improve clinical understanding.

By bridging the gap between medical strategy and field execution, Content Intelligence ensures every interaction is evidence-based, personalized, and efficient.

### ⚠️ Data Limitations
This demo only reflects diabetes data of **Saudi Arabia diabetes market data**, and also with selected supporting data from **UK** and **USA** including:
- Sales data  
- HCP profiles  
- Call notes  
- Market summaries  
- Scientific publication data

Some more medical related data like 
- SGLT2 inhibitors
- Metformin

### 💡 Sample Questions

- *Market Access Specialist:*  
 What is the prescribing guidance of Type 2 diabetes mellitus as per NHS and how it's different from KSA guidelines? 
- *Medical Science Liaison (MSL):*  
 What industry guidance is followed for Type 2 diabetes mellitus in the USA and in KSA?
 """
)

st.write("---")

# -----------------------------
# INPUT FORM
# -----------------------------
with st.form("chat_form", clear_on_submit=False):

    st.subheader("Enquiry:")
    prompt = st.text_area("", placeholder="Type your question here...", height=110)

    st.subheader("Select role:")
    role = st.radio(
        "",
        [
            "Market Access Specialist",
            "Medical Science Liaison (MSL)"
        ],
        index=0
    )

    submitted = st.form_submit_button("Send")

# -----------------------------
# PROCESS SUBMISSION
# -----------------------------
if submitted and prompt.strip():

    with st.spinner(f"Fetching response for **{role}**..."):
        payload = [{"question_type": role, "prompt": prompt}]
        headers = {
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json"
        }

        try:
            response = requests.post(API_URL, headers=headers, data=json.dumps(payload))
            response.raise_for_status()
            data = response.json()

            if isinstance(data, list) and "Customer_Story" in data[0]:
                reply = data[0]["Customer_Story"]
            else:
                reply = f"Unexpected API response format: {data}"

        except Exception as e:
            reply = f"⚠️ Error: {e}"

    st.write("---")
    st.subheader("Response:")
    st.info(reply)

elif submitted and not prompt.strip():
    st.warning("Please enter a question before sending.")

# -----------------------------
# FOOTER
# -----------------------------
st.markdown(
    """
    <hr style="margin-top: 3em; opacity:0.3;">
    <p style="text-align:center; font-size: 0.9em; color: #777;">
        © 2026 Content_Intelligence for Field & Medical Teams | Powered by Allot Ltd
    </p>
    """,
    unsafe_allow_html=True
)