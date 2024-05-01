import streamlit as st
import requests
import time
from dotenv import dotenv_values


# Load environment
env = dotenv_values(".env")
# SnapLogic RAG pipeline
URL = env["SL_HR_TASK_URL"]
BEARER_TOKEN = env["SL_HR_TASK_TOKEN"]
timeout = int(env["SL_TASK_TIMEOUT"])
namespace = env["SL_HR_TASK_NAMESPACE"]
# Streamlit Page Properties
page_title=env["HR_PAGE_TITLE"]
title=env["HR_TITLE"]


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
    ### This is a HR Chatbot demo that allows employees to ask HR questions 
    Examples 
    - When do I get paid ?
    - Do I get a bonus ?
    - What is the expense policy ?
 """)

# Initialize chat history
if "hr_messages" not in st.session_state:
    st.session_state.hr_messages = []

# Display chat messages from history on app rerun
for message in st.session_state.hr_messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# React to user input
prompt = st.chat_input("Ask me anything")
if prompt:
    st.chat_message("user").markdown(prompt)
    # Add user message to chat history
    st.session_state.hr_messages.append({"role": "user", "content": prompt})
    with st.spinner("Working..."):
        params={'namespace': namespace}
        data = {"prompt" : prompt}
        headers = {
            'Authorization': f'Bearer {BEARER_TOKEN}'
        }
        response = requests.post(
            url=URL,
            params=params,
            data=data,
            headers=headers,
            timeout=timeout,
            verify=False
        )

        result = response.json()
        # with st.chat_message("assistant"):
        #     st.markdown(result)
        response=result['choices'][0]['message']['content'].replace("NEWLINE ", "**") + "**"

        
        # Display assistant response in chat message container
        with st.chat_message("assistant"):
            typewriter(text=response, speed=10)
        # Add assistant response to chat history
        st.session_state.hr_messages.append({"role": "assistant", "content": response})