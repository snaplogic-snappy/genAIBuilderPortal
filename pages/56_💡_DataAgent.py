import streamlit as st
import requests
import json
import os
import re
from dotenv import load_dotenv
import urllib3

# Demo metadata for search and filtering
DEMO_METADATA = {
    "categories": ["Business Intelligence"],
    "tags": ["Agents", "Demo", "Data Analysis", "Analytics"]
}
# Disable SSL warnings for self-signed certificates
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Load environment variables
env = dotenv_values(".env")

# Configuration
URL = env["SL_GA_TASK_URL"]
BEARER_TOKEN = env["SL_GA_TASK_TOKEN"]
timeout = int(env["SL_TASK_TIMEOUT"])

# API_URL = "https://a18c9f3a83b3e40a69da924330ab4acd-2111898486.eu-west-3.elb.amazonaws.com/api/1/rest/feed/run/task/ConnectFasterInc/Toni/Toni_Agent_Data/DataAgent_Orchestrator_API"
# BEARER_TOKEN = "XkZD5Ac5WpKzlX9gC81pGDzEs84lfF2D"
# timeout = 180
API_URL = env["SL_DA_TASK_URL"]
BEARER_TOKEN = env["SL_DA_TASK_TOKEN"]
timeout = int(env["SL_TASK_TIMEOUT"])

# Page configuration
st.set_page_config(
    page_title="Data Chat Assistant",
    page_icon="💬",
    layout="wide"
)

# Custom CSS
st.markdown("""
    <style>
    .stChatMessage {
        padding: 1rem;
        border-radius: 0.5rem;
    }
    /* Make the main content area scrollable */
    section[data-testid="stVerticalBlock"] > div:has(div.element-container div.stChatMessage) {
        height: 500px;
        overflow-y: auto;
        border: 1px solid #e0e0e0;
        border-radius: 0.5rem;
        padding: 1rem;
        background-color: #fafafa;
    }
    </style>
""", unsafe_allow_html=True)

# Initialize session state for chat history
if "da_messages" not in st.session_state:
    st.session_state.da_messages = []

def query_snaplogic_agent(question: str) -> dict:
    """
    Query the SnapLogic DataAgent with a natural language question.
    
    Args:
        question: The user's question about the data
        
    Returns:
        dict: The response from the API
    """
    headers = {
        "Authorization": f"Bearer {BEARER_TOKEN}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "query": question
    }
    
    try:
        response = requests.get(
            API_URL,
            headers=headers,
            json=payload,
            verify=False,
            timeout=timeout
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}

def format_response(response_data: dict) -> str:
    """
    Format the API response for display in the chat.
    
    Args:
        response_data: The raw response from the API
        
    Returns:
        str: Formatted response text
    """
    if "error" in response_data:
        return f"❌ Error: {response_data['error']}"
    
    if isinstance(response_data, list) and len(response_data) > 0:
        response_content = response_data[0].get("response", "")
        
        # Fix number spacing issues
        response_content = re.sub(r'(\d),\s+(\d{3})', r'\1,\2', response_content)
        response_content = re.sub(r'\$(\d+),\s+(\d{3})', r'$\1,\2', response_content)
        response_content = re.sub(r'to\s+\$', 'to $', response_content)
        response_content = re.sub(r'\)\s*to\s+', ') to ', response_content)
        response_content = re.sub(r'(\d+)\s*—\s*(\d+)', r'\1 to \2', response_content)
        response_content = re.sub(r'\*\*([^*]+?)\*\*\s*:', r'**\1:**', response_content)
        response_content = re.sub(r',(\w)', r', \1', response_content)
        response_content = re.sub(r'\.(\w)', r'. \1', response_content)
        response_content = re.sub(r'AOV\s*\*([^*]+)\*', r'AOV (\1)', response_content)
        response_content = re.sub(r'(\d+)AOV', r'\1 AOV', response_content)
        response_content = re.sub(r'(\d+)orders', r'\1 orders', response_content)
        response_content = re.sub(r'(\d+)generating', r'\1 generating', response_content)
        response_content = re.sub(r'\*\(', '(', response_content)
        response_content = re.sub(r'\)\*', ')', response_content)
        
        return response_content
    
    return json.dumps(response_data, indent=2)

# App header (always visible)
st.title("💬 Data Chat Assistant")
st.markdown("Ask questions about your data in natural language!")
st.markdown("""   
    ### 💡 How to Use
    Simply type your question in the chat input below and get instant insights from your data!
""")
# Connection status and controls at the top
col_status, col_clear = st.columns([3, 1])
with col_status:
    if API_URL and BEARER_TOKEN:
        st.success("✅ Connected to SnapLogic")
    else:
        st.error("❌ Missing configuration. Check your .env file")

with col_clear:
    if st.button("🗑️ Clear Chat"):
        st.session_state.da_messages = []
        st.rerun()

# Example questions section (always visible)
st.markdown("---")

col1, col2 = st.columns(2)

with col1:
    st.markdown("""
    ### 📊 Revenue & Orders
    - What is the daily revenue for the last 30 days?
    - Show me the average order value (AOV)
    - What's the total order value by status?
    
    ### 🏆 Top Performers
    - What are the top 10 products by revenue in the last 90 days?
    - Which customers contribute to 80% of our sales?
    - Show me customer lifetime value rankings
    
    ### 👥 Customer Insights
    - How many new vs returning customers this month?
    - What's our repeat purchase rate?
    - Which customers have never placed an order?
    """)

with col2:
    st.markdown("""
    ### 📦 Product Analytics
    - Show me product margins sorted by profitability
    - Which products have never been ordered?
    - How many active vs discontinued products do we have?
    
    ### 🌍 Geographic Analysis
    - What's the revenue breakdown by shipping city?
    - Show me customer default shipping addresses
    """)

st.markdown("---")
st.markdown("### 💬 Chat")

# Chat container with fixed height
chat_placeholder = st.container(height=500)

with chat_placeholder:
    if len(st.session_state.da_messages) == 0:
        st.info("👋 Start chatting by typing a question below!")
    else:
        for message in st.session_state.da_messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

# Chat input (always visible at bottom)
if prompt := st.chat_input("Ask a question about your data..."):
    # Add user message to chat history and rerun immediately to show it
    st.session_state.da_messages.append({"role": "user", "content": prompt})
    st.session_state.waiting_for_response = True
    st.rerun()

# If waiting for response, query the agent
if st.session_state.get("waiting_for_response", False):
    with st.spinner("Analyzing your data..."):
        # Get the last user message
        last_user_message = st.session_state.da_messages[-1]["content"]
        response = query_snaplogic_agent(last_user_message)
        formatted_response = format_response(response)
        print("DEBUG: API Response:", formatted_response)
    
    # Add assistant response to chat history
    st.session_state.da_messages.append({"role": "assistant", "content": formatted_response})
    st.session_state.waiting_for_response = False
    st.rerun()

# Footer
st.divider()
st.caption("Powered by SnapLogic DataAgent | Streamlit Chat Interface")