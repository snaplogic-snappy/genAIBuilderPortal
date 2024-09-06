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
st.title("Wendys")

st.markdown(
    """  
    ### This is a Food and Beverage (Financial) Chatbot demo that enables inquirers to ask questions about Wendys Annual Reports.
    Inquiry Examples: 
    - What is Wendys Annual Revenue?
    - What was Wendys Profit this year?
    - How many stores does Wendys have? 
    - What was the same restaurant sales growth?
 """)

# Initialize chat history
if "Wendys_messages" not in st.session_state:
    st.session_state.Wendys_messages = []

# Display chat messages from history on app rerun
for message in st.session_state.Wendys_messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# React to user input
prompt = st.chat_input("Ask me anything related to Wendys Public Financial Reports")
if prompt:
    st.chat_message("user").markdown(prompt)
    # Add user message to chat history
    st.session_state.Wendys_messages.append({"role": "user", "content": prompt})

    with st.spinner("Working..."):
        URL = 'https://elastic.snaplogic.com/api/1/rest/slsched/feed/ConnectFasterInc/Demo_GenAI_App_Builder_NA/Wendys/ACB%20-%20GenAI%20Step%202%20-%20Wendys%20-%20RAG%20Task'
        BEARER_TOKEN = '34fjzpIsKF8B8YAtupdEBHkQEG1e0OTy'
    
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
        st.session_state.Wendys_messages.append({"role": "assistant", "content": response})
