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
                if st.toggle("Show Source", False, key=toggle_key):
                    st.markdown("### Source Information")
                    st.markdown(message["source"])
        else:
            st.markdown(message["content"])

# React to user input
prompt = st.chat_input("Ask me anything about RFI requirements...")
if prompt:
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
                    else:
                        with st.chat_message("assistant"):
                            st.error("❌ Invalid response format from API. Expected a dictionary with a 'response' key.")
                            st.markdown(f"**Raw API Response:** ```json\n{response.text}\n```") # Show raw response
                except ValueError:
                    with st.chat_message("assistant"):
                        st.error("❌ Invalid JSON response from API. The response could not be parsed as JSON.")
                        st.markdown(f"**Raw API Response:** ```\n{response.text}\n```") # Show raw response
            else:
                # Handle non-200 HTTP status codes
                error_message = f"❌ Error from API: Status Code {response.status_code}"
                try:
                    # Attempt to parse error message from JSON response
                    error_details = response.json()
                    if "error" in error_details: # Common pattern for API errors
                        error_message += f"\nDetails: {error_details['error']}"
                    elif "message" in error_details: # Another common pattern
                        error_message += f"\nDetails: {error_details['message']}"
                    else: # If a JSON response, but no clear error key
                        error_message += f"\nResponse Body: ```json\n{response.text}\n```"
                except ValueError:
                    # If response is not JSON, just show the raw text
                    error_message += f"\nResponse Body: ```\n{response.text}\n```"

                with st.chat_message("assistant"):
                    st.error(error_message)

        except requests.exceptions.Timeout:
            with st.chat_message("assistant"):
                st.error(f"❌ The API request timed out after {timeout} seconds. Please try again.")
        except requests.exceptions.ConnectionError as e:
            with st.chat_message("assistant"):
                st.error(f"❌ Connection Error: Could not connect to the API endpoint. Please check your network and the API URL. Details: {e}")
        except requests.exceptions.RequestException as e:
            with st.chat_message("assistant"):
                st.error(f"❌ An unexpected error occurred during the API request: {e}")
        finally:
            st.rerun()
