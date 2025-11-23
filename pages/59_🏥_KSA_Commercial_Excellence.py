import streamlit as st
import requests
import json

# -----------------------------
# CONFIGURATION
# -----------------------------
API_URL = "https://emea.snaplogic.com/api/1/rest/slsched/feed/ConnectFasterInc/projects/Tejasri%20Reddy%20Beeram/Diabetes_tejasri%20Task"
API_KEY = "1CQHpI3oOHloqEWhh1Exwp0AToE7qqJF"

st.set_page_config(page_title="KSA Commercial Excellence", page_icon="💬", layout="centered")

# -----------------------------
# HEADER WITH LOGO + LINK
# -----------------------------
st.markdown(
    """
    <div style="text-align:center; margin-top:20px;">
        <img src="https://allot.123-web.uk/wp-content/uploads/2018/12/logo-2.png" 
             alt="Allot Logo" width="260">
        <br><br>
        <a href="https://www.allotltd.com/" 
            style="text-decoration:none; font-size:22px; color:#1a4dab; font-weight:500;">
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
st.markdown("## 💬 **Kingdom of Saudi Arabia Commercial Excellence**")
st.write("---")

st.markdown(
    """

**Overview:**

This application offers the ‘next best action’ for commercial, sales, market access, and medical pharmaceutical field teams. It focuses on the diabetes market in the Kingdom of Saudi Arabia. Analysis of client internal sales, CRM call notes, medical data, together with external in-market policy, healthcare data, recent medical publications, and future health conferences are governed by client-specific business rules that control the output. It is envisaged that the solution runs in internal client environments and no data ‘leaves the building’.


**Data Limitations:**

The scope of this application is limited to data sourced from the Kingdom of Saudi Arabia, including diabetes sales data, HCP information, call notes, next-best-action insights, market overviews, and clinical publication data.

**Sample Questions:**

1. Sales Representative: Analyze the uploaded 'call notes 2.xls' data, specifically focusing on the recent interactions, prescribing data, and specialty of each Healthcare Professional (HCP) in the Saudi Arabian territory. Generate the 'Next Best Action' (NBA) for each assigned Sales Representative, prioritizing high-potential prescribers of [Product Name: Empagliflozin].
2. Market Access Specialist: Leveraging our proprietary and syndicated data sources (e.g., patient claims data, EMR/EHR insights, payer formulary status, internal CRM activity, and stakeholder engagement metrics) for the Saudi Arabian diabetes market, generate the specific, prioritized 'Next Best Action' (NBA) for each assigned Pharma Market Access Specialist this week. The NBA must be tailored to achieve our primary objective of securing or expanding market access for Semaglutide  within the Kingdom.
3. Medical Science Liasion(MSL): Analyze the uploaded 'call notes 2.xls' for any MSL follow-up requests or complex clinical questions flagged by the Sales Team, or for any KOLs requesting specific data. Generate the 'Next Best Action' (NBA) for each assigned MSL, prioritizing engagements that address complex topics beyond the sales representative’s scope.

    """
)
st.write("---")

# -----------------------------
# INPUT FORM
# -----------------------------
with st.form("chat_form", clear_on_submit=False):

    st.subheader("Commercial enquiry:")
    prompt = st.text_area("", placeholder="Type your question here...", height=100)

    st.subheader("Select role:")
    role = st.radio(
        "",
        [
            "Sales Representative",
            "Market Access Specialist",
            "Medical Science Liaison (MSL)",
            "Marketing Expert"
        ],
        index=0
    )

    submitted = st.form_submit_button("Send")

# -----------------------------
# HANDLE SUBMISSION
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
    <hr style="margin-top: 3em; opacity: 0.3;">
    <p style="text-align:center; font-size: 0.9em; color: #777;">
        © 2025 KSA Commercial Excellence | Powered by Allot Ltd
    </p>
    """,
    unsafe_allow_html=True
)
