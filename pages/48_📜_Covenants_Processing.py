import streamlit as st
import requests
import time
from dotenv import dotenv_values


# Load environment
env = dotenv_values(".env")
# SnapLogic RAG pipeline
URL = env["SL_CA_TASK_URL"]
BEARER_TOKEN = env["SL_CA_TASK_TOKEN"]
timeout = int(env["SL_TASK_TIMEOUT"])
#namespace = env["SL_DI_TASK_NAMESPACE"]
# Streamlit Page Properties
page_title=env["CA_PAGE_TITLE"]
title=env["CA_TITLE"]


def typewriter(text: str, speed: int):
    tokens = text.split()
    container = st.empty()
    for index in range(len(tokens) + 1):
        curr_full_text = " ".join(tokens[:index])
        container.markdown(curr_full_text)
        time.sleep(1 / speed)

st.set_page_config(page_title=page_title)
st.title(title)

st.markdown(
    """  
    ### 👋 **Welcome to the Covenants Processing Agent!**

I'm here to help you work through the Covenants workflow.

**What I can help you with:**
- ✅ Extract and confirm company details from the Compliance Statement (PDF) and Covenant Rental Schedule (XLS)
- 📄 Process uploaded documents like Application Forms to extract relevant data
- ⚠️ Detect and report any data discrepancies
- 📋 Run through the complete Covenants process efficiently

**To get started:**
- Ask me questions about the company or the Covenants process
- I'll run the necessary processes for you
""")

# Initialize chat history
if "dealer_invoices" not in st.session_state:
    st.session_state.dealer_invoices = []

# Display chat messages from history on app rerun
for message in st.session_state.dealer_invoices:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# React to user input
prompt = st.chat_input("Ask me anything")
if prompt:
    st.chat_message("user").markdown(prompt)
    # Add user message to chat history
    st.session_state.dealer_invoices.append({"role": "user", "content": prompt})
    with st.spinner("Working..."):
        #params={'namespace': namespace}
        data = {"prompt" : prompt}
        headers = {
            'Authorization': f'Bearer {BEARER_TOKEN}'
        }
        response = requests.post(
            url=URL,
            #params=params,
            data=data,
            headers=headers,
            timeout=timeout,
            verify=False
        )

        if response.status_code==200:
            result = response.json()
            if len(result) > 0:
                response_text = result[0]
                
                # Ensure we have a string for the typewriter function
                if isinstance(response_text, dict):
                    # If the response is a dict, extract the text field
                    # Adjust the key name based on your API response structure
                    response_text = response_text.get('text', '') or response_text.get('content', '') or str(response_text)
                elif not isinstance(response_text, str):
                    # Convert to string if it's not already
                    response_text = str(response_text)
                
                # Display assistant response in chat message container
                with st.chat_message("assistant"):
                    typewriter(text=response_text, speed=10)
                # Add assistant response to chat history
                st.session_state.dealer_invoices.append({"role": "assistant", "content": response_text})
            else:
                with st.chat_message("assistant"):
                    st.error(f"❌ Error in the SnapLogic API response: Empty Result")
        else:
            with st.chat_message("assistant"):
                st.error(f"❌ Error while calling the SnapLogic API: {response.status_code}")
        st.rerun()
