# ai_data_analytics_insights_summit.py
# Minimal Streamlit lead capture app for the AI Data, Analytics & Insights Summit DACH.
# The form collects attendee info and (when enabled) can trigger a SnapLogic AI workflow.

import streamlit as st
import re

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
# BASIC STYLING
# ===================================
st.markdown("""
<style>
.block-container { padding-top: 2rem; max-width: 700px; margin: auto; }
.stButton>button[disabled] { opacity: 0.6 !important; cursor: not-allowed !important; }
textarea::placeholder { color:#9ca3af; opacity: 1; }
.footer { text-align:center; color:#6b7280; font-size:0.85rem; margin-top:2rem; }
</style>
""", unsafe_allow_html=True)

# ===================================
# CONFIG PLACEHOLDERS (NOT YET ACTIVE)
# ===================================
API_URL = ""       # e.g. "https://emea.snaplogic.com/api/1/rest/slsched/.../SummitLeadProcessor"
AUTH_TOKEN = ""    # e.g. "Bearer xxxxx"

EMAIL_REGEX = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"

def valid_email(addr: str) -> bool:
    return bool(re.match(EMAIL_REGEX, addr or ""))

# ===================================
# HEADER + INTRO
# ===================================
st.title("🎯 AI Data, Analytics & Insights Summit DACH")
st.subheader("Smart Lead Capture powered by SnapLogic")

st.markdown("""
Welcome to the **AI Data, Analytics & Insights Summit DACH**!

Please share your contact details below.  
Once fully enabled, our **SnapLogic AI Agent** will:
- Analyze your organization’s public digital footprint  
- Use your notes to understand your challenges and interests  
- Generate a **hyper-relevant follow-up email** tailored to your **role**, **company**, and **context**

_Submissions are currently disabled for the event demo._
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
        "Notes (optional but very helpful)",
        placeholder=(
            "Why do you visit the AI, DATA ANALYTICS AND INSIGHTS SUMMIT DACH?\n"
            "What is challenging in your daily work?\n"
            "How would an ideal solution look like for you?"
        ),
        height=160
    )

    st.markdown("Fields marked with * are required.")

    # Submit button (disabled until backend is ready)
    submitted = st.form_submit_button(
        "Submit → Send to SnapLogic AI Agent",
        disabled=True  # Set to False once you’re ready to go live
    )

# ===================================
# SUCCESS SCREEN (for when submit is enabled)
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
        # 🔌 Here is where you’d call SnapLogic in the future:
        # - Build a JSON payload with name, email, role, company, notes
        # - POST it to API_URL with AUTH_TOKEN
        # - Let SnapLogic handle enrichment + email drafting

        # For now, we only show a success screen.
        st.success("Thank you! Your information has been submitted successfully. ✅")

        st.markdown("""
### What happens next?

Behind the scenes, our **SnapLogic AI Agent** will:

- Enrich your profile with public information about your **company** and **strategic initiatives**
- Analyze your **notes** to understand your challenges and priorities
- Prepare a **personalized follow-up** with ideas on how AI, data integration, and automation
  can support your work

You’ll hear from us soon with a tailored message.
        """)

# ===================================
# FOOTER
# ===================================
st.markdown(
    "<div class='footer'>"
    "SnapLogic © 2025 · To enable live submissions, configure <code>API_URL</code>, <code>AUTH_TOKEN</code>, "
    "wire the SnapLogic call into the <code>if submitted:</code> block, and set <code>disabled=False</code> on the Submit button."
    "</div>",
    unsafe_allow_html=True
)
