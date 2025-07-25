import streamlit as st
import requests

# --- Configuration and Password Protection ---

# Set page config as the first Streamlit command
st.set_page_config(page_title="RFI Assistant V2")

# Hardcoded password for simple access control
PASSWORD = "RFIbuddy"

# --- Main Application Logic ---

def run_rfi_assistant():
    """
    This function contains the entire chatbot application UI and logic.
    It only runs after the user has been authenticated.
    """
    # SnapLogic RAG pipeline - Updated API details
    URL = "https://emea.snaplogic.com/api/1/rest/slsched/feed/ConnectFasterInc/snapLogic4snapLogic/AutoRFPAgent/AgentDriverAutoRFPRefinerApi"
    BEARER_TOKEN = "FXHZg5dhK2JHlmQtN6GyUkycidMcXSGR" # Updated Authorization token
    TIMEOUT = 300

    st.title("Intelligent RFI Assistant V2")
    st.markdown("""
        ### AI-powered assistant for responding to Requests for Information (RFIs)
        Ask questions about your platform's capabilities – the assistant will analyze information from multiple knowledge sources to help you craft accurate and comprehensive RFI responses.

        **Sample queries:**
        - Is there an APIM policy for client throttling in SnapLogic?
        - Describe the elements of your platform that support the software development life cycle (SDLC), continuous integration and continuous delivery (CI/CD), and versioning.
        - How does your platform handle data governance and compliance?
        - What are the key security features of your platform?
    """)

    # Initialize chat history in session state
    if "rfi_v2_responses" not in st.session_state:
        st.session_state.rfi_v2_responses = []

    # Display chat messages from history on app rerun
    for message in st.session_state.rfi_v2_responses:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # React to user input, now with a unique key
    prompt = st.chat_input("Ask me anything about RFI requirements...", key="chat_widget")
    if prompt:
        # Display user message
        with st.chat_message("user"):
            st.markdown(prompt)
        # Add user message to chat history
        st.session_state.rfi_v2_responses.append({"role": "user", "content": prompt})

        with st.spinner("Analyzing sources and compiling response..."):
            # Construct the payload as required by the new API
            payload = {"metadata": {"question": prompt}}
            headers = {
                'Authorization': f'Bearer {BEARER_TOKEN}',
                'Content-Type': 'application/json'
            }

            try:
                # Post the request to the API endpoint
                response = requests.post(
                    url=URL,
                    json=payload,
                    headers=headers,
                    timeout=TIMEOUT,
                    verify=False
                )

                if response.status_code == 200:
                    try:
                        result = response.json()
                        if result and isinstance(result, list) and len(result) > 0 and isinstance(result[0], dict) and "response" in result[0]:
                            assistant_response_content = result[0]["response"]

                            with st.chat_message("assistant"):
                                st.markdown(assistant_response_content)
                            
                            st.session_state.rfi_v2_responses.append({"role": "assistant", "content": assistant_response_content})
                        else:
                            st.error("❌ Invalid response format from API. The expected 'response' key was not found.")
                    except ValueError:
                        st.error("❌ Failed to decode JSON from API response.")
                else:
                    st.error(f"❌ Error calling the API: Status Code {response.status_code}")
                    st.error(f"Response Body: {response.text}")

            except requests.exceptions.RequestException as e:
                st.error(f"❌ A network error occurred: {e}")


# --- Password Gate ---

# Initialize session state for authentication
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

# If not authenticated, show the password entry form
if not st.session_state.authenticated:
    st.title("Login Required")
    st.write("Please enter the password to access the RFI Assistant.")
    
    # Password input with a unique key
    password_input = st.text_input("Password", type="password", key="password_widget")
    
    if st.button("Unlock"):
        if password_input == PASSWORD:
            # If password is correct, set authenticated state to True and rerun
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("The password you entered is incorrect. Please try again.")
else:
    # If authenticated, run the main chatbot app
    run_rfi_assistant()
