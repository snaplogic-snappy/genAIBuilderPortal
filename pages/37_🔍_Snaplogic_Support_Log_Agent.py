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

#Banner & Title
st.set_page_config(
    page_title="Support Log Agent",
    page_icon="🔍"
)

st.title("SnapLogic Support Agent (Preview)")

st.subheader("This agent analyzes the log data of your environment and provides a detailed report for failed runtime executions.")
st.markdown('')


# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Create form
with st.form("agent_form"):
    st.write("Last hours of runtime to assess")
    last_hours = st.slider("Last Hours",min_value=1,max_value=1080,value=24,help="Select the number of past hours to analyze. The max is 1080 hours, equivalent to 45 days.")  #Last Hours slider
    successful_exec = st.checkbox("Include successful executions") #Get Execution Errors


# Submit button for the form
    submitted = st.form_submit_button(label="Submit",type="primary",icon=":material/check_circle:")
    

if submitted:

    progress_text = "Getting log analysis from the past "+str(last_hours)+" hours..."
    my_bar = st.progress(0, text=progress_text)
    for percent_complete in range(100):
        time.sleep(0.2)
        my_bar.progress(percent_complete + 1, text=progress_text)
    time.sleep(1)

    #pipeline url: https://cdn.emea.snaplogic.com/sl/designer.html#pipe_snode=6813b13d18cf2cce4fbcdaf5
    URL = 'https://emea.snaplogic.com/api/1/rest/slsched/feed/ConnectFasterInc/snapLogic4snapLogic/SnapLogicSupportAgent/GetExecutionLogDataTask'
    BEARER_TOKEN ='lgle9VfbVi5GE7VY8MkgOk2tkQLfrQ7e'

    headers = {
        'Authorization': f'Bearer {BEARER_TOKEN}'
    }
    
    params = {
    'hours': last_hours,
    'inc_successful': str(successful_exec),
    'state':"Failed"
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
