# ai_data_analytics_insights_summit_live.py
# Lead capture + SnapLogic AI Agent integration

import streamlit as st
import requests
import uuid
import re
from datetime import datetime

# ===================================
# PAGE CONFIGURATION
# ===================================
st.set_page_config(
    page_title="AI Data, Analytics & Insights Summit — Lead Capture",
    page_icon="🎫",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ===================================
# STYLING
# ===================================
st.markdown("""
<style>
.block-container { padding-top: 2rem; max-width: 700px; margin: auto; }
textarea::placeholder { color:#9ca3af; opacity: 1; }
.footer { text-align:center; color:#6b7280; font-size:0.85rem; margin-top:2rem; }
</style>
""", unsafe_allow_html=True)

# ===================================
# LIVE CONFIG (YOUR ENDPOINT)
# ===================================
API_URL = "https://emea.snaplogic.com/api/1/rest/slsched/feed/ConnectFasterInc/Konstantin/Events/2025_AI_Summit_Munich_AgentDriver_Task"
AUTH_TOKEN = "Bearer fvBUW1Du9KHQ2dHOv7XSkfcJyCJXH5JO"   # ⚠️ Move to secrets before deploying!

EMAIL_REGEX = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"


def valid_email(addr: str) -> bool:
    return bool(re.match(EMAIL_REGEX, addr or ""))


# ===================================
# HEADER
# ===================================
st.title("🎯 AI Data, Analytics & Insights Summit DACH")
st.subheader("Smart Lead Capture powered by SnapLogic")

st.markdown("""
Welcome to the **AI Data, Analytics & Insights Summit DACH**!

Please share your contact details below.  
Our **SnapLogic AI Agent** will:
- Analyze your organization's public digital footprint  
- Understand your challenges  
- Generate a **tailored follow-up email**  
- Notify the booth team with your details  
""")

st.divider()

# ===================================
# FORM
# ===================================
with st.form("summit_form", clear_on_submit=False, border=True):

    name = st.text_input("Full Name *", placeholder="e.g., Alex Johnson")
    email = st.text_input("Work Email *", placeholder="e.g., alex.johnson@company.com")
    role = st.text_input("Role / Title *", placeholder="e.g., Head of Data Strategy")
    company = st.text_input("Company *", placeholder="e.g., Contoso GmbH")

    notes = st.text_area(
        "Notes (optional, but extremely valuable)",
        placeholder=(
            "Why do you visit the AI, DATA ANALYTICS AND INSIGHTS SUMMIT DACH?\n"
            "What is challenging in your daily work?\n"
            "How would an ideal solution look like for you?"
        ),
        height=160
    )

    st.markdown("Fields marked with * are required.")

    submitted = st.form_submit_button(
        "Submit → Send to SnapLogic AI Agent",
        disabled=False
    )

# ===================================
# FORM PROCESSING
# ===================================
if submitted:
    errors = []

    if not name:
        errors.append("Please provide your full name.")
    if not email or not valid_email(email):
        errors.append("Please provide a valid work email address.")
    if not role:
        errors.append("Please provide your role/title.")
    if not company:
        errors.append("Please provide your company.")

    if errors:
        for e in errors:
            st.error(e)
    else:
        # Build the Bedrock-style messages array directly here
        lead_text = (
            "New AI Summit booth lead:\n"
            f"Name: {name}\n"
            f"Email: {email}\n"
            f"Role: {role}\n"
            f"Company: {company}\n\n"
            "Notes:\n"
            f"{notes or 'n/a'}"
        )

        payload = {
            "session_id": str(uuid.uuid4()),
            "timestamp": datetime.utcnow().isoformat(),
            "source": "AI Summit DACH 2025 booth",
            "lead": {
                "name": name,
                "email": email,
                "role": role,
                "company": company,
                "notes": notes,
            },
            # 👇 Converse-style messages: NO "type": "input_text"
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "text": lead_text
                        }
                    ],
                }
            ],
        }

        try:
            headers = {
                "Authorization": AUTH_TOKEN,
                "Content-Type": "application/json"
            }
            response = requests.post(API_URL, headers=headers, json=payload, timeout=30)
            response.raise_for_status()

            # SNAPLOGIC SUCCESS
            st.success("Thank you! Your information has been submitted successfully. ✅")

            st.markdown("""
### What happens next?

Our **SnapLogic AI Agent** will now:

- Enrich your profile with public info about your company  
- Analyze your notes to understand your challenges  
- Prepare a **personalized email tailored to your needs**  
- Notify our **booth team**, so we can follow up with the right context  

You will hear from us very soon!
            """)

        except requests.exceptions.RequestException as e:
            st.error("There was an issue sending your data to our AI system.")
            st.code(str(e))

# ===================================
# FOOTER
# ===================================
st.markdown(
    "<div class='footer'>SnapLogic © 2025 — Powered by Agentic Automation</div>",
    unsafe_allow_html=True
)
