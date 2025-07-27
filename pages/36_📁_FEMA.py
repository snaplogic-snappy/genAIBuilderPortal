import streamlit as st
import requests
import json
import urllib3
import time
from dotenv import dotenv_values

# Demo metadata for search and filtering
DEMO_METADATA = {
    "categories": ["Industry"],
    "tags": ["Government", "Emergency Management", "FEMA"]
}

# Disable insecure request warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Page configuration
st.set_page_config(
    page_title="PA System Assistant",
    page_icon="🏛️",
    layout="centered"
)

# Constants
API_URL = "https://prodeu-connectfasterinc-cloud-fm.emea.snaplogic.io/api/1/rest/feed/run/task/ConnectFasterInc/Jordan%20Millhausen/Millhausen_pa_system/PASystemAgentDriver_api_v2"
BEARER_TOKEN = "12345"

# Hide Streamlit menu and footer
hide_streamlit_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            .block-container {padding-top: 2rem; padding-bottom: 2rem;}
            </style>
            """
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

# Custom CSS for styling similar to the image
st.markdown("""
    <style>
    .main-title {
        font-size: 2.3rem;
        font-weight: 700;
        margin-bottom: 0.5rem;
    }
    .sub-title {
        font-size: 1.2rem;
        font-weight: 400;
        color: #4F4F4F;
        margin-bottom: 1.5rem;
    }
    .context-text {
        font-size: 1rem;
        margin-bottom: 1.5rem;
    }
    .sample-query {
        margin-left: 1.5rem;
        margin-bottom: 1rem;
    }
    .sample-queries-container {
        margin-bottom: 2rem;
    }
    .chat-message {
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
        background-color: #f9f9f9;
    }
    .stButton button {
        background-color: #f0f2f6;
        border: 1px solid #ddd;
        border-radius: 5px;
        color: #4F4F4F;
        padding: 0.25rem 0.5rem;
        transition: all 0.2s ease;
    }
    .stButton button:hover {
        background-color: #e0e2e6;
        border-color: #ccc;
    }
    </style>
""", unsafe_allow_html=True)

def send_message(message):
    """
    Send a message to the PA System Agent API and get a response.
    """
    headers = {
        'Authorization': f'Bearer {BEARER_TOKEN}',
        'Content-Type': 'application/json'
    }
    
    # Match the payload structure from the working Quiz Analyzer example
    payload = {
        "message": message
    }
    
    try:
        with st.spinner("Thinking..."):
            response = requests.post(
                url=API_URL,
                json=payload,
                headers=headers,
                timeout=60,
                verify=False
            )
            
            # Debug info
            st.session_state.debug_info = {
                "status_code": response.status_code,
                "response_text": response.text[:500] + "..." if len(response.text) > 500 else response.text
            }
            
            response.raise_for_status()
            return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"API Error: {str(e)}")
        return {"response": f"Sorry, I encountered an error while processing your request: {str(e)}"}

def main():
    # Main header and description
    st.markdown('<div class="main-title">🏛️ PA System Assistant 🚨</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-title">🤖 AI-powered assistant for navigating FEMA funding processes 💼</div>', unsafe_allow_html=True)
    
    # Current context and sample queries
    st.markdown('<div class="context-text">📋 Your guide to navigating FEMA Public Assistance programs. Get instant answers about application processes, funding eligibility, and documentation requirements for disaster recovery.</div>', unsafe_allow_html=True)
    
    st.markdown('<div class="sample-queries-container">', unsafe_allow_html=True)
    st.markdown("✨ Sample queries:")
    st.markdown('<div class="sample-query">📝 What are the eligibility requirements for FEMA Public Assistance funding?</div>', unsafe_allow_html=True)
    st.markdown('<div class="sample-query">📸 How do I document damage for a successful claim?</div>', unsafe_allow_html=True)
    st.markdown('<div class="sample-query">⏱️ What is the timeline for receiving funds after approval?</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Initialize chat history
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    
    # Initialize debug info
    if "debug_info" not in st.session_state:
        st.session_state.debug_info = {}
    
    # Display chat history
    for message in st.session_state.chat_history:
        if message["role"] == "user":
            st.markdown(f"<div class='chat-message user'><strong>👤 You:</strong> {message['content']}</div>", unsafe_allow_html=True)
        else:
            st.markdown(f"<div class='chat-message assistant'><strong>🤖 Assistant:</strong> {message['content']}</div>", unsafe_allow_html=True)
    
    # Chat input with a placeholder similar to the image
    user_input = st.text_input(
        label="User Input", 
        placeholder="💬 Ask me anything about FEMA Public Assistance funding", 
        key="user_input",
        label_visibility="collapsed"  # This hides the label while keeping it accessible
    )
    
    # Send button (using a simple button with an arrow icon)
    col1, col2 = st.columns([6, 1])
    with col2:
        send_button = st.button("Send")
    
    if (send_button or user_input and user_input != st.session_state.get("previous_input", "")) and user_input:
        # Save current input to prevent duplicate submissions
        st.session_state.previous_input = user_input
        
        # Add user message to chat history
        st.session_state.chat_history.append({
            "role": "user", 
            "content": user_input
        })
        
        # Get response from API
        response_data = send_message(user_input)
        
        if response_data:
            # Get the response from the structure that matches your API response
            assistant_message = ""
            
            # Handle different response structures
            if isinstance(response_data, list) and len(response_data) > 0:
                # If response is a list like in the Quiz Analyzer example
                assistant_message = response_data[0].get("response", "I'm having trouble processing your request.")
            elif isinstance(response_data, dict):
                # If response is a dictionary
                assistant_message = response_data.get("response", "I'm having trouble processing your request.")
            else:
                # Fallback for other response types
                assistant_message = str(response_data)
            
            # Add assistant response to chat history
            st.session_state.chat_history.append({
                "role": "assistant",
                "content": assistant_message
            })
        
        # Rerun to update UI with new messages
        st.rerun()
    
    # Add a debug section that can be expanded
    with st.expander("Debug Info", expanded=False):
        st.json(st.session_state.debug_info)

if __name__ == "__main__":
    main()