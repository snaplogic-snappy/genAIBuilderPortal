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

if 'doc_key' not in st.session_state:
    st.session_state.doc_key = None
    st.session_state.doc_status = 0

def doc_proc():
    if st.session_state.doc_key == None:
        st.session_state.doc_status = 0
    if st.session_state.doc_key != None:
        st.session_state.doc_status = 1


st.set_page_config(page_title="GenAI Builder - Chatbot")
st.title("Manufacturing Spec Assistant")
st.subheader("This is an Assistant to help users retrieve information from Manufacturing Specifications and Tests.", divider = "blue")

#with st.container(height=300):
with st.expander("Examples", expanded=True, icon=":material/lightbulb:"):
    st.markdown(
        """  
        Examples: 
        | Document | Question|
        | -------- | :-------- |
        | MSG_01_HGPL-B.pdf | What is the weight of the grippers by size? |
        | MSG_01_HGPL-B.pdf | What is the maximum operating frequency of the gripper? |
        | MSG_02_HGPT_HGPL_HGDT.pdf | What are the differences between the various grippers? |
        | MSG_02_HGPT_HGPL_HGDT.pdf  | What is the maximum lifting force of the HGPL in size 14? |
        | MSG_04_measurement_test.pdf | In which interval is the setpoint for the density? |
        | MSG_04_measurement_test.pdf | In which interval is the actual value for the density? |
        """)


# Document Selection
doc = st.radio(
    "**Which Document are you inquiring about?**",
    ["MSG_01_HGPL-B.pdf", "MSG_02_HGPT_HGPL_HGDT.pdf", "MSG_04_measurement_test.pdf"],
    index=None,
    key='doc_key',
    on_change=doc_proc(),
    
)

#st.write("You selected:", doc)

# Create Input Message
if st.session_state.doc_status == 0:
    st.inputmsg = "Choose a Document to begin chat"
    st.chatDisabled = True
if st.session_state.doc_status == 1:
    st.inputmsg = "What do you want to know about "+st.session_state.doc_key
    st.chatDisabled = False

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []


# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# React to user input
prompt = st.chat_input(placeholder=st.inputmsg,disabled=st.chatDisabled)
if prompt:
    st.chat_message("user").markdown(prompt)
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})

    URL = 'https://abd36121231c84034b34129e798681ad-485346289.eu-west-3.elb.amazonaws.com/api/1/rest/feed-master/queue/ConnectFasterInc/RG/msg/MSG_Ultra%20Task'
    BEARER_TOKEN = 's7R0GSJF7AfAayGFrSxHeFC3Tc1tjo3P'

    data = {"prompt" : prompt, "Document" : st.session_state.doc_key}

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
    response=result['choices'][0]['message']['content']

    # Display assistant response in chat message container
    with st.chat_message("assistant"):
        st.markdown(response,unsafe_allow_html=True)
        #typewriter(text=response, speed=10)

# Add assistant response to chat history
    st.session_state.messages.append({"role": "assistant", "content": response})
