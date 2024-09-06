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
st.title("AT&T 5G Services")

st.markdown(
    """  
    ### This is a Communications Industry Chatbot demo that enables inquirers to ask questions about AT&T 5G service along with AT&T Protect Advantage to understand compatibiity, upgrades and asset support
    Examples 
    - What is 5G?
    - What is the best 5G Phone right now?
    - How do I find a great deal on a 5G phone?
    - How much does 5G cost?
    - What is AT&T Protect Advantage?
 """)

# Initialize chat history
if "ATT_messages" not in st.session_state:
    st.session_state.ATT_messages = []

# Display chat messages from history on app rerun
for message in st.session_state.ATT_messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# React to user input
prompt = st.chat_input("Ask me anything related to AT&T 5G Service and Protection")
if prompt:
    st.chat_message("user").markdown(prompt)
    # Add user message to chat history
    st.session_state.ATT_messages.append({"role": "user", "content": prompt})

    with st.spinner("Working..."):
        URL = 'https://elastic.snaplogic.com/api/1/rest/slsched/feed/ConnectFasterInc/Demo_GenAI_App_Builder_NA/AT%26T/ACB%20-%20GenAI%20Step%202%20-%20ATT%20-%20RAG%20Task'
        BEARER_TOKEN = 'kQAK3K0nrlQf7Qgit0TGbJOYC1Bb2nPS'
    
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
        st.session_state.ATT_messages.append({"role": "assistant", "content": response})
