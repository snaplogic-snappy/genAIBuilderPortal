import streamlit as st
import requests
import json
import time
from dotenv import dotenv_values

# Demo metadata for search and filtering
DEMO_METADATA = {
    "categories": ["Content"],
    "tags": ["RFI", "Testing", "Tools"]
}

# --- CONFIGURATION & PASSWORD ---
PASSWORD = "RFIbuddy"  # A simple, hardcoded password

# Set page config as the first Streamlit command
st.set_page_config(page_title="RFI Analyst Assistant")


# --- MAIN APPLICATION LOGIC ---
def run_rfi_assistant():
    """
    This function contains the entire chatbot application and only runs
    after the user has been authenticated.
    """
    # --- API & APP CONSTANTS ---
    URL = "https://prodeu-connectfasterinc-cloud-fm.emea.snaplogic.io/api/1/rest/feed-master/queue/ConnectFasterInc/snapLogic4snapLogic/ToolsAsApi/RetrieverAnalystRFIsApi"
    BEARER_TOKEN = "jPjAekEskIsx96xEmSqwzp5eJMtoCwqo"
    TIMEOUT = 300

    # --- HELPER FUNCTION ---
    def typewriter(text: str, speed: int = 50):
        """Displays text with a typewriter effect."""
        tokens = text.split()
        container = st.empty()
        for index in range(len(tokens) + 1):
            curr_full_text = " ".join(tokens[:index])
            container.markdown(curr_full_text)
            time.sleep(1 / speed)

    # --- PAGE SETUP ---
    st.title("🤖 RFI Analyst Assistant")
    st.markdown("""
        ### AI-powered assistant for exploring RFI documents
        Ask questions in natural language about SnapLogic's platform capabilities.

        **Sample questions:**
        - Describe the elements of your platform that support the software development life cycle (SDLC), continuous integration and continuous delivery (CI/CD), and versioning.
        - How does SnapLogic support data governance?
        - What are the platform's collaboration features for development teams?
        - Explain SnapLogic's integration with version control systems like Git.
    """)

    # --- CHAT INITIALIZATION ---
    if "rfi_chat" not in st.session_state:
        st.session_state.rfi_chat = []

    # --- DISPLAY CHAT HISTORY ---
    for idx, message in enumerate(st.session_state.rfi_chat):
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            if message.get("source"):
                toggle_key = f"toggle_{idx}"
                if st.toggle("Show Sources", key=toggle_key):
                    st.info(f"**Sources:** {message['source']}")

    # --- USER INPUT AND API CALL ---
    # Add a unique key to the chat_input to prevent duplicate widget errors
    if prompt := st.chat_input("Ask a question about SnapLogic's capabilities...", key="chat_widget"):
        # Add user message to chat history
        st.session_state.rfi_chat.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Display assistant response
        with st.chat_message("assistant"):
            with st.spinner("Analyzing documents..."):
                payload = {"Requirement": prompt}
                headers = {
                    'Authorization': f'Bearer {BEARER_TOKEN}',
                    'Content-Type': 'application/json'
                }

                try:
                    response = requests.post(
                        url=URL,
                        json=payload,
                        headers=headers,
                        timeout=TIMEOUT,
                        verify=False
                    )
                    response.raise_for_status()

                    result = response.json()
                    api_response = result.get("response", {})
                    answer = api_response.get("answer")
                    source = api_response.get("source")

                    if answer:
                        typewriter(text=answer)
                        if source:
                            toggle_key = f"toggle_{len(st.session_state.rfi_chat)}"
                            if st.toggle("Show Sources", key=toggle_key):
                                st.info(f"**Sources:** {source}")

                        # Add assistant response to chat history
                        st.session_state.rfi_chat.append({
                            "role": "assistant",
                            "content": answer,
                            "source": source
                        })
                    else:
                        st.error("❌ The API returned a response, but it did not contain an answer.")

                except requests.exceptions.HTTPError as http_err:
                    st.error(f"❌ HTTP Error: {http_err} - {response.text}")
                except requests.exceptions.RequestException as e:
                    st.error(f"❌ Error calling the SnapLogic API: {e}")
                except ValueError:
                    st.error("❌ Could not decode the JSON response from the API.")

# --- PASSWORD GATE ---
# Initialize session state for authentication
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

# If not authenticated, show the password entry form
if not st.session_state.authenticated:
    st.title("Login Required")
    st.write("Please enter the password to access the RFI Assistant.")

    # Add a unique key to the password input to prevent duplicate widget errors
    password_input = st.text_input("Password", type="password", key="password_widget")

    if st.button("Unlock"):
        if password_input == PASSWORD:
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("The password you entered is incorrect. Please try again.")
else:
    # If authenticated, run the main chatbot application
    run_rfi_assistant()
