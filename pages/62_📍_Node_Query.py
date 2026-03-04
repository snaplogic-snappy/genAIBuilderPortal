import streamlit as st
import requests
import time

# ── Configuration ────────────────────────────────────────────────────────────
URL          = "https://emea.snaplogic.com/api/1/rest/slsched/feed/ConnectFasterInc/Nilesh/GenAI/FNT_Retriever_Task"
BEARER_TOKEN = "S6PxXMLihJ9nW67N2NeW9UfZJvsnZlET"
TIMEOUT      = 120
PAGE_TITLE   = "FNT Node Health"
TITLE        = "FNT Node Operational Health Assistant"
# ─────────────────────────────────────────────────────────────────────────────


def typewriter(text: str, speed: int):
    tokens = text.split()
    container = st.empty()
    for index in range(len(tokens) + 1):
        curr_full_text = " ".join(tokens[:index])
        container.markdown(curr_full_text)
        time.sleep(1 / speed)


st.set_page_config(page_title=PAGE_TITLE)
st.title(TITLE)

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
    """
)

# Initialise chat history
if "node_query_messages" not in st.session_state:
    st.session_state.node_query_messages = []

# Render existing chat messages
for message in st.session_state.node_query_messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Handle new user input
prompt = st.chat_input("Ask me anything")
if prompt:
    st.chat_message("user").markdown(prompt)
    st.session_state.node_query_messages.append({"role": "user", "content": prompt})

    with st.spinner("Working..."):
        headers = {"Authorization": f"Bearer {BEARER_TOKEN}"}
        data    = {"prompt": prompt}

        response = requests.post(
            url=URL,
            data=data,
            headers=headers,
            timeout=TIMEOUT,
            verify=False
        )

        if response.status_code == 200:
            result = response.json()
            if result:
                answer = result[0]
                with st.chat_message("assistant"):
                    typewriter(text=answer, speed=10)
                st.session_state.node_query_messages.append({"role": "assistant", "content": answer})
            else:
                st.error("❌ SnapLogic API returned an empty response.")
        else:
            st.error(f"❌ SnapLogic API error — HTTP {response.status_code}")

    st.rerun()