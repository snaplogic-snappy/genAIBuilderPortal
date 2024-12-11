import streamlit as st
import requests
import time
from dotenv import dotenv_values

# Load environment
env = dotenv_values(".env")

# SnapLogic RAG pipeline
URL = "https://prodeu-connectfasterinc-cloud-fm.emea.snaplogic.io/api/1/rest/feed/ConnectFasterInc/apim/SnapLogic%20Sales%20Agent/1.0/callAgentWorkerSalesAssistant"
BEARER_TOKEN = "rsFZlA7hO5Ngp4loIH600cXHcKKluHYL"
timeout = 180

def typewriter(text: str, speed: int):
    tokens = text.split()
    container = st.empty()
    for index in range(len(tokens) + 1):
        curr_full_text = " ".join(tokens[:index])
        container.markdown(curr_full_text)
        time.sleep(1 / speed)

def handle_api_error(status_code: int) -> str:
    error_messages = {
        401: "Authentication error: Invalid or expired token",
        403: "Authorization error: Insufficient permissions to access this resource",
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
                    result = response.json()
                    if "response" in result:
                        assistant_response = result["response"]
                        with st.chat_message("assistant"):
                            typewriter(text=assistant_response, speed=30)
                        st.session_state.sales_assistant.append({"role": "assistant", "content": assistant_response})
                    else:
                        st.session_state.error_message = "❌ Invalid response format from API"
                except ValueError as e:
                    st.session_state.error_message = "❌ Invalid JSON response from API"
            else:
                error_message = handle_api_error(response.status_code)
                st.session_state.error_message = f"❌ {error_message}"
                    
        except requests.exceptions.Timeout:
            st.session_state.error_message = "❌ Request timed out. Please try again later.\n\nIf this persists, contact jarcega@snaplogic.com"
        except requests.exceptions.ConnectionError:
            st.session_state.error_message = "❌ Connection error. Please check your internet connection.\n\nIf this persists, contact jarcega@snaplogic.com"
        except Exception as e:
            st.session_state.error_message = f"❌ An unexpected error occurred: {str(e)}\n\nPlease report this to jarcega@snaplogic.com"
        
        st.rerun()
