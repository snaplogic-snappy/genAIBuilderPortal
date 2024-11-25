import streamlit as st
import requests
import time
from dotenv import dotenv_values

# Load environment
env = dotenv_values(".env")
# SnapLogic RAG pipeline
URL = env["SL_UW_TASK_URL"]
BEARER_TOKEN = env["SL_UW_TASK_TOKEN"]
timeout = int(env["SL_TASK_TIMEOUT"])

def typewriter(text: str, speed: int):
    tokens = text.split()
    container = st.empty()
    for index in range(len(tokens) + 1):
        curr_full_text = " ".join(tokens[:index])
        container.markdown(curr_full_text)
        time.sleep(1 / speed)

st.set_page_config(page_title="Data Analytics Assistant")
st.title("Intelligent Data Analytics Assistant")
st.markdown(
    """  
    ### AI-powered analytics assistant for exploring datasets
    Currently analyzing TSA claims data. Ask questions in natural language - the assistant will automatically refine queries to find accurate insights.
    
    Sample queries:
    - What are the most common types of claims filed at major airports?
    - Show the trend of claim amounts over time in California
    - Compare average settlement amounts between different items
    - Which airports have the highest claim denial rates?
    - What's the seasonal pattern of electronics-related claims?
    - Analyze correlation between claim amounts and processing time
 """)

# Initialize chat history
if "data_analytics" not in st.session_state:
    st.session_state.data_analytics = []

# Display chat messages from history on app rerun
for message in st.session_state.data_analytics:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# React to user input
prompt = st.chat_input("Ask me anything about the TSA claims data")
if prompt:
    st.chat_message("user").markdown(prompt)
    st.session_state.data_analytics.append({"role": "user", "content": prompt})
    with st.spinner("Working..."):
        data = {"prompt": prompt}
        headers = {
            'Authorization': f'Bearer {BEARER_TOKEN}'
        }
        response = requests.post(
            url=URL,
            data=data,
            headers=headers,
            timeout=timeout,
            verify=False
        )
        if response.status_code == 200:
            result = response.json()
            if len(result) > 0:
                response = result[0]
                with st.chat_message("assistant"):
                    typewriter(text=response, speed=10)
                st.session_state.data_analytics.append({"role": "assistant", "content": response})
            else:
                with st.chat_message("assistant"):
                    st.error("❌ Error in the SnapLogic API response: Empty Result")
        else:
            st.error("❌ Error while calling the SnapLogic API")
        st.rerun()
