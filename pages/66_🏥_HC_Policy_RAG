import re
import streamlit as st
import requests
import time
 
# ── Configuration ────────────────────────────────────────────────────────────
URL          = "https://uat.elastic.snaplogic.com/api/1/rest/slsched/feed/snaplogic/Ravi%20Krishnan/MKB/MKB_HC_Policies_AgenticRetieval%20Task"
BEARER_TOKEN = "12345"
TIMEOUT      = 120
PAGE_TITLE   = "Humana Healthcare Policy AI Agent"
TITLE        = "Humana Healthcare Policy AI Assistant"
# ─────────────────────────────────────────────────────────────────────────────
 
def typewriter(text: str, speed: int):
    # Split into words *while keeping whitespace* (including newlines) as
    # its own list items, instead of text.split() which discards all
    # whitespace/newlines. Re-joining with "".join(...) then reproduces the
    # original text exactly (markdown tables, headers, bullet lists, etc.)
    # rather than flattening everything onto one line.
    tokens = re.split(r"(\s+)", text)
    container = st.empty()
    for index in range(len(tokens) + 1):
        curr_full_text = "".join(tokens[:index])
        container.markdown(curr_full_text)
        time.sleep(1 / speed)
 
 
st.set_page_config(page_title=PAGE_TITLE)
st.title(TITLE)
 
st.markdown(
    """
    ### Humana Healhcare Policy AI Assistant
    Ask questions about Humana Policies.
 
    **Examples**
    - What policies have a annual benefit maximum of 5000?
    - What policies have a routine vision exam that is covered?
    - How does Humana Part D Work?
    - What are the Humana PDP Options?
    - What Humana policies cover Medicare Part A and Part B?
    - What is the difference between Plan G and High-Deductible Plan G?
    - What is the copay for HumanaChoice PPO plan?
    - What is included in the HumanaChoice PPO Plan?
    - How does the Humana Gold Plus HMO work?
    - What is the eligibility requirements for the Humana Gold Plus HMO?
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
prompt = st.chat_input("Ask me anything about Humana Policies")
 
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
                    # Case-insensitive lookup — the pipeline actually returns
                    # the key as "Response" (capital R), which is why the
                    # earlier lowercase-only .get() calls all missed it and
                    # fell through to the str(raw) fallback.
                    lower_map = {k.lower(): v for k, v in raw.items()}
                    answer = (
                        lower_map.get("response")
                        or lower_map.get("answer")
                        or lower_map.get("text")
                        or lower_map.get("content")
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
 
