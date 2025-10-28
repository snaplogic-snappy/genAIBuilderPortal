# 57_🕸️_Graph_Intelligence_Dashboard.py

import streamlit as st
import requests
import uuid
import pandas as pd
import re

# --- Custom CSS Styling ---
st.markdown("""
    <style>
        /* Make code blocks smaller and tighter */
        code, pre {
            font-size: 0.85em !important;
        }

        /* Adjust container padding for a cleaner look */
        .stContainer {
            padding: 0.5rem !important;
        }

        /* Optional: slightly dim code color for softer contrast */
        code {
            color: #555 !important;
        }

        /* Reduce spacing between cards */
        div[data-testid="stVerticalBlock"] > div:nth-child(1) {
            margin-top: -0.25rem !important;
        }
    </style>
""", unsafe_allow_html=True)

# ==========================================================
# DEMO_METADATA - REQUIRED FOR SEARCH FUNCTIONALITY
# ==========================================================
DEMO_METADATA = {
    "categories": ["Technical"],
    "tags": ["GraphDB", "Neo4j", "Agent Creator", "AI Agent", "Sales", "Support", "Customer", "Product"]
}

# ==========================================================
# API CONFIGURATION
# ==========================================================
API_URL = "https://emea.snaplogic.com/api/1/rest/slsched/feed/ConnectFasterInc/snapLogic4snapLogic/KnowledgeAssistant/Knowledge%20Assistant%20AD%20Task"
AUTH_TOKEN = "Bearer vpRYcSE4iBmlYBsPqkQnhrdSCAqEcoKt"

# ==========================================================
# PAGE SETUP
# ==========================================================
st.set_page_config(
    page_title="Sales & Support Intelligence Agent",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ==========================================================
# SIDEBAR
# ==========================================================
with st.sidebar:
    st.image("https://placehold.co/400x100/002B45/FFFFFF?text=Sales+%26+Support+Agent", use_column_width=True)
    st.title("🧠 Sales & Support Intelligence Agent")
    st.info("Your co-pilot for customer, sales, and support insights powered by Neo4j (Graph Intelligence Dashboard).")
    
    if st.button("Start New Chat"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()

# ==========================================================
# SESSION INITIALIZATION
# ==========================================================
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

if "messages" not in st.session_state:
    st.session_state.messages = []

# ==========================================================
# HELPER FUNCTION
# ==========================================================
def display_agent_response(content: str):
    """Displays structured or markdown responses from the agent."""
    st.markdown(content)

# ==========================================================
# MAIN HEADER
# ==========================================================
st.title("🧠 Sales & Support Intelligence Agent")
st.caption(f"Session ID: {st.session_state.session_id}")

st.markdown("""
This **AI-powered Graph Intelligence Dashboard** helps you reason across your sales, support, and product graph data.  
It integrates with **Neo4j (or any GraphDB)** to provide contextual insights into customers, opportunities, and service cases.
""")

# ==========================================================
# TWO-COLUMN SCHEMA + INTRO SECTION
# ==========================================================
st.markdown("---")
st.subheader("📈 Schema Overview – Data Relationships")

col_left, col_right = st.columns([1, 1.2])

with col_left:
    st.markdown("""
    **Entity Relationships:**
    - 🧑‍💼 **Customer** connects to **Opportunities**, **Cases**, and **Products**  
    - 💼 **Opportunities** link to **Products** and **Sales Stages**  
    - 🧰 **Cases** represent support requests linked to **Issue Types**, **Status**, and **Priority**  
    - 🌍 **Customers** belong to **Regions**, **Industries**, and **Tiers**, and are managed by an **Account Manager**

    ---

    👋 **Welcome!**  
    I’m your **AI Sales & Support Intelligence Agent**, powered by the **SnapLogic Agent Creator** and connected to your **graph database**.

    This workspace combines **Sales**, **Service**, and **Product Intelligence** in one unified data graph — helping you:
    - Detect **cross-sell and upsell** opportunities from historical patterns  
    - Predict **deal outcomes** and **customer churn** likelihood  
    - Monitor **support case clusters** to identify recurring product issues  
    - Highlight **top-performing products** and **high-value customers**  
    - Uncover **similar accounts** to replicate winning strategies  

    By leveraging **graph relationships** and **AI reasoning**, the agent can reveal insights hidden across CRM, ERP, and support systems — without requiring SQL or Cypher expertise.

    **Ask me about:**
    - Customer performance and opportunities  
    - Support case analytics and critical issues  
    - Product recommendations and cross-sell opportunities  

    **Here are some example queries you can try:**
    """)


with col_right:
    schema_url = "https://raw.githubusercontent.com/snaplogic-snappy/genAIBuilderPortal/main/assets/57_Graph_Schema.png"

    try:
        st.markdown(
            f"""
            <div style="display:flex; justify-content:center; align-items:center;">
                <img src="{schema_url}" alt="Graph Schema" style="max-height:850px; width:auto; border-radius:8px;"/>
            </div>
            <p style="text-align:center; font-size:0.9em; color:gray;">
                Customer–Product–Opportunity–Case Data Model
            </p>
            """,
            unsafe_allow_html=True
        )
    except Exception as e:
        st.warning(f"⚠️ Could not load schema diagram. Error: {e}")


# ==========================================================
# EXAMPLE PROMPTS
# ==========================================================
if not st.session_state.messages:
    col1, col2, col3 = st.columns(3)

    with col1:
        with st.container(border=True):
            st.subheader("📊 Customer 360° Overview")
            st.code("Show me the full customer overview for Gamma Connect Solutions.")

        with st.container(border=True):
            st.subheader("📈 Opportunity Performance")
            st.code("List open opportunities by stage and expected close date.")

        with st.container(border=True):
            st.subheader("🎯 Account Manager Portfolio")
            st.code("Show me the accounts managed by Jean Grey.")

        with st.container(border=True):
            st.subheader("🗂 Support Case History")
            st.code("Show all open support cases for Vertex Analytics LLC.")

    with col2:
        with st.container(border=True):
            st.subheader("📦 Product Analytics")
            st.code("Analyze sales and case history for the Catalyst 9300 Switch.")

        with st.container(border=True):
            st.subheader("🚨 Critical Case Overview")
            st.code("List unresolved critical cases grouped by product.")

        with st.container(border=True):
            st.subheader("🏆 Top Performing Customers")
            st.code("Which customers have the highest closed-won revenue in 2025?")

        with st.container(border=True):
            st.subheader("🧭 Industry Distribution")
            st.code("Summarize opportunities by industry and tier.")

    with col3:
        with st.container(border=True):
            st.subheader("🤝 Cross-Sell Recommendations")
            st.code("Find cross-sell opportunities for Gamma Connect Solutions.")

        with st.container(border=True):
            st.subheader("🧠 Product Recommendations")
            st.code("Recommend products for Evergreen Logistics Solutions.")

        with st.container(border=True):
            st.subheader("🔗 Similar Customers")
            st.code("Find customers similar to Nexus Logistics Corp.")

        with st.container(border=True):
            st.subheader("🎯 Predict Opportunity Success")
            st.code("Predict the win likelihood for opportunity OPP00042.")

# ==========================================================
# CHAT HISTORY
# ==========================================================
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        if msg["role"] == "user":
            st.markdown(msg["content"])
        else:
            display_agent_response(msg["content"])

# ==========================================================
# CHAT INPUT + API CALL
# ==========================================================
if prompt := st.chat_input("Ask about customers, opportunities, or support cases..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Querying graph data and reasoning across Neo4j..."):
            try:
                api_messages = [
                    {"content": m["content"], "sl_role": "USER" if m["role"] == "user" else "ASSISTANT"}
                    for m in st.session_state.messages
                ]
                payload = {"session_id": st.session_state.session_id, "messages": api_messages}
                headers = {"Authorization": AUTH_TOKEN, "Content-Type": "application/json"}

                response = requests.post(API_URL, headers=headers, json=payload, timeout=120)
                response.raise_for_status()
                data = response.json()
                agent_response = data[0].get("response", "No response received from the agent.")
            except requests.exceptions.RequestException as e:
                agent_response = f"⚠️ **Request failed:** {str(e)}"
            except (KeyError, IndexError, ValueError) as e:
                agent_response = f"⚠️ **Parsing error:** {e}\n\nRaw response:\n{response.text}"

            display_agent_response(agent_response)
            st.session_state.messages.append({"role": "assistant", "content": agent_response})
