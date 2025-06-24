import streamlit as st
import requests
import json

# Initialize chat history with welcome message
def init_session_state():
    if "messages" not in st.session_state:
        welcome_message = """👋 **Welcome to the Blog Agent !**"""

        st.session_state.messages = [{"role": "assistant", "content": welcome_message}]

# Initialize session state
init_session_state()

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Handle user input
prompt = st.chat_input("What is your question?")

if prompt:
    # Display user message
    with st.chat_message("user"):
        st.markdown(prompt)

    # Add user message to history
    st.session_state.messages.append({"role": "user", "content": prompt})

    # Process the request
    api_url = "https://elastic.snaplogic.com/api/1/rest/slsched/feed/SLoS_Dev/Blog_Agent/orchestration/proxy_agent%20Task?bearer_token=OzFfTJzroC5O4sKFUBZ48FUqdVqgmd1k"

    # Prepare payload
    payload = {
        "messages": st.session_state.messages,
        "current_message": prompt
    }

    # Add uploaded file data if available
    if "uploaded_file_data" in st.session_state:
        payload["file"] = st.session_state.uploaded_file_data

    # Show thinking message and process request
    with st.chat_message("assistant"):
        thinking_placeholder = st.empty()
        thinking_placeholder.markdown("Thinking...")

        try:
            # Make API call
            response = requests.post(api_url, json=payload, timeout=300)

            if response.status_code == 200:
                try:
                    api_response = response.json()
                    if isinstance(api_response, list) and len(api_response) > 0:
                        first_item = api_response[0]
                        if isinstance(first_item, dict):
                            bot_response = first_item.get("response", str(first_item))
                        else:
                            bot_response = str(first_item)
                    elif isinstance(api_response, dict):
                        bot_response = api_response.get("response", str(api_response))
                    else:
                        bot_response = str(api_response)
                except json.JSONDecodeError:
                    bot_response = response.text
            else:
                bot_response = f"Sorry, I encountered an error (Status: {response.status_code}). Please try again."

        except requests.exceptions.Timeout:
            bot_response = "Sorry, the request timed out. Please try again."
        except requests.exceptions.RequestException as e:
            bot_response = f"Sorry, I couldn't connect to the service. Error: {str(e)}"
        except Exception as e:
            bot_response = f"An unexpected error occurred: {str(e)}"

        # Replace thinking message with actual response
        thinking_placeholder.markdown(bot_response)
