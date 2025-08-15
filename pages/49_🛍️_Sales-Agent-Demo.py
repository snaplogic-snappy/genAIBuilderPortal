import streamlit as st
import requests
import warnings

# Suppress the InsecureRequestWarning from the requests library for demo purposes
warnings.filterwarnings("ignore", message="Unverified HTTPS request")

# --- Configuration ---

# Set the page configuration. This must be the first Streamlit command.
st.set_page_config(
    page_title="AI Sales Agent",
    page_icon="🤖"
)

# --- Main Application Logic ---

def run_sales_agent_app():
    """
    This function contains the entire chatbot application UI and logic
    for the AI Sales Agent.
    """
    # API details for the sandbox sales agent
    URL = "https://prodeu-connectfasterinc-cloud-fm.emea.snaplogic.io/api/1/rest/feed/run/task/ConnectFasterInc/snapLogic4snapLogic/AiInDataIntegration/RetrieverWinReportsApi"
    BEARER_TOKEN = "Xa5FsyL1nEIxykFxdpqgnJNY1dI7yFHD"
    TIMEOUT = 300

    st.title("AI Sales Agent 🤖")
    st.markdown("""
        ### Your intelligent partner for sales insights.
        Ask questions about our products, customer success stories, and competitive advantages. This assistant leverages our internal win reports to give you the edge you need.

        **You can ask things like:**
        - How have our company helped customers with our APIM product?
        - Give me a summary of our win against Competitor X for Customer Y.
        - What were the key business challenges for the TechNova Solutions project?
    """)

    # Initialize chat history in session state if it doesn't exist
    if "sales_agent_messages" not in st.session_state:
        st.session_state.sales_agent_messages = []

    # Display past chat messages from history
    for message in st.session_state.sales_agent_messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Capture user input from the chat widget
    prompt = st.chat_input("Ask about customer wins, product value, etc.", key="sales_chat_widget")
    if prompt:
        # Display the user's message in the chat
        with st.chat_message("user"):
            st.markdown(prompt)
        # Add the user's message to the chat history
        st.session_state.sales_agent_messages.append({"role": "user", "content": prompt})

        with st.spinner("Searching win reports and generating insights..."):
            # Construct the payload and headers as required by the API
            payload = {"prompt": prompt}
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
                    verify=False  # Disabled for this specific sandbox environment
                )

                # Check for a successful response
                if response.status_code == 200:
                    try:
                        result = response.json()
                        # Validate the structure of the JSON response
                        if result and isinstance(result, list) and len(result) > 0 and "response" in result[0]:
                            # Extract the main response text
                            assistant_response_content = result[0].get("response", "No response text found.")
                            # Extract the sources, if they exist
                            sources = result[0].get("sources", [])
                            
                            full_response = assistant_response_content
                            # If sources are found, format and append them to the response
                            if sources:
                                source_list = "\n- " + "\n- ".join(sources)
                                full_response += f"\n\n**Sources:**{source_list}"

                            # Display the assistant's full response
                            with st.chat_message("assistant"):
                                st.markdown(full_response)
                            
                            # Add the full response to the chat history
                            st.session_state.sales_agent_messages.append({"role": "assistant", "content": full_response})
                        else:
                            st.error("❌ Invalid response format from API. The expected 'response' key was not found.")
                    except ValueError:
                        st.error("❌ Failed to decode JSON from the API response.")
                else:
                    st.error(f"❌ Error calling API: Status Code {response.status_code}")
                    st.text(f"Response Body: {response.text}")

            except requests.exceptions.RequestException as e:
                st.error(f"❌ A network error occurred: {e}")

# --- Run Application ---
# Since no password is needed, we can call the main function directly.
if __name__ == "__main__":
    run_sales_agent_app()