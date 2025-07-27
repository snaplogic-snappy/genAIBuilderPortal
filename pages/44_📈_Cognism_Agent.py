import streamlit as st
import requests
import time
from dotenv import dotenv_values

# Demo metadata for search and filtering
DEMO_METADATA = {
    "categories": ["Content"],
    "tags": ["Cognism", "Data", "Analytics"]
}

# --- Configuration for Cognism Agent Chatbot ---
# API Endpoint for the SnapLogic Cognism Agent
SNAPLOGIC_API_URL = "https://prodeu-connectfasterinc-cloud-fm.emea.snaplogic.io/api/1/rest/feed/run/task/ConnectFasterInc/Agent%20Creator/Cognism/AgentDriverCognismApi"
# Authorization Bearer Token
SNAPLOGIC_BEARER_TOKEN = "PJDXT4AeqMJWWshmG2GGKNQsUJ5glia7"
# API request timeout in seconds
API_TIMEOUT = 300

def typewriter_effect(text: str, speed: int = 50):
    """Displays text with a typewriter effect in Streamlit."""
    tokens = text.split()
    container = st.empty()
    for i in range(len(tokens) + 1):
        current_text = " ".join(tokens[:i])
        container.markdown(current_text)
        time.sleep(1 / speed)

# --- Streamlit Page Setup ---
st.set_page_config(page_title="Cognism Account Search")
st.title("🤖 Cognism Account Search Agent")
st.markdown(
    """
    ### Your AI-powered assistant for finding company accounts!
    Ask me to search for companies, and I'll find them using the Cognism database via a SnapLogic API.

    **For example, you can ask:**
    - "Search for the account Coca-Cola"
    - "Find tech companies in London"
    - "Who are the main competitors of Salesforce?"
    """
)

# --- Chat History Initialization ---
CHAT_HISTORY_KEY = "cognism_agent_chat_history"
if CHAT_HISTORY_KEY not in st.session_state:
    st.session_state[CHAT_HISTORY_KEY] = []

# --- Display Past Chat Messages (with Summary Toggle) ---
for idx, message in enumerate(st.session_state[CHAT_HISTORY_KEY]):
    with st.chat_message(message["role"]):
        # Display the main response content
        st.markdown(message.get("answer") or message.get("content", ""))

        # If the message is from the assistant and has a summary, show a toggle
        if message["role"] == "assistant" and message.get("summary"):
            toggle_key = f"summary_toggle_{idx}"
            show_summary = st.toggle(
                "Show agent's process",
                key=toggle_key,
            )
            if show_summary:
                st.markdown("--- \n**Agent's Process:**")
                st.markdown(message["summary"])


# --- Handle User Input ---
user_prompt = st.chat_input("How can I help you find accounts today?")

if user_prompt:
    st.session_state[CHAT_HISTORY_KEY].append({"role": "user", "content": user_prompt})
    with st.chat_message("user"):
        st.markdown(user_prompt)

    with st.chat_message("assistant"):
        with st.spinner("Searching for accounts... 🕵️‍♂️"):
            # The API expects a list containing a dictionary.
            api_payload = [{"prompt": user_prompt}]
            api_headers = {"Authorization": f"Bearer {SNAPLOGIC_BEARER_TOKEN}"}
            assistant_message_content = {}

            try:
                response = requests.post(
                    url=SNAPLOGIC_API_URL,
                    json=api_payload,
                    headers=api_headers,
                    timeout=API_TIMEOUT,
                    verify=False, # Note: Disabling SSL verification, use with caution.
                )
                response.raise_for_status()

                api_response_json = response.json()

                # --- UPDATED RESPONSE HANDLING ---
                # The API returns a list, we need 'response' and 'summary' from the first item.
                if isinstance(api_response_json, list) and api_response_json:
                    assistant_response_data = api_response_json[0]
                    answer_from_api = assistant_response_data.get("response", "Sorry, I received an empty response from the service.")
                    summary_from_api = assistant_response_data.get("summary", "") # Extract the summary
                else:
                    raise ValueError("Unexpected API response format. Expected a list.")

                typewriter_effect(answer_from_api)
                
                # --- UPDATED MESSAGE STORAGE ---
                # Store both the answer and the summary in the session state
                assistant_message_content = {"role": "assistant", "answer": answer_from_api, "summary": summary_from_api}

            except requests.exceptions.HTTPError as http_err:
                error_message_detail = response.text if 'response' in locals() else 'No response details'
                error_message = f"❌ API Error: {http_err} - {error_message_detail}"
                st.error(error_message)
                assistant_message_content = {"role": "assistant", "content": error_message}
            except requests.exceptions.RequestException as req_err:
                error_message = f"❌ Connection Error: {req_err}"
                st.error(error_message)
                assistant_message_content = {"role": "assistant", "content": error_message}
            except (ValueError, IndexError) as format_err: # Handles JSON/format errors
                error_message_detail = response.text if 'response' in locals() else 'N/A'
                error_message = f"❌ API Response Error: Could not parse response or format is wrong. {format_err}. Raw response: {error_message_detail}"
                st.error(error_message)
                assistant_message_content = {"role": "assistant", "content": error_message}
            except Exception as e:
                error_message = f"❌ An unexpected error occurred: {e}"
                st.error(error_message)
                assistant_message_content = {"role": "assistant", "content": error_message}
            
            if assistant_message_content:
                st.session_state[CHAT_HISTORY_KEY].append(assistant_message_content)

    # Rerun the script to display the new message immediately
    st.rerun()
