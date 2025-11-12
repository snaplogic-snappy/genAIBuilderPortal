# ai_data_analytics_insights_summit_live.py
# Lead capture + SnapLogic AI Agent integration (fire-and-forget via background thread)

import streamlit as st
import requests
import uuid
import re
import threading
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


def async_post(url: str, headers: dict, payload: dict):
    """
    Fire-and-forget POST to SnapLogic.
    Runs in a background thread so the UI never waits for the AI Agent to finish.
    """
    try:
        # 30s is fine here because this does NOT block the UI.
        requests.post(url, headers=headers, json=payload, timeout=30)
    except Exception:
        # We intentionally ignore any exceptions here:
        # - network blips
        # - timeouts
        # The user already got a success message and the booth team
        # can monitor failures via SnapLogic logs.
        pass


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
# FORM PROCESSING — FIRE & FORGET
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
            # Bedrock Converse-style messages for the orchestrator agent
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"text": lead_text}
                    ],
                }
            ],
        }

        headers = {
            "Authorization": AUTH_TOKEN,
            "Content-Type": "application/json"
        }

        # Fire-and-forget: run the POST in a background thread
        threading.Thread(
            target=async_post,
            args=(API_URL, headers, payload),
            daemon=True
        ).start()

        # Immediate success for the user (no waiting for AI Agent)
        st.success("Thank you! Your information has been submitted successfully. ✅")

        st.markdown("""
### What happens next?

Our **SnapLogic AI Agent** is now processing your information in the background.

Behind the scenes it will:
- Enrich your profile with public information  
- Analyze your notes to understand your challenges  
- Generate a **personalized follow-up email**  
- Notify our **booth team** so we can follow up with the right context  

You will hear from us soon — enjoy the summit!
        """)

# ===================================
# FOOTER
# ===================================
st.markdown(
    "<div class='footer'>SnapLogic © 2025 — Powered by Agentic Automation</div>",
    unsafe_allow_html=True
)
