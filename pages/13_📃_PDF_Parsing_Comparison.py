import streamlit as st
import requests
import time


def typewriter(text: str, speed: int):
    tokens = text.split()
    container = st.empty()
    for index in range(len(tokens) + 1):
        curr_full_text = " ".join(tokens[:index])
        container.markdown(curr_full_text)
        time.sleep(1 / speed)


st.set_page_config(page_title="GenAI Builder - Chatbot")
st.title("PDF Parsing Comparison")
st.markdown(
    """

    ### This use-case is about parsing and summarising PDFs.
    This bot will process PDFs using 3 different techniques:
    
    *Methods 1 and 2 are suitable for small PDFs, but become inefficient with larger documents.*
    1. Parsing the entire PDF to text, and providing that to the LLM
    2. Parsing the entire PDF to images, and providing that to the LLM **(WIP)**
    3. Vectorising the PDF in a vector DB, and querying that via the LLM **(WIP)**
    """
)
# Initialize chat history
if "PDF_Parsing_messages" not in st.session_state:
    st.session_state.PDF_Parsing_messages = []

# Display chat messages from history on app rerun
for message in st.session_state.PDF_Parsing_messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# React to user input
with st.chat_message("assistant"):
    st.markdown("Upload a PDF to summarise")

uploaded_file = st.file_uploader(' ')
if uploaded_file is not None:
    file_bytes = uploaded_file.getvalue()
    with st.chat_message("assistant"):
        st.markdown("Successful Upload! Click below to summarize the document! ")
    time.sleep(0.5)
    if st.button(":blue[Summarize!]"):
        with st.spinner("Parsing and summarizing PDF ..."):
            URL = 'https://emea.snaplogic.com/api/1/rest/slsched/feed/ConnectFasterInc/Joe/shared/GenAIDocumentSummary%20Task'
            BEARER_TOKEN = 'Hca25iyvXsgyeh6ec2b8a0HBo9VHdJeu'
            headers = {
                'Authorization': f'Bearer {BEARER_TOKEN}',
                'Content-Type': 'application/octet-stream'
            }
            response = requests.post(
                url=URL,
                data=file_bytes,
                headers=headers,
                timeout=180,
                verify=False
            )

        result = response.json()
        # st.write(result)
        response = (
            """
            | Method 1 (Text parsing)    | Method 2 (Image parsing) | Method 3 (Vector Search) |
            | -------- | ------- | ------- |
            | """+result[0]["parseToTextResult"]["content"]+"""  | """+result[0]["parseToImageResult"]["content"]+"""     | """+result[0]["vectorQueryResult"]["content"]+"""     |
            """
        )
        # Display assistant response in chat message container
        with st.chat_message("assistant"):
            st.markdown(response,unsafe_allow_html=True)
            # typewriter(text=response, speed=10)

        # Add assistant response to chat history
        st.session_state.PDF_Parsing_messages.append({"role": "assistant", "content": response})
