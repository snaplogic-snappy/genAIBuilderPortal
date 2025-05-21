import streamlit as st
import requests
import time
from dotenv import dotenv_values

# Load environment
env = dotenv_values(".env")
# SnapLogic RAG pipeline
URL = "https://emea.snaplogic.com/api/1/rest/slsched/feed/ConnectFasterInc/Nilesh/NEC_Offender_demo/OffenderAgent"
BEARER_TOKEN = "q4zlgg1iLWBqU871R4a4fvxzMcJIddhG"
timeout = 300

def typewriter(text: str, speed: int):
    tokens = text.split()
    container = st.empty()
    for index in range(len(tokens) + 1):
        curr_full_text = " ".join(tokens[:index])
        container.markdown(curr_full_text)
        time.sleep(1 / speed)

st.set_page_config(page_title="Young Offender Assistant")
st.title("Intelligent Young Offender Assistant")
st.markdown("""  
    ### AI-powered young offender assistant for exploring datasets
    Ask questions in natural language - the assistant will automatically refine queries to find accurate insights.
    
    Sample queries:
    - Are there patterns in meeting frequency and behavior improvement (as noted by case workers)?
    - Is there any trend in repeated violence or threats across meetings for the same offender?
    - What is the average duration between the first offense and the case resolution, and what factors influence this duration?
    - Do certain case workers or prisons have consistently different outcomes or notes in terms of progress?
    - How do discussion topics relate to outcomes for young offenders?
""")

# Initialize chat history and toggle states
if "data_analytics" not in st.session_state:
    st.session_state.data_analytics = []
if "toggle_states" not in st.session_state:
    st.session_state.toggle_states = {}

# Display chat messages from history
for idx, message in enumerate(st.session_state.data_analytics):
    with st.chat_message(message["role"]):
        if message["role"] == "assistant":
            st.markdown(message.get("answer", message.get("content", "")))
            if message.get("summary"):
                toggle_key = f"toggle_{idx}"
                if st.toggle("Show thinking process", False, key=toggle_key):
                    st.markdown("### Agent's Thought Process")
                    st.markdown(message["summary"])
        else:
            st.markdown(message["content"])

# React to user input
prompt = st.chat_input("Ask me anything about the offender data")
if prompt:
    st.chat_message("user").markdown(prompt)
    st.session_state.data_analytics.append({"role": "user", "content": prompt})
    with st.spinner("Working..."):
        data = {"prompt": prompt}
        headers = {'Authorization': f'Bearer {BEARER_TOKEN}'}
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
                if len(result) > 0 and isinstance(result[0], dict):
                    response_data = result[0]
                    answer = response_data.get("answer", "")
                    summary = response_data.get("summary", "")
                    
                    with st.chat_message("assistant"):
                        typewriter(text=answer, speed=10)
                        if summary:
                            toggle_key = f"toggle_{len(st.session_state.data_analytics)}"
                            if st.toggle("Show thinking process", False, key=toggle_key):
                                st.markdown("### Agent's Thought Process")
                                st.markdown(summary)
                    
                    st.session_state.data_analytics.append({
                        "role": "assistant",
                        "answer": answer,
                        "summary": summary
                    })
                else:
                    with st.chat_message("assistant"):
                        st.error("❌ Invalid response format from API")
            except ValueError:
                with st.chat_message("assistant"):
                    st.error("❌ Invalid JSON response from API")
        else:
            st.error("❌ Error while calling the SnapLogic API")
        st.rerun()
