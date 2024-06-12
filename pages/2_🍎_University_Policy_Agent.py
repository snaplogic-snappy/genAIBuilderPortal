import streamlit as st
import requests
import time
from dotenv import dotenv_values


# Load environment
env = dotenv_values(".env")
# SnapLogic RAG pipeline
URL = env["SL_UNI_TASK_URL"]
BEARER_TOKEN = env["SL_UNI_TASK_TOKEN"]
timeout = int(env["SL_TASK_TIMEOUT"])
namespace = env["SL_UNI_TASK_NAMESPACE"]
# Streamlit Page Properties
page_title=env["UNI_PAGE_TITLE"]
title=env["UNI_TITLE"]


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
    ### This is a University Policy Agent demo that allows students or parents to quickly answer their questions regarding University policies. 
    Examples 
    - Can I get a dog?
    - What happens if my son or daughter is intoxicated on campus?
    - I lost my ID, what should I do?
 """
)

# Initialize chat history
if "uni_messages" not in st.session_state:
    st.session_state.uni_messages = []

# Display chat messages from history on app rerun
for message in st.session_state.uni_messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# React to user input
prompt = st.chat_input("Ask me anything about our University Policies")
if prompt:
    st.chat_message("user").markdown(prompt)
    # Add user message to chat history
    st.session_state.uni_messages.append({"role": "user", "content": prompt})
    with st.spinner("Working..."):
        params = {'namespace': namespace}
        data = {"prompt": prompt}
        headers = {
            'Authorization': f'Bearer {BEARER_TOKEN}',
            'Content-Type': 'application/json'
        }
        response = requests.post(
            url=URL,
            params=params,
            json=data,  # Ensure the payload is sent as JSON
            headers=headers,
            timeout=timeout,
            verify=False
        )

        if response.status_code == 200:
            result = response.json()
            print(result)  # For debugging purposes
            if 'completion' in result:
                response_text = result['completion'].replace("NEWLINE ", "\n") + "\n"
                # Display assistant response in chat message container
                with st.chat_message("assistant"):
                    typewriter(text=response_text, speed=10)
                # Add assistant response to chat history
                st.session_state.uni_messages.append({"role": "assistant", "content": response_text})
            else:
                with st.chat_message("assistant"):
                    st.error("❌ Error in the SnapLogic API response")
        else:
            with st.chat_message("assistant"):
                st.error(f"❌ Error while calling the SnapLogic API")