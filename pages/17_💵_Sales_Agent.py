import streamlit as st
import requests
import time
from dotenv import dotenv_values
from streamlit_oauth import OAuth2Component
import requests
import base64
import json


# Load & Set environment variables 
env = dotenv_values(".env")
AUTHORIZE_URL = env["SF_AUTHORIZE_URL"]
TOKEN_URL = env["SF_TOKEN_URL"]
REVOKE_TOKEN_URL = env["SF_REVOKE_TOKEN_URL"]
REDIRECT_URI=env["SF_REDIRECT_URI"]
SCOPE=env["SF_SCOPE"]

# Load & Set Secrets
CLIENT_ID = st.secrets["SF_CLIENT_ID"]
CLIENT_SECRET = st.secrets["SF_CLIENT_SECRET"]

# API Endpoint
URL = "https://prodeu-connectfasterinc-cloud-fm.emea.snaplogic.io/api/1/rest/feed/ConnectFasterInc/apim/SnapLogic Sales Agent/2.0/callAgentWorkerSalesAssistant"
timeout = 180

# Create OAuth Object
oauth2 = OAuth2Component(CLIENT_ID, CLIENT_SECRET, AUTHORIZE_URL, TOKEN_URL, TOKEN_URL, REVOKE_TOKEN_URL)

def typewriter(text: str, speed: int):
    tokens = text.split()
    container = st.empty()
    for index in range(len(tokens) + 1):
        curr_full_text = " ".join(tokens[:index])
        container.markdown(curr_full_text)
        time.sleep(1 / speed)

def cleartoken():
    # Revoke Access Token in SF
    oauth2.revoke_token(st.session_state["SF_token"])
    del st.session_state["SF_token"]
    del st.session_state["SF_id_token"]
    del st.session_state["SF_user"]
    del st.session_state["SF_auth"]
    del st.session_state["SF_access_token"]
    del st.session_state["sales_assistant"]


st.set_page_config(page_title="SnapLogic Sales Assistant")
st.title("SnapLogic Sales Assistant")
st.markdown(
    """  
   
    ### AI-powered sales assistant for SnapLogic employees
    Get instant answers to your sales-related questions, with references to official SnapLogic content.
    
    Sample queries:
    - What are SnapLogic's key differentiators against MuleSoft?
    - Create a customer facing documents with customer success stories in the healthcare industry
    - What's our pricing model for enterprise customers?
    - What ROI metrics can I share with prospects?
    - Find competitive analysis against Boomi for financial services
    - What's our partner program structure?
 """)

# Check for (Access) token in Sesion State
if "SF_token" not in st.session_state:

    # create a button to start the OAuth2 flow
    result = oauth2.authorize_button(
        name="Log in",
        icon="https://www.salesforce.com/etc/designs/sfdc-www/en_us/favicon.ico",
        redirect_uri=REDIRECT_URI, 
        scope=SCOPE,
        use_container_width=False
    )
    
    if result:
        print(result)
        st.write(result)
        #decode the id_token jwt and get the user's email address
        id_token = result["token"]["id_token"]
        access_token = result["token"]["access_token"]
        # verify the signature is an optional step for security
        payload = id_token.split(".")[1]
        # add padding to the payload if needed
        payload += "=" * (-len(payload) % 4)
        payload = json.loads(base64.b64decode(payload))
        email = payload["email"]
        username = payload["name"]
        st.session_state["SF_token"] = result["token"]
        st.session_state["SF_user"] = username
        st.session_state["SF_auth"] = email
        st.session_state["SF_access_token"]=access_token
        st.session_state["SF_id_token"]=id_token
        st.rerun()
else:
    st.write(f"Congrats **{st.session_state.SF_user}**, you are logged in now!")
    if st.button("Log out"):
        cleartoken()
        st.rerun()

    # Initialize chat history
    if "sales_assistant" not in st.session_state:
        st.session_state.sales_assistant = []

    # Display chat messages from history on app rerun
    for message in st.session_state.sales_assistant:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # React to user input
    prompt = st.chat_input("Ask me anything about SnapLogic sales")
    if prompt:
        st.chat_message("user").markdown(prompt)
        st.session_state.sales_assistant.append({"role": "user", "content": prompt})
        with st.spinner("Working..."):
            data = {"prompt" : prompt}
            headers = {
                'Authorization': f'Bearer {st.session_state["SF_access_token"]}'
            }
            response = requests.post(
                url=URL,
                data=data,
                headers=headers,
                timeout=timeout,
                verify=False
            )
            if response.status_code == 200:
                try:
                    result = response.json()
                    if "response" in result:
                        assistant_response = result["response"]
                        with st.chat_message("assistant"):
                            typewriter(text=assistant_response, speed=30)
                        st.session_state.sales_assistant.append({"role": "assistant", "content": assistant_response})
                    else:
                        with st.chat_message("assistant"):
                            st.error("❌ Invalid response format from API")
                except ValueError:
                    with st.chat_message("assistant"):
                        st.error("❌ Invalid JSON response from API")
            else:
                st.error(f"❌ Error while calling the SnapLogic API")
                cleartoken()
            st.rerun()
