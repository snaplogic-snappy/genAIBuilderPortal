import streamlit as st
import requests
import time
from dotenv import dotenv_values

# Load environment variables (if you have them, otherwise remove this line)
# env = dotenv_values(".env")

# SnapLogic RAG pipeline - Updated API details
URL = "https://prodeu-connectfasterinc-cloud-fm.emea.snaplogic.io/api/1/rest/feed-master/queue/ConnectFasterInc/snapLogic4snapLogic/ToolsAsApi/RetrieverAnalystRFIsApi"
BEARER_TOKEN = "jPjAekEskIsx96xEmSqwzp5eJMtoCwqo" # Updated Authorization token
timeout = 300

def typewriter(text: str, speed: int):
    tokens = text.split()
    container = st.empty()
    for index in range(len(tokens) + 1):
        curr_full_text = " ".join(tokens[:index])
        container.markdown(curr_full_text)
        time.sleep(1 / speed)

st.set_page_config(page_title="RFI Assistant")
st.title("Intelligent RFI Assistant")
st.markdown("""
    ### AI-powered assistant for responding to Requests for Information (RFIs)
    Ask questions about your platform's capabilities – the assistant will retrieve relevant information from your knowledge base to help you craft accurate and comprehensive RFI responses.

    Sample queries:
    - Describe the elements of your platform that support the software development life cycle (SDLC), continuous integration and continuous delivery (CI/CD), and versioning.
    - How does your platform handle data governance and compliance?
    - What are the key security features of your platform?
    - Can you explain your platform's scalability options?
    - What reporting and analytics capabilities does your platform offer?
""")

# Initialize chat history, toggle states, and error message state
if "rfi_responses" not in st.session_state:
    st.session_state.rfi_responses = []
if "toggle_states" not in st.session_state:
    st.session_state.toggle_states = {}
if "error_message" not in st.session_state:
    st.session_state.error_message = None # To store persistent error messages

# Display chat messages from history
for idx, message in enumerate(st.session_state.rfi_responses):
    with st.chat_message(message["role"]):
        if message["role"] == "assistant":
            st.markdown(message.get("answer", message.get("content", "")))
            if message.get("source"): # Display source if available
                toggle_key = f"toggle_{idx}"
                if st.toggle("Show Source", False, key=toggle_key):
                    st.markdown("### Source Information")
                    st.markdown(message["source"])
        else:
            st.markdown(message["content"])

# Display persistent error message if one exists
if st.session_state.error_message:
    st.error(st.session_state.error_message)
    # Optionally clear the error after displaying, or leave it until next successful interaction
    # For this case, we'll clear it after the next user input
    # If you want it to stay until a new *successful* interaction, you'd clear it only after a successful API call.

# React to user input
prompt = st.chat_input("Ask me anything about RFI requirements...")
if prompt:
    # Clear any previous error messages when a new prompt is entered
    st.session_state.error_message = None

    st.chat_message("user").markdown(prompt)
    st.session_state.rfi_responses.append({"role": "user", "content": prompt})

    with st.spinner("Retrieving information..."):
        # Construct the payload as expected by the new API
        payload = [{"content": {"Requirement": prompt}}]
        headers = {
            'Authorization': f'Bearer {BEARER_TOKEN}',
            'Content-Type': 'application/json' # Specify content type for JSON payload
        }
        try:
            response = requests.post(
                url=URL,
                json=payload, # Use json parameter for automatic JSON serialization
                headers=headers,
                timeout=timeout,
                verify=False
            )

            # Check for successful HTTP status code (200 OK)
            if response.status_code == 200:
                try:
                    result = response.json()
                    # Check if the result is a dictionary and contains the 'response' key
                    if isinstance(result, dict) and "response" in result:
                        response_data = result["response"] # Access the nested 'response' dictionary directly
                        answer = response_data.get("answer", "")
                        source = response_data.get("source", "") # Extract source from response

                        with st.chat_message("assistant"):
                            typewriter(text=answer, speed=10)
                            if source:
                                toggle_key = f"toggle_{len(st.session_state.rfi_responses)}"
                                if st.toggle("Show Source", False, key=toggle_key):
                                    st.markdown("### Source Information")
                                    st.markdown(source)

                        st.session_state.rfi_responses.append({
                            "role": "assistant",
                            "answer": answer,
                            "source": source
                        })
                        # Clear error message on successful response
                        st.session_state.error_message = None
                    else:
                        error_msg = ("❌ Invalid response format from API. "
                                     "Expected a dictionary with a 'response' key.\n"
                                     f"**Raw API Response:** ```json\n{response.text}\n```")
                        st.session_state.error_message = error_msg

                except ValueError:
                    error_msg = ("❌ Invalid JSON response from API. "
                                 "The response could not be parsed as JSON.\n"
                                 f"**Raw API Response:** ```\n{response.text}\n```")
                    st.session_state.error_message = error_msg

            else:
                # Handle non-200 HTTP status codes
                error_message = f"❌ Error from API: Status Code {response.status_code}"
                try:
                    error_details = response.json()
                    if "error" in error_details:
                        error_message += f"\nDetails: {error_details['error']}"
                    elif "message" in error_details:
                        error_message += f"\nDetails: {error_details['message']}"
                    else:
                        error_message += f"\nResponse Body: ```json\n{response.text}\n```"
                except ValueError:
                    error_message += f"\nResponse Body: ```\n{response.text}\n```"

                st.session_state.error_message = error_message

        except requests.exceptions.Timeout:
            st.session_state.error_message = (
                f"❌ The API request timed out after {timeout} seconds. Please try again."
            )
        except requests.exceptions.ConnectionError as e:
            st.session_state.error_message = (
                f"❌ Connection Error: Could not connect to the API endpoint. "
                f"Please check your network and the API URL. Details: {e}"
            )
        except requests.exceptions.RequestException as e:
            st.session_state.error_message = (
                f"❌ An unexpected error occurred during the API request: {e}"
            )
        finally:
            st.rerun() # Rerun to display the stored error message or new content
