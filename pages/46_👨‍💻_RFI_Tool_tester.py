import streamlit as st
import requests
import time
from dotenv import dotenv_values

# --- Configuration and Password Protection ---

# Set page config as the first Streamlit command
st.set_page_config(page_title="RFI Assistant")

# Hardcoded password for simple access control
PASSWORD = "RFIbuddy"

# --- Helper Function ---

def typewriter(text: str, speed: int):
    """Displays text with a typewriter effect."""
    tokens = text.split()
    container = st.empty()
    for index in range(len(tokens) + 1):
        curr_full_text = " ".join(tokens[:index])
        container.markdown(curr_full_text)
        time.sleep(1 / speed)

# --- Main Application Logic ---

def run_rfi_assistant():
    """
    This function contains the entire chatbot application UI and logic.
    It only runs after the user has been authenticated.
    """
    # Load environment variables (if you have them, otherwise remove this line)
    env = dotenv_values(".env")

    # SnapLogic RAG pipeline - Updated API details
    URL = "https://prodeu-connectfasterinc-cloud-fm.emea.snaplogic.io/api/1/rest/feed-master/queue/ConnectFasterInc/snapLogic4snapLogic/ToolsAsApi/RetrieverAnalystRFIsApi"
    BEARER_TOKEN = "jPjAekEskIsx96xEmSqwzp5eJMtoCwqo" # Updated Authorization token
    timeout = 300
    
    st.title("Intelligent RFI Assistant")
    st.markdown("""
        ### AI-powered assistant for responding to Requests for Information (RFIs)
        Ask questions about your platform's capabilities – the assistant will retrieve relevant information from your knowledge base to help you craft accurate and comprehensive RFI responses.

        Sample queries:
        - Describe the elements of your platform that support the software development life cycle (SDLC), continuous integration and continuous delivery (CI/CD), and versioning.
        - How does your platform handle data governance and compliance?
    """)

    # Initialize chat history and toggle states
    if "rfi_responses" not in st.session_state:
        st.session_state.rfi_responses = []
    if "toggle_states" not in st.session_state:
        st.session_state.toggle_states = {}

    # Display chat messages from history
    for idx, message in enumerate(st.session_state.rfi_responses):
        with st.chat_message(message["role"]):
            if message["role"] == "assistant":
                st.markdown(message.get("answer", message.get("content", "")))
                if message.get("source"): # Display source if available
                    toggle_key = f"toggle_{idx}"
                    if st.toggle("Show Source", value=False, key=toggle_key):
                        st.markdown("### Source Information")
                        st.markdown(message["source"])
            else:
                st.markdown(message["content"])

    # React to user input with a unique key
    prompt = st.chat_input("Ask me anything about RFI requirements...", key="chat_widget")
    if prompt:
        st.chat_message("user").markdown(prompt)
        st.session_state.rfi_responses.append({"role": "user", "content": prompt})
        
        with st.spinner("Retrieving information..."):
            payload = [{"content": {"Requirement": prompt}}]
            headers = {
                'Authorization': f'Bearer {BEARER_TOKEN}',
                'Content-Type': 'application/json'
            }
            try:
                response = requests.post(
                    url=URL,
                    json=payload,
                    headers=headers,
                    timeout=timeout,
                    verify=False
                )
                if response.status_code == 200:
                    try:
                        result = response.json()
                        if len(result) > 0 and isinstance(result[0], dict) and "response" in result[0]:
                            response_data = result[0]["response"]
                            answer = response_data.get("answer", "No answer found.")
                            source = response_data.get("source", "No source provided.")

                            with st.chat_message("assistant"):
                                typewriter(text=answer, speed=10)
                                if source:
                                    # This toggle needs a unique key for each message
                                    source_toggle_key = f"toggle_source_{len(st.session_state.rfi_responses)}"
                                    if st.toggle("Show Source", value=False, key=source_toggle_key):
                                        st.markdown("### Source Information")
                                        st.markdown(source)

                            st.session_state.rfi_responses.append({
                                "role": "assistant",
                                "answer": answer,
                                "source": source
                            })
                        else:
                             st.error("❌ Invalid response format from API.")
                    except ValueError:
                        st.error("❌ Invalid JSON response from API")
                else:
                    st.error(f"❌ API Error: Status Code {response.status_code}")
                    st.error(f"Response: {response.text}")
            except requests.exceptions.RequestException as e:
                st.error(f"❌ A network error occurred: {e}")
        st.rerun()

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
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("The password you entered is incorrect. Please try again.")
else:
    # If authenticated, run the main chatbot app
    run_rfi_assistant()