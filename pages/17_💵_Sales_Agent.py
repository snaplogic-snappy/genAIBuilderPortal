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

def show_auth_button():
    """Create a button that opens Salesforce login in a new window"""
    auth_html = f"""
        <button 
            onclick="window.open('https://snaplogic.my.salesforce.com/services/oauth2/authorize', '_blank', 'width=600,height=700')"
            style="background-color: #0176d3; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer;"
        >
            Login with Salesforce
        </button>
    """
    st.markdown(auth_html, unsafe_allow_html=True)

st.set_page_config(page_title="SnapLogic Sales Assistant")
st.title("SnapLogic Sales Assistant")

# Check if user is authenticated
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

# Show login page if not authenticated
if not st.session_state.authenticated:
    st.markdown("### Please authenticate with Salesforce to continue")
    show_auth_button()
    # Add instructions
    st.markdown("""
        1. Click the button above to open Salesforce login
        2. Complete authentication in the popup window
        3. Return to this window and refresh the page
    """)
else:
    # Rest of your existing chat interface code here
    st.markdown("""  
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

    # Display chat messages from history
    for message in st.session_state.sales_assistant:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Chat input and response handling
    prompt = st.chat_input("Ask me anything about SnapLogic sales")
    if prompt:
        # Your existing chat handling code here...
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
                            st.error("❌ Invalid response format from API")
                    except ValueError:
                        st.error("❌ Authentication required. Please log in again.")
                        st.session_state.authenticated = False
                        st.rerun()
                            
            except requests.exceptions.Timeout:
                st.error("❌ Request timed out. Please try again later.\n\nIf this persists, contact jarcega@snaplogic.com")
            except requests.exceptions.ConnectionError:
                st.error("❌ Connection error. Please check your internet connection.\n\nIf this persists, contact jarcega@snaplogic.com")
            except Exception as e:
                st.error(f"❌ An unexpected error occurred: {str(e)}\n\nPlease report this to jarcega@snaplogic.com")
