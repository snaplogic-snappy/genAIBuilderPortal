import streamlit as st
import requests
import time
# from dotenv import dotenv_values # Uncomment if you plan to use a .env file for credentials

# --- Configuration for Trello Companion Chatbot ---
# API Endpoint for the SnapLogic Trello Companion
SNAPLOGIC_API_URL = "https://emea.snaplogic.com/api/1/rest/slsched/feed/ConnectFasterInc/snapLogic4snapLogic/SKO/TrelloCompagnon"
# Authorization Bearer Token
SNAPLOGIC_BEARER_TOKEN = "NGiulqIhjld6sv1M2ne4L6htn9hO3xDt"
# API request timeout in seconds
API_TIMEOUT = 300

def typewriter_effect(text: str, speed: int = 10):
    """Displays text with a typewriter effect in Streamlit."""
    tokens = text.split()
    container = st.empty()
    for i in range(len(tokens) + 1):
        current_text = " ".join(tokens[:i])
        container.markdown(current_text)
        time.sleep(1 / speed)

# --- Streamlit Page Setup ---
st.set_page_config(page_title="Trello Companion Chatbot")
st.title("🤖 Your Trello Companion")
st.markdown(
    """
    ### Your AI-powered assistant for managing Trello!
    Ask me to create cards, update lists, manage boards, and more, all using natural language.
    I'll interact with Trello on your behalf via SnapLogic.

    **For example, you can ask:**
    - "Create a new card titled 'Discuss Q3 budget' in the 'Meetings' list on the 'Team Sync' board."
    - "Can you list all my Trello boards?"
    - "What are the lists on the 'Project Phoenix' board?"
    - "Move the card 'Finalize report' from 'To Do' to 'Done' on the 'Sprint Tasks' board."
    """
)

# --- Chat History Initialization ---
CHAT_HISTORY_KEY = "trello_companion_chat_history"
if CHAT_HISTORY_KEY not in st.session_state:
    st.session_state[CHAT_HISTORY_KEY] = []

# --- Display Past Chat Messages ---
for idx, message in enumerate(st.session_state[CHAT_HISTORY_KEY]):
    with st.chat_message(message["role"]):
        # Display the main answer or content (internally stored as "answer")
        st.markdown(message.get("answer") or message.get("content", ""))

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
user_prompt = st.chat_input("How can I help with Trello today?")

if user_prompt:
    st.session_state[CHAT_HISTORY_KEY].append({"role": "user", "content": user_prompt})
    with st.chat_message("user"):
        st.markdown(user_prompt)

    with st.chat_message("assistant"):
        with st.spinner("Working on your Trello request... 🛠️"):
            api_payload = {"prompt": user_prompt}
            api_headers = {"Authorization": f"Bearer {SNAPLOGIC_BEARER_TOKEN}"}
            assistant_message_content = {} 

            try:
                response = requests.post(
                    url=SNAPLOGIC_API_URL,
                    json=api_payload,
                    headers=api_headers,
                    timeout=API_TIMEOUT,
                    verify=False,
                )
                response.raise_for_status()

                api_response_json = response.json()

                if isinstance(api_response_json, list) and api_response_json:
                    assistant_response_data = api_response_json[0]
                elif isinstance(api_response_json, dict):
                    assistant_response_data = api_response_json
                else:
                    raise ValueError("Unexpected API response format.")

                # --- THIS IS THE CORRECTED LINE ---
                # The API response uses the key "response" for the main text.
                # We'll store it in our 'answer' variable for internal use.
                answer_from_api = assistant_response_data.get("response", "Sorry, I couldn't understand the response from Trello service.")
                summary_from_api = assistant_response_data.get("summary", "")

                typewriter_effect(answer_from_api)
                # Internally, we still call the main text "answer" for consistency in chat history structure
                assistant_message_content = {"role": "assistant", "answer": answer_from_api, "summary": summary_from_api}

            except requests.exceptions.HTTPError as http_err:
                error_message_detail = response.text if 'response' in locals() and response else 'No response details'
                error_message = f"❌ Trello API Error: {http_err} - {error_message_detail}"
                st.error(error_message)
                assistant_message_content = {"role": "assistant", "content": error_message}
            except requests.exceptions.RequestException as req_err:
                error_message = f"❌ Connection Error: {req_err}"
                st.error(error_message)
                assistant_message_content = {"role": "assistant", "content": error_message}
            except ValueError as json_err: # Handles JSON decoding errors or unexpected format
                error_message_detail = response.text if 'response' in locals() and response else 'N/A'
                error_message = f"❌ API Response Error: Could not decode JSON or unexpected format. {json_err}. Raw response: {error_message_detail}"
                st.error(error_message)
                assistant_message_content = {"role": "assistant", "content": error_message}
            except Exception as e:
                error_message = f"❌ An unexpected error occurred: {e}"
                st.error(error_message)
                assistant_message_content = {"role": "assistant", "content": error_message}
            
            if assistant_message_content:
                st.session_state[CHAT_HISTORY_KEY].append(assistant_message_content)

    st.rerun()
