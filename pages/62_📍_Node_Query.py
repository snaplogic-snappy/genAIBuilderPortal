import streamlit as st
import requests
import time
from dotenv import dotenv_values

# Demo metadata for search and filtering
DEMO_METADATA = {
    "categories": ["Business"],
    "tags": ["Invoices", "Automotive", "Finance"]
}

# Load environment
env = dotenv_values(".env")
# SnapLogic RAG pipeline
URL = env["https://emea.snaplogic.com/api/1/rest/slsched/feed/ConnectFasterInc/Nilesh/GenAI/FNT_Retriever_Task"]
BEARER_TOKEN = env["S6PxXMLihJ9nW67N2NeW9UfZJvsnZlET"]
timeout = int(env["SL_TASK_TIMEOUT"])
#namespace = env["SL_DI_TASK_NAMESPACE"]
# Streamlit Page Properties
page_title=env["DI_PAGE_TITLE"]
title=env["DI_TITLE"]


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
    ### FNT Node Operational Health Assistant
    Ask questions about node health, stability, change history, and operational risk across the network estate.

    **Examples**
    - Which nodes are currently in a CRITICAL health state and how long have they been that way?
    - Rank the top 5 most unstable nodes and explain what makes them risky.
    - Which team has made the most changes across the estate, and to which nodes?
    - Are there any nodes with high alert counts but still showing OK health status?
    - Classify all nodes by lifecycle maturity — newly deployed, stable, actively evolving, or aging.
    - Which nodes have been touched by multiple different teams? Does this correlate with poor health?
    - Are there any ACTIVE nodes with no change history at all?
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
            if len(result) > 0 :
                response=result[0]
                # Display assistant response in chat message container
                with st.chat_message("assistant"):
                    typewriter(text=response, speed=10)
                # Add assistant response to chat history
                st.session_state.dealer_invoices.append({"role": "assistant", "content": response})
            else:
                with st.chat_message("assistant"):
                    st.error(f"❌ Error in the SnapLogic API response: Empty Result")
        else:
                st.error(f"❌ Error while calling the SnapLogic API")
        st.rerun()
