import streamlit as st
import requests
import time
import webbrowser
from dotenv import dotenv_values

# Load environment
env = dotenv_values(".env")

# SnapLogic RAG pipeline
URL = "https://prodeu-connectfasterinc-cloud-fm.emea.snaplogic.io/api/1/rest/feed/ConnectFasterInc/apim/SnapLogic%20Sales%20Agent/1.0/callAgentWorkerSalesAssistant"
BEARER_TOKEN = "b752b027d75439d8b14675082bdd3093"
timeout = 180

def typewriter(text: str, speed: int):
    tokens = text.split()
    container = st.empty()
    for index in range(len(tokens) + 1):
        curr_full_text = " ".join(tokens[:index])
        container.markdown(curr_full_text)
        time.sleep(1 / speed)

def handle_api_error(status_code: int, response_headers: dict) -> str:
    if status_code in (401, 403):
        # Check if there's a redirect URL in the response headers
        login_url = response_headers.get('Location') or response_headers.get('location')
        if login_url:
            # Open the Salesforce login popup
            webbrowser.open(login_url)
            return "You need to login to Salesforce. A login window has been opened. Please login and try again."
        return "Authentication required. Please login to Salesforce and try again."
    
    error_messages = {
        404: "Resource not found: The requested endpoint doesn't exist",
        429: "Too many requests: Rate limit exceeded",
        500: "Internal server error: Something went wrong on the server",
        502: "Bad gateway: The server received an invalid response",
        503: "Service unavailable: The server is temporarily down",
        504: "Gateway timeout: The server took too long to respond"
    }
    base_message = error_messages.get(status_code, f"Unexpected error (Status code: {status_code})")
    return f"{base_message}\n\nPlease report this issue to jarcega@snaplogic.com with the following details:\n- Time of error: {time.strftime('%Y-%m-%d %H:%M:%S')}\n- Status code: {status_code}"

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

# Initialize chat history
if "sales_assistant" not in st.session_state:
    st.session_state.sales_assistant = []

# Initialize error state
if "error_message" not in st.session_state:
    st.session_state.error_message = None

# Display error message if exists
if st.session_state.error_message:
    st.error(st.session_state.error_message)
    # Clear error after displaying
    st.session_state.error_message = None

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
        try:
            data = {"prompt": prompt}
            headers = {
                'Authorization': f'Bearer {BEARER_TOKEN}'
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
                    # Print raw response for debugging
                    print("Raw response:", response.text)
                    result = response.json()
                    if "response" in result:
                        assistant_response = result["response"]
                        with st.chat_message("assistant"):
                            typewriter(text=assistant_response, speed=30)
                        st.session_state.sales_assistant.append({"role": "assistant", "content": assistant_response})
                    else:
                        st.session_state.error_message = "❌ Invalid response format from API. Expected 'response' field in JSON."
                except ValueError as e:
                    st.session_state.error_message = f"❌ Invalid JSON response from API. Error details: {str(e)}\n\nPlease report this to jarcega@snaplogic.com with the following response:\n{response.text[:200]}..."
            else:
                error_message = handle_api_error(response.status_code, response.headers)
                st.session_state.error_message = f"❌ {error_message}"
                    
        except requests.exceptions.Timeout:
            st.session_state.error_message = "❌ Request timed out. Please try again later.\n\nIf this persists, contact jarcega@snaplogic.com"
        except requests.exceptions.ConnectionError:
            st.session_state.error_message = "❌ Connection error. Please check your internet connection.\n\nIf this persists, contact jarcega@snaplogic.com"
        except Exception as e:
            st.session_state.error_message = f"❌ An unexpected error occurred: {str(e)}\n\nPlease report this to jarcega@snaplogic.com"
        
        st.rerun()
