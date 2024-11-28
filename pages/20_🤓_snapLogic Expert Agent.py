import streamlit as st
import requests
import time
from dotenv import dotenv_values

# Load environment
env = dotenv_values(".env")
URL = "https://emea.snaplogic.com/api/1/rest/slsched/feed/ConnectFasterInc/snapLogic4snapLogic/AutoRFPAgent/ApiRfpAgent"
BEARER_TOKEN = "nNpLBJrd8FAtFh3TVC9xR97QAwWtJHgF"
timeout = 300

def typewriter(text: str, speed: int):
    tokens = text.split()
    container = st.empty()
    for index in range(len(tokens) + 1):
        curr_full_text = " ".join(tokens[:index])
        container.markdown(curr_full_text)
        time.sleep(1 / speed)

st.set_page_config(page_title="SnapLogic Expert Assistant")
st.title("SnapLogic Expert Assistant")
st.markdown(
    """  
    ### AI-powered RFP and technical expert assistant
    Get detailed answers to RFP questions and technical inquiries, with information sourced from official documentation, Slack discussions, and various other SnapLogic resources.
    
    Sample queries:
    - What security certifications does SnapLogic maintain?
    - Describe SnapLogic's approach to API management
    - What is the SnapLogic disaster recovery strategy?
    - How does SnapLogic handle data encryption at rest and in transit?
    - What monitoring capabilities are available in the platform?
    - Explain SnapLogic's integration with identity providers
 """)

# Initialize chat history
if "expert_assistant" not in st.session_state:
    st.session_state.expert_assistant = []

# Display chat messages from history
for message in st.session_state.expert_assistant:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# React to user input
prompt = st.chat_input("Ask me anything about SnapLogic's technical capabilities")
if prompt:
    st.chat_message("user").markdown(prompt)
    st.session_state.expert_assistant.append({"role": "user", "content": prompt})
    with st.spinner("Working..."):
        data = {"prompt": prompt}
        headers = {
            'Authorization': f'Bearer {BEARER_TOKEN}'
        }
        response = requests.post(
            url=URL,
            data=data,
            headers=headers,
            timeout=timeout,
            verify=False
        )
        if response.status_code == 200:
            try:
                result = response.json()
                if "response" in result:
                    assistant_response = result["response"]
                    with st.chat_message("assistant"):
                        typewriter(text=assistant_response, speed=10)
                    st.session_state.expert_assistant.append({"role": "assistant", "content": assistant_response})
                else:
                    with st.chat_message("assistant"):
                        st.error("❌ Invalid response format from API")
            except ValueError:
                with st.chat_message("assistant"):
                    st.error("❌ Invalid JSON response from API")
        else:
            st.error(f"❌ Error while calling the SnapLogic API")
        st.rerun()
