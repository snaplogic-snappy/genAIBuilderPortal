import streamlit as st
import requests
import json
import time
from dotenv import dotenv_values



# SnapLogic RAG pipeline
env = dotenv_values(".env")
URL = env["SL_CREC_TASK_URL"]
BEARER_TOKEN = env["SL_CREC_TASK_TOKEN"]
timeout = int(env["SL_TASK_TIMEOUT"])
# Streamlit Page Properties
page_title=env["CREC_PAGE_TITLE"]
title=env["CREC_TITLE"]


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
    
    ### This use-case is about doing Contract reconciliation between:
    - Digital version of a contract (PDF)
    - Contract data provisioned in the ERP/Billing System

    The specific pain that this use-case is solving is because the PDF contract contains pricing revision formula that are not always provisioned the right way in the ERP/Billing System. 
    The issues that can happen are the following:
    - the pricing revision formula is not applied at all => It means the initial price (P0) will never be increased
    - the pricing revision formula is wrong in the ERP
    Consequences: the customers are **underbilled**
    
    """
)
time.sleep(2.0)


with st.chat_message("assistant"):
    st.markdown("Welcome! 👋")

time.sleep(1.0)
with st.chat_message("assistant"):
    st.markdown("Select the PDF Contract to check against the ERP")
    
time.sleep(0.5)
uploaded_file = st.file_uploader(' ')
if uploaded_file is not None:
    file_bytes = uploaded_file.getvalue()
    with st.chat_message("assistant"):
        st.markdown("Successful Upload !")
    time.sleep(0.5)
    with st.chat_message("assistant"):
        st.markdown("Click below to launch the content comparison!")    
    if st.button(":blue[Analyze!]"):
        with st.spinner("Comparing PDF and ERP ..."):
            headers = {
                'Authorization': f'Bearer {BEARER_TOKEN}',
                'Content-Type': 'application/octet-stream'
            }
            response = requests.post(
                url=URL,
                data=file_bytes,
                headers=headers,
                timeout=timeout,
                verify=False
            )
            result = response.json()[0]["result"]
            message = f"Comparison completed for the contract N˚ **{result['pdf']['referenceClient']}** for customer **{result['pdf']['nomClient']}**"
            with st.chat_message("assistant"):
                typewriter(text=message,speed=10)
            time.sleep(1.0)
            with st.chat_message("assistant"):
                typewriter(text="Here's the result:", speed=10)
            if result["status"] == "OK":
                time.sleep(1.0)
                typewriter(text=f"✅ {result['message']}", speed=10)            
                time.sleep(1.0)
                typewriter(text="The price revision formula is the following:", speed=10)            
                time.sleep(1.0)
                st.latex(f"{result['pdf']['revisionFormulaPDF']}")
                time.sleep(1.0)
            elif result["status"] == "NOK_WRONG_FORMULA":
                    time.sleep(1.0)
                    st.error(f"❌ {result['message']}")            
                    typewriter(text="The price revision formula extracted from the PDF Contract is the following:", speed=10)
                    st.latex(f"{result['pdf']['revisionFormulaPDF']}")
                    typewriter(text="The price revision formula extracted from the ERP is the following:", speed=10)
                    st.latex(f"{result['erp']['revisionFormulaERP']}")
            elif result["status"] == "NOK_DISABLED_FORMULA":
                    time.sleep(1.0)
                    st.error(f"❌ {result['message']}")            
                    typewriter(text="The price revision formula extracted from the PDF Contract is the following:", speed=10)
                    st.latex(f"{result['pdf']['revisionFormulaPDF']}")
