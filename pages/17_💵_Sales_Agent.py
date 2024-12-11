import streamlit as st
import requests
import time
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
                    # First try to parse as JSON
                    result = response.json()
                    if "response" in result:
                        assistant_response = result["response"]
                        with st.chat_message("assistant"):
                            typewriter(text=assistant_response, speed=30)
                        st.session_state.sales_assistant.append({"role": "assistant", "content": assistant_response})
                except ValueError:
                    # If it's not JSON, check if it's the auth HTML
                    if 'text/html' in response.headers.get('content-type', '').lower():
                        # Create a container for the auth HTML
                        auth_container = st.empty()
                        # Render the HTML which contains the redirect script
                        auth_container.components.html(response.text, height=0)
                        st.info("🔒 Redirecting to Salesforce login... Please complete the authentication and try again.")
                    else:
                        st.error("❌ Invalid response format from API")
                        
        except requests.exceptions.Timeout:
            st.error("❌ Request timed out. Please try again later.\n\nIf this persists, contact jarcega@snaplogic.com")
        except requests.exceptions.ConnectionError:
            st.error("❌ Connection error. Please check your internet connection.\n\nIf this persists, contact jarcega@snaplogic.com")
        except Exception as e:
            st.error(f"❌ An unexpected error occurred: {str(e)}\n\nPlease report this to jarcega@snaplogic.com")

        st.rerun()
