import streamlit as st
import requests
import json
import time
from dotenv import dotenv_values

# Demo metadata for search and filtering
DEMO_METADATA = {
    "categories": ["Business"],
    "tags": ["Finance", "Billing", "Reconciliation"]
}


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

tab1, tab2, tab3 = st.tabs([
    "✅ Contract OK",
    "⚠️ Contract with Missing formula in ERP",
    "❌ Contract with Wrong formula in ERP"
])

with tab1:
    if st.button("📄 See Contract OK"):
        st.pdf("Contract-Reconciliation-OK.pdf", height=800)

with tab2:
    if st.button("📄 See Contract with Missing formula in ERP"):
        st.pdf("Contract-Reconciliation-NOK-Formula-Not-Applied.pdf", height=800)

with tab3:
    if st.button("📄 See Contract with Wrong formula in ERP"):
        st.pdf("Contract-Reconciliation-NOK-Wrong-Formula-Applied.pdf", height=800)

st.divider()


with st.chat_message("assistant"):
    st.markdown("Select the PDF contract to check")

contract_type = st.radio(
    "Contract Type",
    (
        "Contract OK",
        "Contract with Missing formula in ERP",
        "Contract with Wrong formula in ERP",
    ),
)
file_map = {
    "Contract OK": "Contract-Reconciliation-OK.pdf",
    "Contract with Missing formula in ERP": "Contract-Reconciliation-NOK-Formula-Not-Applied.pdf",
    "Contract with Wrong formula in ERP": "Contract-Reconciliation-NOK-Wrong-Formula-Applied.pdf",
}

# --- Clear state if selection changes ---
if "last_contract_type" not in st.session_state:
    st.session_state.last_contract_type = contract_type
elif st.session_state.last_contract_type != contract_type:
    # Reset loaded contract when radio changes
    st.session_state.pop("contract_bytes", None)
    st.session_state.pop("contract_filename", None)
    st.session_state.last_contract_type = contract_type

# --- 1) Load the PDF once and persist it in session_state ---
if st.button("Load the selected contract", key="btn_load"):
    filepath = file_map[contract_type]
    try:
        with open(filepath, "rb") as f:
            file_bytes = f.read()
        st.session_state["contract_filename"] = filepath
        st.session_state["contract_bytes"] = file_bytes
        st.success(f"Contract loaded")
    except FileNotFoundError:
        st.error(f"Could not load the contract : {filepath}")

# --- 2) Only show the 'Lancer le Contrôle !' button if a contract is loaded ---
if "contract_bytes" in st.session_state:
    with st.chat_message("assistant"):
        st.markdown("Contract loaded. You can now run the check")
    if st.button(":blue[Run the check!]", key="btn_run"):
        with st.spinner("Comparing Contract and ERP ..."):
            headers = {
                'Authorization': f'Bearer {BEARER_TOKEN}',
                'Content-Type': 'application/octet-stream'
            }
            response = requests.post(
                url=URL,
                data=st.session_state["contract_bytes"],
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
                    time.sleep(1.0)
                    st.markdown("""<hr style="height:10px;border:none;color:#333;background-color:#333;" /> """, unsafe_allow_html=True)
                    c1, c2, c3 = st.columns(3)
                    with c1:
                        st.metric(label="Amount Billed by the ERP", value="2500,00 €")
                    with c2:
                        st.metric(label="Amount to be billed from the contract", value="3132,21 €")
                    with c3:
                        st.metric(label="Underbilled Amount", value="632,21 €")
                
