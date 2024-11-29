import streamlit as st
import requests
import time
from dotenv import dotenv_values

# Load environment
env = dotenv_values(".env")
# SnapLogic RAG pipeline
URL = "https://emea.snaplogic.com/api/1/rest/slsched/feed/ConnectFasterInc/snapLogic4snapLogic/SalesAssistant/callAgentWorkerSalesAssistant"
BEARER_TOKEN = "rsFZlA7hO5Ngp4loIH600cXHcKKluHYL"
timeout = 180

def typewriter(text: str, speed: int):
    tokens = text.split()
    container = st.empty()
    for index in range(len(tokens) + 1):
        curr_full_text = " ".join(tokens[:index])
        container.markdown(curr_full_text)
        time.sleep(1 / speed)

st.set_page_config(page_title="SnapLogic Sales Assistant")
st.title("SnapLogic Sales Assistant")
st.markdown(
    """  
    ### AI-powered sales assistant for SnapLogic employees
    Get instant answers to your sales-related questions, with references to official SnapLogic content.
    
    Sample queries:
    - What are SnapLogic's key differentiators against MuleSoft?
    - Create a customer facing documents with customer success stories in the healthcare industry
    - What's our pricing model for enterprise customers?
    - What ROI metrics can I share with prospects?
    - Find competitive analysis against Boomi for financial services
    - What's our partner program structure?
 """)

# Initialize chat history
if "sales_assistant" not in st.session_state:
    st.session_state.sales_assistant = []

# Display chat messages from history on app rerun
for message in st.session_state.sales_assistant:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# React to user input
prompt = st.chat_input("Ask me anything about SnapLogic sales")
if prompt:
    st.chat_message("user").markdown(prompt)
    st.session_state.sales_assistant.append({"role": "user", "content": prompt})
    with st.spinner("Working..."):
        data = {"prompt" : prompt}
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
            try:
                result = response.json()
                if "response" in result:
                    assistant_response = result["response"]
                    with st.chat_message("assistant"):
                        typewriter(text=assistant_response, speed=10)
                    st.session_state.sales_assistant.append({"role": "assistant", "content": assistant_response})
                else:
                    with st.chat_message("assistant"):
                        st.error("❌ Invalid response format from API")
            except ValueError:
                with st.chat_message("assistant"):
                    st.error("❌ Invalid JSON response from API")
        else:
            st.error(f"❌ Error while calling the SnapLogic API")
        st.rerun()
