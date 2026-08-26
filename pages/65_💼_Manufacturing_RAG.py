import streamlit as st
import requests
import time
 
# ── Configuration ────────────────────────────────────────────────────────────
URL          = "https://uat.elastic.snaplogic.com/api/1/rest/slsched/feed/snaplogic/Ravi%20Krishnan/MKB/GoldentTech_API"
BEARER_TOKEN = "12345"
TIMEOUT      = 120
PAGE_TITLE   = "Golden Technologies"
TITLE        = "Golden Products AI Assistant"
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
    ### Golden Product AI Assistant
    Ask questions about Golden Products.
 
    **Examples**
    - What is the UN number and transport hazard class for the 15Ah battery pack, and what special packing requirements apply when shipping it?
    - What conditions should be avoided with the 15Ah battery to prevent a hazardous reaction, and what are the hazardous decomposition products if it's exposed to those conditions?
    - What are the steps to install the power fuse on the Buzzaround CarryOn scooter, and what happens if it isn't installed?
    - In the fuse installation diagram, where does the fuse get moved from and to?
    - What is the maximum weight capacity and top speed of the GB120?
    - What is the GB120's operating range with the standard 15 AH battery versus the optional 6.5 AH battery?
    - What is the rated capacity, energy, and nominal voltage of the 12.5Ah battery pack?
    - What happens if the internal cell of the 12.5Ah battery pack is compromised, and what routes of exposure to the electrolyte can occur?
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
prompt = st.chat_input("Ask me anything about Golden Products")
 
if prompt:
    st.chat_message("user").markdown(prompt)
    st.session_state.node_query_messages.append({"role": "user", "content": prompt})
 
    with st.spinner("Working..."):
        headers = {"Authorization": f"Bearer {BEARER_TOKEN}"}
 
        # GET request — prompt is sent as the "Prompt" query string parameter,
        # e.g. .../GoldentTech_API?Prompt=What+are+the+tools+needed...
        # `params=` lets requests handle URL-encoding (spaces, punctuation, etc.)
        # instead of building the query string by hand.
        params = {"Prompt": prompt}
 
        response = requests.get(
            url=URL,
            params=params,
            headers=headers,
            timeout=TIMEOUT,
            verify=False
        )
 
        if response.status_code == 200:
            result = response.json()
 
            # DEBUG: uncomment this line to see the raw shape of the API
            # response while you're diagnosing the extraction below, then
            # remove/comment it out again once you know the correct shape.
            # st.write("DEBUG raw result:", result)
 
            if result:
                # The endpoint may not return a plain string in result[0] —
                # it can come back as a list item that's itself a dict, or
                # as a dict/object instead of a list. Handle each shape so
                # this doesn't crash with AttributeError on .split().
                raw = result[0] if isinstance(result, list) else result
 
                if isinstance(raw, str):
                    answer = raw
                elif isinstance(raw, dict):
                    # Try common key names a Snap might use for the answer
                    # text. Adjust/add keys here once you see the real
                    # shape via the DEBUG line above.
                    answer = (
                        raw.get("answer")
                        or raw.get("response")
                        or raw.get("text")
                        or raw.get("content")
                        or str(raw)
                    )
                else:
                    answer = str(raw)
 
                with st.chat_message("assistant"):
                    typewriter(text=answer, speed=10)
                st.session_state.node_query_messages.append({"role": "assistant", "content": answer})
            else:
                st.error("❌ SnapLogic API returned an empty response.")
        else:
            st.error(f"❌ SnapLogic API error — HTTP {response.status_code}")
 
    st.rerun()
 
