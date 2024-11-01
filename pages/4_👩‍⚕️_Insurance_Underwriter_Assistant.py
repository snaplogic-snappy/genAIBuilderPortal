import streamlit as st
import requests
import time
from dotenv import dotenv_values


# Load environment
env = dotenv_values(".env")
# SnapLogic RAG pipeline
URL = env["SL_UW_TASK_URL"]
BEARER_TOKEN = env["SL_UW_TASK_TOKEN"]
timeout = int(env["SL_TASK_TIMEOUT"])
#namespace = env["SL_UW_TASK_NAMESPACE"]
# Streamlit Page Properties
page_title=env["UW_PAGE_TITLE"]
title=env["UW_TITLE"]


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
    ### This is a an Insurance Assistant demo that allows underwriters to ask questions about a patient medical history 
    Examples 
    - What medical conditions has patient had and when
	- What test results have been done and when?
	- Which test results were abnormal and have normal tests been done since
	- Have any genetic tests been carried out and noted.
	- What medication have they taken and when?
	- What conditions does the patient have and what medication is associated to it?
 """)

# Initialize chat history
if "health_insurance" not in st.session_state:
    st.session_state.health_insurance = []

# Display chat messages from history on app rerun
for message in st.session_state.health_insurance:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# React to user input
prompt = st.chat_input("Ask me anything")
if prompt:
    st.chat_message("user").markdown(prompt)
    # Add user message to chat history
    st.session_state.health_insurance.append({"role": "user", "content": prompt})
    with st.spinner("Working..."):
        #params={'namespace': namespace}
        data = {"prompt" : prompt}
        headers = {
            'Authorization': f'Bearer {BEARER_TOKEN}'
        }
        response = requests.post(
            url=URL,
            #params=params,
            data=data,
            headers=headers,
            timeout=timeout,
            verify=False
        )

        if response.status_code==200:
            result = response.json()
            if len(result) > 0 :
                response=result[0]
                # Display assistant response in chat message container
                with st.chat_message("assistant"):
                    typewriter(text=response, speed=10)
                # Add assistant response to chat history
                st.session_state.health_insurance.append({"role": "assistant", "content": response})
            else:
                with st.chat_message("assistant"):
                    st.error(f"❌ Error in the SnapLogic API response: Empty Result")
        else:
                st.error(f"❌ Error while calling the SnapLogic API")
        st.rerun()
