import streamlit as st
import requests
import time
import json
import uuid

# Configuration
URL = "https://elastic.snaplogic.com/api/1/rest/slsched/feed/ConnectFasterInc/.Rich/Agent_Creator/USMC_Web_Scraper_Agent%20Task"
BEARER_TOKEN = "lRMyWuyrlHaUe8UJVH94eHVL9n7kYm6n"
timeout = 300

def typewriter(text: str, speed: int):
    tokens = text.split()
    container = st.empty()
    for index in range(len(tokens) + 1):
        curr_full_text = " ".join(tokens[:index])
        container.markdown(curr_full_text)
        time.sleep(1 / speed)

st.set_page_config(page_title="USMC Web Assistant")
st.title("USMC Web Assistant")

st.markdown("""
### Please enter any questions about USMC regulations

This assistant provides information about Marine Corps regulations, policies, and facilities based on official documentation.
""")

# Initialize session ID if not exists
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display sample question suggestion
if not st.session_state.messages:
    st.info("Sample questions you can ask:")
    st.markdown("""
    - What is the Marine Corps regulation on tattoos?
    - Are beards allowed in the Marine Corps?
    - What are the Marine Corps bases in California?
    - What are the Marine Corps requirements for mustaches?
    """)

# Display chat messages from history
for message in st.session_state.messages:
    with st.chat_message(message["sl_role"].lower()):
        st.markdown(message["content"])

# React to user input
prompt = st.chat_input("Ask a question about USMC regulations")
if prompt:
    # Add user message to chat
    st.chat_message("user").markdown(prompt)
    user_message = {"content": prompt, "sl_role": "USER"}
    st.session_state.messages.append(user_message)
    
    with st.spinner("Searching USMC regulations..."):
        # Prepare payload for API
        payload = json.dumps([{
            "session_id": st.session_state.session_id,
            "messages": st.session_state.messages
        }])
        
        headers = {
            'Authorization': f'Bearer {BEARER_TOKEN}',
            'Content-Type': 'application/json'
        }
        
        # Call the API
        try:
            response = requests.post(
                url=URL,
                data=payload,
                headers=headers,
                timeout=timeout
            )
            
            if response.status_code == 200:
                try:
                    result = response.json()
                    if "response" in result:
                        assistant_response = result["response"]
                        with st.chat_message("assistant"):
                            typewriter(text=assistant_response, speed=30)
                        
                        # Add assistant message to chat history
                        assistant_message = {"content": assistant_response, "sl_role": "ASSISTANT"}
                        st.session_state.messages.append(assistant_message)
                    else:
                        with st.chat_message("assistant"):
                            st.error("❌ Invalid response format from API")
                except ValueError:
                    with st.chat_message("assistant"):
                        st.error("❌ Invalid JSON response from API")
            else:
                with st.chat_message("assistant"):
                    st.error(f"❌ Error while calling the API: {response.status_code}")
        except Exception as e:
            with st.chat_message("assistant"):
                st.error(f"❌ Exception occurred: {str(e)}")
        
        st.rerun()

# Add footer
st.markdown("""
---
*This assistant provides information based on official USMC documentation. For the most accurate and up-to-date information, please consult official Marine Corps publications.*
""")
