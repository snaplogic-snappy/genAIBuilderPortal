import streamlit as st
import requests
import time
import json # Keep json import for handling potential complex responses if needed

# --- Configuration ---

# Load Secrets (Ensure you have .streamlit/secrets.toml with SNAPLOGIC_API_BEARER_TOKEN)
try:
    BEARER_TOKEN = "jPjAekEskIsx96xEmSqwzp5eJMtoCwqo"
except KeyError:
    st.error("❗️ Error: SNAPLOGIC_API_BEARER_TOKEN not found in Streamlit Secrets. Please configure secrets.toml")
    st.stop() # Stop execution if the token is missing

# API Endpoint Details
URL = "https://prodeu-connectfasterinc-cloud-fm.emea.snaplogic.io/api/1/rest/feed-master/queue/ConnectFasterInc/snapLogic4snapLogic/ToolsAsApi/RetrieverSlackCrawlerApi"
API_TIMEOUT = 180 # seconds

# --- Helper Functions ---

def typewriter(text: str, speed: int):
    """Displays text with a typewriter effect."""
    tokens = text.split()
    container = st.empty()
    for index in range(len(tokens) + 1):
        curr_full_text = " ".join(tokens[:index])
        container.markdown(curr_full_text)
        time.sleep(1 / speed)

# --- Streamlit App ---

st.set_page_config(page_title="SnapLogic Tribal Knowledge Bot")
st.title("🧠 SnapLogic Tribal Knowledge Assistant")
st.markdown(
    """
    ### AI-powered assistant using SnapLogic's tribal knowledge (from Slack)
    Select the question type (Technical or Sales) and get answers based on internal discussions and expertise.

    **Sample Queries:**
    * *(Technical):* How do you configure dynamic account credentials in a REST GET Snap?
    * *(Technical):* What is the best practice for handling large file processing without memory issues?
    * *(Sales):* What are SnapLogic's key differentiators for ETL modernization projects?
    * *(Sales):* Provide a summary of recent customer wins in the retail sector.
    """
)

# Initialize chat history and question type in session state if they don't exist
if "tribal_knowledge_chat" not in st.session_state:
    st.session_state.tribal_knowledge_chat = []
if "question_type" not in st.session_state:
    st.session_state.question_type = "Technical" # Default selection

# Display chat messages from history on app rerun
for message in st.session_state.tribal_knowledge_chat:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- User Input Area ---

# Selector for question type - Added Radio Button
st.radio(
    "Select Question Type:",
    ("Technical", "Sales"),
    key="question_type", # Links widget to session state key
    horizontal=True,
    # index=0 is implicit default if key not in session_state, but we initialize above
    help="Choose the category your question falls into."
)

# React to user input - Updated placeholder text
prompt = st.chat_input(f"Ask a {st.session_state.question_type} question about SnapLogic...")

if prompt:
    # Display user message in chat message container
    with st.chat_message("user"):
        st.markdown(prompt)
    # Add user message to chat history
    st.session_state.tribal_knowledge_chat.append({"role": "user", "content": prompt})

    # --- API Call ---
    with st.spinner(f"Searching {st.session_state.question_type.lower()} knowledge..."):
        # Get question type from the radio button selection (stored in session state) - Updated logic
        question_type_selected = st.session_state.question_type.lower() # Convert to lowercase for API

        # Prepare data payload according to API specification
        data_payload = [{"Prompt": prompt, "type": question_type_selected}]

        # Prepare headers with Bearer token authentication
        headers = {
            'Authorization': f'Bearer {BEARER_TOKEN}',
            'Content-Type': 'application/json' # Important for sending JSON data
        }

        try:
            response = requests.post(
                url=URL,
                json=data_payload, # Use json parameter for automatic JSON serialization and Content-Type header
                headers=headers,
                timeout=API_TIMEOUT
            )

            # Check response status
            if response.status_code == 200:
                try:
                    result = response.json()
                    # Extract the response text - adjust based on actual API response structure
                    assistant_response = f"Sorry, I couldn't find an answer in the {st.session_state.question_type.lower()} knowledge base for that." # Default message
                    if isinstance(result, list) and len(result) > 0 and isinstance(result[0], dict) and "response" in result[0]:
                         assistant_response = result[0]["response"]
                    elif isinstance(result, dict) and "response" in result: # Handles direct dictionary response
                         assistant_response = result["response"]
                    elif isinstance(result, dict) and result.get("response") is None: # Handle case where key exists but value is null/None
                         assistant_response = f"The {st.session_state.question_type.lower()} knowledge base acknowledged the query but didn't provide a specific answer. Perhaps rephrase?"
                    else:
                        st.warning(f"⚠️ Unexpected API response format received: {result}") # Log unexpected format

                    # Display assistant response in chat message container with typewriter effect
                    with st.chat_message("assistant"):
                        typewriter(text=assistant_response, speed=30)
                    # Add assistant response to chat history
                    st.session_state.tribal_knowledge_chat.append({"role": "assistant", "content": assistant_response})

                except ValueError: # JSON decoding error
                    with st.chat_message("assistant"):
                        st.error("❌ Error: Could not decode the response from the API (Invalid JSON).")
                        st.caption(f"Raw Response: {response.text[:500]}...") # Show snippet of raw response for debugging
                    st.session_state.tribal_knowledge_chat.append({"role": "assistant", "content": "Sorry, I received an invalid response from the knowledge base."})
                except Exception as e: # Catch other potential errors during response processing
                     with st.chat_message("assistant"):
                        st.error(f"❌ Error processing API response: {e}")
                     st.session_state.tribal_knowledge_chat.append({"role": "assistant", "content": "Sorry, an error occurred while processing the response."})

            else: # Handle API errors (non-200 status codes)
                with st.chat_message("assistant"):
                    st.error(f"❌ Error calling API: Received status code {response.status_code}")
                    st.caption(f"Error Response: {response.text[:500]}...") # Show snippet of error response
                st.session_state.tribal_knowledge_chat.append({"role": "assistant", "content": f"Sorry, there was an error communicating with the knowledge base (Status: {response.status_code})."})

        except requests.exceptions.Timeout:
            with st.chat_message("assistant"):
                st.error(f"❌ Error: The request to the API timed out after {API_TIMEOUT} seconds.")
            st.session_state.tribal_knowledge_chat.append({"role": "assistant", "content": "Sorry, the request timed out. Please try again."})
        except requests.exceptions.RequestException as e:
            with st.chat_message("assistant"):
                st.error(f"❌ Error: A network or connection error occurred: {e}")
            st.session_state.tribal_knowledge_chat.append({"role": "assistant", "content": "Sorry, I couldn't connect to the knowledge base. Please check the connection or try again later."})

