import streamlit as st
import requests
import time

def typewriter(text: str, speed: int):
    tokens = text
    container = st.empty()
    for index in range(len(tokens) + 1):
        curr_full_text = " ".join(tokens[:index])
        container.markdown(curr_full_text)
        time.sleep(1 / speed)

st.set_page_config(
    page_title="Support Agent Dashboard",
    page_icon="🔍"
)

st.title("SnapLogic Support Agent (Preview)")

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Create form

with st.form("agent_form"):
    st.write("Last Hours to Analyze")
    slider_val = st.slider("Last Hours",min_value=1,max_value=1080,value=24,help="Select the number of past hours to analyse. The max is 1080 hours, equivalent to 45 days.")  #Last Hours slider
    checkbox_val = st.checkbox("Get failed executions") #Get Execution Errors
    checkbox_val = st.checkbox("Get successful executions") #Get Execution Errors

# Submit button for the form
    submitted = st.form_submit_button(label="Submit",type="primary",icon=":material/check_circle:")

if submitted:
    URL = 'https://emea.snaplogic.com/api/1/rest/slsched/feed/ConnectFasterInc/snapLogic4snapLogic/SnapLogicSupportAgent/GetExecutionLogDataTask'
    BEARER_TOKEN ='lgle9VfbVi5GE7VY8MkgOk2tkQLfrQ7e'

    headers = {
        'Authorization': f'Bearer {BEARER_TOKEN}'
    }

    response = requests.get(
        url=URL,
        headers=headers,
        timeout=180,
        verify=False
    )
    if response.status_code == 200:
        result = response.json()
        post_content = result[0]["response"]
                        
        # Display the generated post in a nice format
        with st.chat_message("assistant"):
            st.markdown("### Extracted Execution Log Data")
            st.markdown("---")
            typewriter(text=post_content, speed=30)
        
    

    #st.write(result)
    # Display assistant response in chat message container
    with st.chat_message("assistant"):
        st.markdown(response,unsafe_allow_html=True)
        #typewriter(text=response, speed=10)
