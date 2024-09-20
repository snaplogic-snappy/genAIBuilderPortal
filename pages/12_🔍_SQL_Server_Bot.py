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


st.set_page_config(page_title="GenAI Builder - Chatbot")
st.title("SQL Server Bot")
st.markdown(
    """

    ### This use-case is about querying SQL style databases using natural language.
    This chatbot will allow you to ask  questions of the data (in this case a table of accounts) and get a natural response, including the raw SQL for validation purposes.
     Examples 
    - Which account made the most money in 2015 ?
    - How many accounts were active in 2024 ?
    """
)
# Initialize chat history
if "SQL_messages" not in st.session_state:
    st.session_state.SQL_messages = []

# Display chat messages from history on app rerun
for message in st.session_state.SQL_messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# React to user input
prompt = st.chat_input("Ask me anything about the data in the SQL Server Database")
if prompt:
    st.chat_message("user").markdown(prompt)
    # Add user message to chat history
    st.session_state.SQL_messages.append({"role": "user", "content": prompt})

    with st.spinner("Working..."):
        URL = 'https://emea.snaplogic.com/api/1/rest/slsched/feed/ConnectFasterInc/Joe/SQL_GenAI/Get%20SQL%20Schema%20from%20Task'
        BEARER_TOKEN = 'tROo6n4jVsV1u3RhxKvbihsNIHNxZ1zJ'
    
        data = {"prompt": prompt}
    
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
        # st.write(result)
        # response=result[0]['choices'][0]['message']['content']
        response = result[0]['content'] + '\n\n```' + result[0]['sql'] + '```'
        # Display assistant response in chat message container
        with st.chat_message("assistant"):
            # st.markdown(response,unsafe_allow_html=True)
            typewriter(text=response, speed=10)
    
        # Add assistant response to chat history
        st.session_state.SQL_messages.append({"role": "assistant", "content": response})
