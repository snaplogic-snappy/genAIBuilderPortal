# ai_data_analytics_insights_summit.py
# Minimal Streamlit lead capture app for the AI Data, Analytics & Insights Summit.
# The form collects attendee info and (when enabled) triggers a SnapLogic AI workflow.

import streamlit as st
import uuid
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
h1, h2, h3 { text-align: center; }
.footer { text-align:center; color:#6b7280; font-size:0.85rem; margin-top:2rem; }
</style>
""", unsafe_allow_html=True)

# ===================================
# CONFIG PLACEHOLDERS (NOT YET ACTIVE)
# ===================================
API_URL = ""       # e.g. "https://emea.snaplogic.com/api/1/rest/slsched/.../SummitLeadProcessor"
AUTH_TOKEN = ""    # e.g. "Bearer xxxxx"

# ===================================
# HEADER + INTRO
# ===================================
st.title("🎯 AI Data, Analytics & Insights Summit")
st.subheader("Smart Lead Capture powered by SnapLogic")

st.markdown("""
Welcome to the **AI Data, Analytics & Insights Summit**!

Please share your contact details below.  
After submission, our **SnapLogic AI Agent** (once enabled) will:
- Research your company’s public digital footprint and strategic initiatives  
- Tailor a personalized follow-up email that’s highly relevant to your **role** and **organization**  

_Submissions are currently disabled for the live event demo._
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

    st.markdown("All fields are required.")

    # Submit button (disabled until SnapLogic backend is ready)
    submitted = st.form_submit_button("Submit → Send to SnapLogic AI Agent", disabled=True)

# ===================================
# FOOTER
# ===================================
st.markdown(
    "<div class='footer'>"
    "SnapLogic © 2025 | This demo form is part of the AI Data, Analytics & Insights Summit. "
    "To activate live submissions, configure <code>API_URL</code> and <code>AUTH_TOKEN</code> "
    "and enable the Submit button."
    "</div>",
    unsafe_allow_html=True
)
