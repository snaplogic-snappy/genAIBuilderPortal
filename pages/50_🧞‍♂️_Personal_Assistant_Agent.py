import streamlit as st
import requests
import time
from dotenv import dotenv_values

# Demo metadata for search and filtering
DEMO_METADATA = {
    "categories": ["Public Knowledge"],
    "tags": ["Agents", "Demo"]
}

# Load environment
env = dotenv_values(".env")
# SnapLogic RAG pipeline
URL = env["SL_GA_TASK_URL"]
BEARER_TOKEN = env["SL_GA_TASK_TOKEN"]
timeout = int(env["SL_TASK_TIMEOUT"])
# Streamlit Page Properties
page_title=env["GA_PAGE_TITLE"]
title=env["GA_TITLE"]


def typewriter(text: str, speed: int):
    tokens = text.split()
    container = st.empty()
    for index in range(len(tokens) + 1):
        curr_full_text = " ".join(tokens[:index])
        container.markdown(curr_full_text)
        time.sleep(1 / speed)

st.set_page_config(page_title=page_title)
st.title(title)

st.markdown(
    """  
    ### This is a Personal Assistant Agent that can answer questions and provide a response:
    - by email
    - by slack
    - saved as PDF in Box
    
    Examples 
    - What is the recipe for sponge cake? send it to me by slack at tbranco@snaplogic.com and by email at tbranco+demo@snaplogic.com. Export it as PDF
 """)

# Initialize chat history
if "ga_messages" not in st.session_state:
    st.session_state.ga_messages = []

# Display chat messages from history on app rerun
for message in st.session_state.ga_messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# React to user input
prompt = st.chat_input("Ask me anything")
if prompt:
    st.chat_message("user").markdown(prompt)
    # Add user message to chat history
    st.session_state.ga_messages.append({"role": "user", "content": prompt})
    with st.spinner("Working..."):
        data = {"prompt" : prompt}
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

        if response.status_code==200:
            result = response.json()[0]
            # Print to console (for debugging)
            print("DEBUG: API Result:", result)

            # with st.chat_message("assistant"):
            #     st.markdown(result)
            if 'response' in result:
                response=result['response'] + "\n\n"
                # Display assistant response in chat message container
                with st.chat_message("assistant"):
                    typewriter(text=response, speed=10)
                # Add assistant response to chat history
                st.session_state.ga_messages.append({"role": "assistant", "content": response})
            else:
                with st.chat_message("assistant"):
                    st.error(f"❌ Error in the SnapLogic API response")
                    st.error(f"{result['reason']}")
        else:
            with st.chat_message("assistant"):
                st.error(f"❌ Error while calling the SnapLogic API")
        st.rerun()
