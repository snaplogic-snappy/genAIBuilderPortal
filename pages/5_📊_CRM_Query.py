import streamlit as st
import requests
import time

def typewriter(text: str, speed: int):
    tokens = text.split()
    container = st.empty()
    for index in range(len(tokens) + 1):
        curr_full_text = " ".join(tokens[:index])
        container.markdown(curr_full_text)
        time.sleep(1 / speed)

st.set_page_config(page_title="CRM Chatbot - *BETA*")
st.title("Query directly against Salesforce")

st.markdown(
    """  
    ### This is a an CRM Chatbot demo that allows management to ask questions about Accounts and Opportunities in Salesforce 
    Examples 
    - Which opportunities have the best chance of closing in February 2023?
 """)

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# React to user input
prompt = st.chat_input("Ask me anything related to Salesforce Pipeline, Accounts and Opportunities")
if prompt:
    st.chat_message("user").markdown(prompt)
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})

    URL = 'https://snapgpt.labs.snaplogicdev.com/api/1/rest/slsched/feed/snaplogic/projects/Nilesh%20Parmar/GenAI_SOQL_Generation_NP_Task'
    BEARER_TOKEN ='KKsuIzfnymYwRbzKuKsazMo1cE9bQ1QM'

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
    response=result[0]['choices'][0]['message']['content']
    # Display assistant response in chat message container
    with st.chat_message("assistant"):
        #st.markdown(response,unsafe_allow_html=True)
        typewriter(text=response, speed=10)

    # Add assistant response to chat history
    st.session_state.messages.append({"role": "assistant", "content": response})
