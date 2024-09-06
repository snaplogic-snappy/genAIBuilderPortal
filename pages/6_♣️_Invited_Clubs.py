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
st.title("Invited Clubs - Formerly ClubCorp")

st.markdown(
    """  
    ### This is a Hospitality Chatbot demo that enables inquirers to ask questions about Invited Clubs Golf
    Examples 
    - What Clubs are located in Texas
    - Other Property Information
    - Member Attendance
    - Tee Time availability
 """)

# Initialize chat history
if "IC_messages" not in st.session_state:
    st.session_state.IC_messages = []

# Display chat messages from history on app rerun
for message in st.session_state.IC_messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# React to user input
prompt = st.chat_input("Ask me anything related to Invited Clubs")
if prompt:
    st.chat_message("user").markdown(prompt)
    # Add user message to chat history
    st.session_state.IC_messages.append({"role": "user", "content": prompt}) 
    with st.spinner("Working..."):
        URL = 'https://demo-fm.snaplogic.io/api/1/rest/feed/run/task/ConnectFasterInc/Demo_GenAI_App_Builder_NA/Invited%20Clubs/ACB%20-%20GenAI%20Step%202%20-%20Invited%20Clubs%20-%20RAG%20Task'
        BEARER_TOKEN = 'P2IjJo0bdIfmQ4k6rq0r4QTRR8LRI5kp'
    
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
        st.session_state.IC_messages.append({"role": "assistant", "content": response})
