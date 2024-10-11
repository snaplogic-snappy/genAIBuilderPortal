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

fileOk = "https://snaplogic.box.com/s/vbdo1942zjm7fsxmdx9vizoojjs3uu6q"
fileMissing = "https://snaplogic.box.com/s/9v4sn7hmw8mugismmftwodnnmrx2p92z"
fileWrong = "https://snaplogic.box.com/s/ao0zdxjmhfbgwwzeb0ew26acbf6z6sxn"

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

    Sample files:
    - [Contract (OK)](https://snaplogic.box.com/s/vbdo1942zjm7fsxmdx9vizoojjs3uu6q)
    - [Contract (Missing formula in ERP)](https://snaplogic.box.com/s/9v4sn7hmw8mugismmftwodnnmrx2p92z)
    - [Download (Wrong formula in ERP)](https://snaplogic.box.com/s/ao0zdxjmhfbgwwzeb0ew26acbf6z6sxn)
    """
)

with st.chat_message("assistant"):
    st.markdown("Welcome! 👋")
with st.chat_message("assistant"):
    st.markdown("Select the PDF Contract")
uploaded_file = st.file_uploader(' ')
if uploaded_file is not None:
    file_bytes = uploaded_file.getvalue()
    with st.chat_message("assistant"):
        st.markdown("Successful Upload !Click below to launch the content comparison! ")
    if st.button(":blue[Analyze!]"):
        with st.spinner("Comparing Contract and ERP ..."):
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
                    time.sleep(1.0)
                    st.markdown("""<hr style="height:10px;border:none;color:#333;background-color:#333;" /> """, unsafe_allow_html=True)
                    c1, c2, c3 = st.columns(3)
                    with c1:
                        st.metric(label="Amount Billed by the ERP", value="462,39 €")
                    with c2:
                        st.metric(label="Amount to be billed from the contract", value="569,63 €")
                    with c3:
                        st.metric(label="Underbilled Amount", value="107,24 €")
            elif result["status"] == "NOK_DISABLED_FORMULA":
                    time.sleep(1.0)
                    st.error(f"❌ {result['message']}")            
                    typewriter(text="The price revision formula extracted from the PDF Contract is the following:", speed=10)
                    st.latex(f"{result['pdf']['revisionFormulaPDF']}")
