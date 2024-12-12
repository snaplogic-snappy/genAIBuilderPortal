import streamlit as st
import requests
import time
from dotenv import dotenv_values

# Load environment
env = dotenv_values(".env")
URL = "https://demo-fm.snaplogic.io/api/1/rest/feed-master/queue/ConnectFasterInc/Dylan%20Vetter/CRM_Agent/CRM_Ultra"
BEARER_TOKEN = "12345"
timeout = 300

def typewriter(text: str, speed: int):
    tokens = text.split()
    container = st.empty()
    for index in range(len(tokens) + 1):
        curr_full_text = " ".join(tokens[:index])
        container.markdown(curr_full_text)
        time.sleep(1 / speed)

st.set_page_config(page_title="SnapLogic CRM Assistant")
st.title("SnapLogic CRM Assistant")
st.markdown(
    """  
    ### AI-powered CRM assistant
    This is a CRM Agent demo that allows employees to interact with Production Systems using Natural Language
    
    Sample queries:
    - What campaigns are completed and what were their performance metrics? Include names
    - What accounts are in New York?
    - What are my 3 top opportunities? Please include information about the respective account
    - What is the names of the opportunities are sourced from partners and what the total amount?
 """)

# Initialize chat history
if "expert_assistant" not in st.session_state:
    st.session_state.expert_assistant = []

# Display chat messages from history
for message in st.session_state.expert_assistant:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# React to user input
prompt = st.chat_input("Ask me anything about CRM objects")
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
                        typewriter(text=assistant_response, speed=30)
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
