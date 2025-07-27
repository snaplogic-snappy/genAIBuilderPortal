import streamlit as st
import requests
import time
from dotenv import dotenv_values

# Demo metadata for search and filtering
DEMO_METADATA = {
    "categories": ["Technical"],
    "tags": ["SnapLogic", "Runtime", "Debugging"]
}

def typewriter(text: str, speed: int):
    tokens = text
    container = st.empty()
    for index in range(len(tokens) + 1):
        curr_full_text = " ".join(tokens[:index])
        container.markdown(curr_full_text)
        time.sleep(1 / speed)

#Banner & Title
st.set_page_config(
    page_title="Support Log Agent",
    page_icon="🔍"
)

st.title("SnapLogic Runtime ID Agent")

st.subheader("This agent analyzes the log data based on your runtime ID and provides a detailed report for the failure.")
st.markdown('')


# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Create form
with st.form("agent_form"):
    runtime_id = st.text_input("Execution Runtime ID", "")


# Submit button for the form
    submitted = st.form_submit_button(label="Submit",type="primary",icon=":material/check_circle:")
    

if submitted:

    progress_text = "Getting log analysis for "+str(runtime_id)
    my_bar = st.progress(0, text=progress_text)
    for percent_complete in range(100):
        time.sleep(0.2)
        my_bar.progress(percent_complete + 1, text=progress_text)
    time.sleep(1)

    URL = 'https://emea.snaplogic.com/api/1/rest/slsched/feed/ConnectFasterInc/snapLogic4snapLogic/SnapLogicSupportAgent/GetExecutionLogDataByRuntimeIdAPI'
    BEARER_TOKEN ='AJbqtIE3rprlzy3K2DQwisLa9B2il0Bt'

    headers = {
        'Authorization': f'Bearer {BEARER_TOKEN}'
    }
    
    params = {
    'id': runtime_id    
    }

    response = requests.get(
        url=URL,
        headers=headers,
        timeout=180,
        verify=False,
        params=params
    )

    if response.status_code == 200:
        result = response.json()
        post_content = result["response"]
                        
        # Display the generated post in a nice format
        with st.chat_message("assistant"):
            my_bar.empty()
            st.markdown("### Extracted Execution Log Data")
            st.markdown("---")
            typewriter(text=post_content, speed=30)

    
    #st.write(result)
    # Display assistant response in chat message container
    with st.chat_message("assistant"):
        st.markdown(response,unsafe_allow_html=True)
        #typewriter(text=response, speed=10)
