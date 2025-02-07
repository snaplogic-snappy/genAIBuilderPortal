import streamlit as st
import requests
import time
import uuid
from dotenv import dotenv_values
from streamlit_oauth import OAuth2Component
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
URL = "https://prodeu-connectfasterinc-cloud-fm.emea.snaplogic.io/api/1/rest/feed-master/queue/ConnectFasterInc/apim/SnapLogic%20Sales%20Agent/3.0/SalesAgentUltra"
timeout = 180

# Create OAuth Object
oauth2 = OAuth2Component(CLIENT_ID, CLIENT_SECRET, AUTHORIZE_URL, TOKEN_URL, TOKEN_URL, REVOKE_TOKEN_URL)

def typewriter(text: str, speed: int):
    container = st.empty()
    full_text = ""
    for char in text:
        full_text += char
        container.markdown(full_text)
        time.sleep(1 / (speed * 5))

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

    # Initialize session state
    if "session_id" not in st.session_state:
        st.session_state.session_id = str(uuid.uuid4())
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display chat messages from history on app rerun
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # React to user input
    prompt = st.chat_input("Ask me anything about SnapLogic sales")
    if prompt:
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.chat_message("user").markdown(prompt)

        with st.spinner("Working..."):
            # Prepare the payload with session ID and messages
            data = {
                "session_id": st.session_state.session_id,
                "messages": st.session_state.messages,
            }
            headers = {
                'Authorization': f'Bearer {st.session_state["SF_access_token"]}',
                'Content-Type': 'application/json'
            }
            try:
                response = requests.post(
                    url=URL,
                    json=data,
                    headers=headers,
                    timeout=timeout,
                    verify=False
                )
                response.raise_for_status()
                result = response.json()
                if "response" in result:
                    assistant_response = result["response"]
                    # Add assistant response to chat history
                    st.session_state.messages.append({"role": "assistant", "content": assistant_response})
                    with st.chat_message("assistant"):
                        typewriter(text=assistant_response, speed=30)
                else:
                    st.error("Invalid response format from API")
            except Exception as e:
                st.error(f"An error occurred: {str(e)}")
