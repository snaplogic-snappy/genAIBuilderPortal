import streamlit as st
import requests
import time
from dotenv import dotenv_values
import os

# Load environment
env = dotenv_values(".env")

# Customer Intelligence API endpoint
URL = "https://emea.snaplogic.com/api/1/rest/slsched/feed/ConnectFasterInc/Aleksandra%20Kulawska/customer_churn/main_pipeline%20Task"
BEARER_TOKEN = "vSOLUL58nAc0Yaq2YaADIxgORNpSf98b"
timeout = 300

def typewriter(text: str, speed: int):
    tokens = text.split()
    container = st.empty()
    for index in range(len(tokens) + 1):
        curr_full_text = " ".join(tokens[:index])
        container.markdown(curr_full_text)
        time.sleep(1 / speed)

st.set_page_config(
    page_title="Customer Intelligence Assistant",
    layout="wide"
)

# Title and description
st.title("🛍️ Customer Intelligence AI Assistant")
st.caption("Your customers. SnapLogic's AI.")

# Custom CSS for stats container
st.markdown("""
    <style>
    .stats-container {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
    </style>
""", unsafe_allow_html=True)

# Stats section in a container
st.markdown('<div class="stats-container">', unsafe_allow_html=True)
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Total Segments", "5", "Active")
with col2:
    st.metric("Active Customers", "12,458", "+2.4%")
with col3:
    st.metric("Avg. Customer Value", "$487", "+$23")
with col4:
    st.metric("Churn Risk", "14%", "-2%")
st.markdown('</div>', unsafe_allow_html=True)

# Features container
with st.expander("🎯 What can this assistant do?", expanded=True):
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
        ### Key Features
        - 📊 Segment Analysis
        - 💰 Customer Value Tracking
        - 📈 Behavior Pattern Detection
        """)
    with col2:
        st.markdown("""
        ### Sample Questions
        - "Show purchase patterns by segment"
        - "What defines our high-value segments?"
        - "Which segments have highest churn risk?"
        """)

# Chat interface
st.markdown("---")
st.subheader("💬 Ask About Your Customers")

# Initialize chat history and toggle states
if "customer_analytics" not in st.session_state:
    st.session_state.customer_analytics = []
if "toggle_states" not in st.session_state:
    st.session_state.toggle_states = {}

# Display chat messages from history
for idx, message in enumerate(st.session_state.customer_analytics):
    with st.chat_message(message["role"]):
        if message["role"] == "assistant":
            st.markdown(message.get("answer", message.get("content", "")))
            if message.get("summary"):
                toggle_key = f"toggle_{idx}"
                with st.expander("View Analysis Details", expanded=False):
                    st.markdown(message["summary"])
        else:
            st.markdown(message["content"])

# Chat input
prompt = st.chat_input("Ask me anything about your customer segments...")
if prompt:
    st.chat_message("user").markdown(prompt)
    st.session_state.customer_analytics.append({"role": "user", "content": prompt})
    
    with st.spinner("Analyzing customer data..."):
        data = {"prompt": prompt}
        headers = {'Authorization': f'Bearer {BEARER_TOKEN}'}
        
        try:
            response = requests.post(
                url=URL,
                json=data,
                headers=headers,
                timeout=timeout,
                verify=False
            )
            
            if response.status_code == 200:
                try:
                    result = response.json()
                    if len(result) > 0 and isinstance(result[0], dict):
                        response_data = result[0]
                        answer = response_data.get("answer", "")
                        summary = response_data.get("summary", "")
                        visualizations = response_data.get("visualizations", None)
                        
                        with st.chat_message("assistant"):
                            typewriter(text=answer, speed=10)
                            
                            if visualizations:
                                st.plotly_chart(visualizations, use_container_width=True)
                            
                            if summary:
                                with st.expander("View Analysis Details", expanded=False):
                                    st.markdown(summary)
                        
                        st.session_state.customer_analytics.append({
                            "role": "assistant",
                            "answer": answer,
                            "summary": summary,
                            "visualizations": visualizations
                        })
                    else:
                        with st.chat_message("assistant"):
                            st.error("❌ Invalid response format from API")
                except ValueError:
                    with st.chat_message("assistant"):
                        st.error("❌ Invalid JSON response from API")
            else:
                with st.chat_message("assistant"):
                    st.error(f"❌ API Error: {response.status_code}")
        except requests.exceptions.RequestException as e:
            with st.chat_message("assistant"):
                st.error(f"❌ Connection Error: {str(e)}")
        
        st.rerun()
