import streamlit as st
import requests
import time
from dotenv import dotenv_values


# Load environment
env = dotenv_values(".env")
# SnapLogic RAG pipeline
URL = env["SL_CRM_TASK_URL"]
BEARER_TOKEN = env["SL_CRM_TASK_TOKEN"]
timeout = int(env["SL_TASK_TIMEOUT"])
# Streamlit Page Properties
page_title=env["CRM_PAGE_TITLE"]
title=env["CRM_TITLE"]

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
    ### This is a an CRM AI Assistant demo that allows management to ask questions about Accounts and Opportunities in Salesforce 
    Examples 
    - Which opportunities have the best chance of closing in February 2023?
    - List all opportunities, sorted by Amount higher first, return Name, amount and closing date
    - What is the total amount of opportunities closing in 2024 ?
 """)

# Initialize chat history
if "CRM_messages" not in st.session_state:
    st.session_state.CRM_messages = []

# Display chat messages from history on app rerun
for message in st.session_state.CRM_messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# React to user input
prompt = st.chat_input("Ask me anything related to Salesforce Pipeline, Accounts and Opportunities")
if prompt:
    st.chat_message("user").markdown(prompt)
    # Add user message to chat history
    st.session_state.CRM_messages.append({"role": "user", "content": prompt})

    with st.spinner("Working..."):
        
        data = {"prompt" : prompt}
    
        headers = {
            'Authorization': f'Bearer {BEARER_TOKEN}'
        }
    
        response = requests.post(
            url=URL,
            data=data,
            headers=headers,
            timeout=180,
            verify=False
        )
    
        result = response.json()
        #st.write(result)
        response=result[0]['choices'][0]['message']['content'] + "\n\n"
        soql_cmd=result[0]['soql']
        # Display assistant response in chat message container
        with st.chat_message("assistant"):
            st.markdown(response,unsafe_allow_html=True)
            with st.expander("Generated SOQL command", expanded=False):
                st.markdown(soql_cmd,unsafe_allow_html=True)
    
        # Add assistant response to chat history
        st.session_state.CRM_messages.append({"role": "assistant", "content": response+soql_cmd})
        #st.rerun()
