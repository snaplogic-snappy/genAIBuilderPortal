import streamlit as st
import requests
import time
from dotenv import dotenv_values
import os

# Load environment
env = dotenv_values(".env")

# Customer Intelligence API endpoint
URL = "https://your-api-endpoint/customer-intelligence"
BEARER_TOKEN = env.get("API_TOKEN", "your-default-token")
timeout = 300

def typewriter(text: str, speed: int):
    tokens = text.split()
    container = st.empty()
    for index in range(len(tokens) + 1):
        curr_full_text = " ".join(tokens[:index])
        container.markdown(curr_full_text)
        time.sleep(1 / speed)

st.set_page_config(page_title="Customer Intelligence Assistant")
st.title("Customer Intelligence AI Assistant")

st.markdown("""  
    ### AI-powered assistant for understanding customer segments and behavior
    Ask questions about your customer base - the assistant will analyze patterns and provide actionable insights.
    
    Sample queries:
    - What are the key characteristics of each customer segment?
    - Which customer segments have the highest lifetime value?
    - What are the common purchasing patterns in each segment?
    - How do different segments respond to marketing campaigns?
    - Which segments show the highest churn risk?
""")

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
                if st.toggle("Show analysis process", False, key=toggle_key):
                    st.markdown("### Analysis Details")
                    st.markdown(message["summary"])
        else:
            st.markdown(message["content"])

# React to user input
prompt = st.chat_input("Ask me anything about your customer segments")
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
                            
                            # Display any visualizations if provided
                            if visualizations:
                                st.markdown("### Segment Visualization")
                                st.plotly_chart(visualizations)
                            
                            if summary:
                                toggle_key = f"toggle_{len(st.session_state.customer_analytics)}"
                                if st.toggle("Show analysis process", False, key=toggle_key):
                                    st.markdown("### Analysis Details")
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

# Add a sidebar with additional information
with st.sidebar:
    st.header("📊 Customer Segments Overview")
    st.info("""
    This assistant analyzes your customer base using advanced clustering algorithms to identify distinct customer segments. 
    
    It can help you understand:
    - Customer behavior patterns
    - Purchase frequency and value
    - Segment-specific trends
    - Churn risk factors
    - Campaign response rates
    """)
    
    # Add segment metrics (these would be populated by your backend)
    st.subheader("Quick Stats")
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Total Segments", "5")
        st.metric("Avg. Customer Value", "$487")
    with col2:
        st.metric("Active Customers", "12,458")
        st.metric("Churn Risk", "14%")
