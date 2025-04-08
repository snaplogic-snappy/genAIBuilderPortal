import streamlit as st
import requests
import time
import json
from dotenv import dotenv_values

# Load environment
env = dotenv_values(".env")
# SnapLogic pipeline
URL = "https://demo-fm.snaplogic.io/api/1/rest/feed/run/task/ConnectFasterInc/00_Bhavin%20Patel/GenAI/ExtractInsuranceDoc"
BEARER_TOKEN = "123456"
timeout = 90
# Streamlit Page Properties
page_title = 'Insurance Form/Document Agent'
title = 'Insurance Form/Document Agent'

def typewriter(text: str, speed: int):
    #text = "Insurance Form/Document Information : " + text + ",-------------------------------------------------------------"
    tokens = text.split()
    container = st.empty()
    for index in range(len(tokens) + 1):
        #curr_full_text = " ".join(tokens[:index])
        container.markdown(text)
        time.sleep(1 / speed)

st.set_page_config(page_title=page_title, layout="wide")
st.title(title)

st.markdown(
    """
    ### Insurance Document/Form Agent.
    Insurance Form Agent extracts Below Form Information. You can upload Text or Image PDF File.
    - Form/Document Type
    - Policy Information (Policy Number, Effective Date, Expiration Date)
    - General Liability Information (GL Aggregate, PCO Aggregate, Personal Injury & Advertising Injury, Each Occurrence, Damage to Rented Premises, Medical Expense, GL Liability)
    - Property Information (Property Limit, AOP Deductible, Wind/Hail Deductible)
    - Addition Deductibles
    - Total Premium
    """
)
# Initialize chat history
if "Binder_Extraction_messages" not in st.session_state:
    st.session_state.Binder_Extraction_messages = []

# Display chat messages from history on app rerun
for message in st.session_state.Binder_Extraction_messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# React to user input
with st.chat_message("assistant"):
    st.markdown("Upload an Insurance Form/Document PDF for Extraction.")

uploaded_file = st.file_uploader(' ')
if uploaded_file is not None:
    file_bytes = uploaded_file.getvalue()
    with st.chat_message("assistant"):
        st.markdown("Successful Upload! Click below to extract policy information! ")
    time.sleep(0.5)
    if st.button(":blue[Extract!]"):
        with st.spinner("Parsing and Extracting Policy Info from PDF ..."):
            headers = {
                'Authorization': f'Bearer {BEARER_TOKEN}',
                'Content-Type': 'application/octet-stream'
            }
            response = requests.post(
                url=URL,
                data=file_bytes,
                headers=headers,
                timeout=180
            )
        print(response)
        result = response.json()
        response = result[0]['response']
        # Display assistant response in chat message container
        with st.chat_message("assistant"):
            typewriter(text=response, speed=10)
        # Add assistant response to chat history
        st.session_state.Binder_Extraction_messages.append({"role": "assistant", "content": response.replace("{", "").replace("}", "").replace(",", " ")})
