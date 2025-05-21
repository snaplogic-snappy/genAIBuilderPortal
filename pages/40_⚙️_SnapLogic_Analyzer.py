import streamlit as st
import requests
import time
import json # Import json for formatting the request data

# API Configuration - Updated for SnapLogic Analyzer
URL = "https://emea.snaplogic.com/api/1/rest/slsched/feed/ConnectFasterInc/snapLogic4snapLogic/SKO/snapLogicAnalyzer"
BEARER_TOKEN = "XB9BTnDJ9gJW7OVjSID2hH4vEDu5JiE8" # New Bearer Token
timeout = 300

def typewriter(text: str, speed: int):
    """Displays text with a typewriter effect."""
    tokens = text.split()
    container = st.empty()
    for index in range(len(tokens) + 1):
        curr_full_text = " ".join(tokens[:index])
        container.markdown(curr_full_text)
        time.sleep(1 / speed)

# Page Configuration
st.set_page_config(page_title="SnapLogic Analyzer Chatbot")
st.title("🤖 SnapLogic Analyzer Chatbot")

st.markdown("""
### Your AI-powered assistant for SnapLogic insights.

Ask questions about your SnapLogic environment, pipeline executions, and more.
""")

st.markdown("""
🔍 **Sample Queries:**
- What are the last five pipelines executed?
- Show me failed pipeline executions in the last 24 hours.
- Which projects have the most active pipelines?
- What is the average duration of the 'Main Data Load' pipeline?
- List all pipelines triggered by 'scheduler_user@example.com'.
""")

# Initialize chat history
if "analyzer_chat" not in st.session_state:
    st.session_state.analyzer_chat = []

# Display chat messages from history
for message in st.session_state.analyzer_chat:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# React to user input
prompt = st.chat_input("Ask about your SnapLogic pipelines...")
if prompt:
    st.chat_message("user").markdown(prompt)
    st.session_state.analyzer_chat.append({"role": "user", "content": prompt})

    with st.spinner("Analyzing... 🤔"):
        # Construct the data payload as a list of dictionaries
        data_payload = [{"prompt": prompt}]
        headers = {
            'Authorization': f'Bearer {BEARER_TOKEN}',
            'Content-Type': 'application/json' # Good practice to specify content type
        }

        try:
            response = requests.post(
                url=URL,
                # Send data as JSON
                data=json.dumps(data_payload), # Convert the list of dicts to a JSON string
                headers=headers,
                timeout=timeout,
                verify=False # Note: In production, consider certificate verification
            )

            if response.status_code == 200:
                try:
                    result = response.json()
                    if "response" in result:
                        assistant_response = result["response"]
                        with st.chat_message("assistant"):
                            typewriter(text=assistant_response, speed=50) # Adjusted speed for potentially longer/formatted responses
                        st.session_state.analyzer_chat.append({"role": "assistant", "content": assistant_response})
                    else:
                        # Handle cases where 'response' key might be missing even with a 200
                        error_message = f"🔍 API returned a 200 OK, but the 'response' key is missing. Full response: ```{response.text}```"
                        with st.chat_message("assistant"):
                            st.error(error_message)
                        st.session_state.analyzer_chat.append({"role": "assistant", "content": error_message})
                except ValueError: # Handles JSON decoding errors
                    error_message = f"❌ Invalid JSON response from API. Status Code: {response.status_code}. Response body: ```{response.text}```"
                    with st.chat_message("assistant"):
                        st.error(error_message)
                    st.session_state.analyzer_chat.append({"role": "assistant", "content": error_message})
            else:
                error_message = f"❌ Error calling SnapLogic Analyzer API. Status Code: {response.status_code}. Response: ```{response.text}```"
                st.error(error_message)
                # Optionally add this to chat history as well if you want to display API errors in the chat
                # st.session_state.analyzer_chat.append({"role": "assistant", "content": error_message})

        except requests.exceptions.RequestException as e:
            error_message = f"CONNECTION ERROR: 🌐 Failed to connect to the SnapLogic Analyzer API. Please check your network or the API endpoint. Error: {e}"
            st.error(error_message)
            # st.session_state.analyzer_chat.append({"role": "assistant", "content": error_message})
    
    # Rerun to update the chat display immediately after processing
    st.rerun()