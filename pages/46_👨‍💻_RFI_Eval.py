import streamlit as st
import requests

# SnapLogic RAG pipeline - Updated API details
URL = "https://emea.snaplogic.com/api/1/rest/slsched/feed/ConnectFasterInc/snapLogic4snapLogic/AutoRFPAgent/AgentDriverAutoRFPRefinerApi"
BEARER_TOKEN = "FXHZg5dhK2JHlmQtN6GyUkycidMcXSGR" # Updated Authorization token
TIMEOUT = 300

# Page configuration
st.set_page_config(page_title="RFI Assistant V2")
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

# React to user input
prompt = st.chat_input("Ask me anything about RFI requirements...")
if prompt:
    # Display user message in chat message container
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
                verify=False  # Assuming SSL verification might be needed to be off
            )

            # Check for a successful response
            if response.status_code == 200:
                try:
                    result = response.json()
                    # Validate the structure of the JSON response
                    if result and isinstance(result, list) and len(result) > 0 and isinstance(result[0], dict) and "response" in result[0]:
                        # Extract the detailed markdown response
                        assistant_response_content = result[0]["response"]

                        # Display assistant response in chat message container
                        with st.chat_message("assistant"):
                            st.markdown(assistant_response_content)
                        
                        # Add assistant response to chat history
                        st.session_state.rfi_v2_responses.append({"role": "assistant", "content": assistant_response_content})

                    else:
                        st.error("❌ Invalid response format from API. The expected 'response' key was not found.")
                except ValueError:
                    st.error("❌ Failed to decode JSON from API response.")
            else:
                # Handle non-200 responses
                st.error(f"❌ Error calling the API: Status Code {response.status_code}")
                st.error(f"Response Body: {response.text}")

        except requests.exceptions.RequestException as e:
            st.error(f"❌ A network error occurred: {e}")

# The st.rerun() is implicitly handled by Streamlit's execution model
# when user input is received or state changes.