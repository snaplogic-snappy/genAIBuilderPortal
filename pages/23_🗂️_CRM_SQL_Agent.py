import streamlit as st
import requests
import time
from dotenv import dotenv_values


# Load environment
env = dotenv_values(".env")
# SnapLogic RAG pipeline
URL = env["SL_CRM_SQL_TASK_URL"]
BEARER_TOKEN = env["SL_CRM_SQL_TASK_TOKEN"]
timeout = int(env["SL_TASK_TIMEOUT"])
# Streamlit Page Properties
page_title=env["CRM_SQL_PAGE_TITLE"]
title=env["CRM_SQL_TITLE"]


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
    ### This is a CRM and SQL Agent demo that allows employees to interact with Production Systems using Natural Language
    Examples 
    - What accounts are in New york?
    - What’s the cost per response for our most expensive campaign?
    - How did the Re:Invent campaign impact opportunities and market share?
 """)

# Initialize chat history
if "CRM_SQL_messages" not in st.session_state:
    st.session_state.CRM_SQL_messages = []

# Display chat messages from history on app rerun
for message in st.session_state.CRM_SQL_messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# React to user input
prompt = st.chat_input("Ask me anything")
if prompt:
    st.chat_message("user").markdown(prompt)
    # Add user message to chat history
    st.session_state.CRM_SQL_messages.append({"role": "user", "content": prompt})
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

        if response.status_code==200:
            result = response.json()
            # with st.chat_message("assistant"):
            #     st.markdown(result)
            if 'choices' in result:
                response=result['choices'][0]['message']['content'].replace("NEWLINE ", "**") + "**" + "\n\n"
                # Display assistant response in chat message container
                with st.chat_message("assistant"):
                    typewriter(text=response, speed=10)
                # Add assistant response to chat history
                st.session_state.CRM_SQL_messages.append({"role": "assistant", "content": response})
            else:
                with st.chat_message("assistant"):
                    st.error(f"❌ Error in the SnapLogic API response")
                    st.error(f"{result['reason']}")
        else:
            with st.chat_message("assistant"):
                st.error(f"❌ Error while calling the SnapLogic API")
        st.rerun()
