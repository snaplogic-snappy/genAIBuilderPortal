import streamlit as st
import requests
import json
import time
import os
from dotenv import dotenv_values

# Demo metadata for search and filtering
DEMO_METADATA = {
    "categories": ["Content"],
    "tags": ["Invoices", "French", "Reconciliation"]
}


# SnapLogic RAG pipeline
env = dotenv_values(".env")
URL = env["SL_CREC_TASK_URL"]
BEARER_TOKEN = env["SL_CREC_TASK_TOKEN"]
timeout = int(env["SL_TASK_TIMEOUT"])
# Streamlit Page Properties
page_title="Rapprochement de Factures"
title="Rapprochement et contrôle de cohérence entre les contrats et le SI Facturation"


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
    
    ### Ce cas d'usage concerne le rapprochement et contrôle de cohérence entre :
    - la version numérique d'un contrat (PDF)
    - les données du contrat fournies dans le SI/système de facturation.

    Le problème spécifique traité est que le contrat PDF contient des formules de révision de prix qui ne sont pas toujours provisionnées de la bonne manière dans le SI/système de facturation. 
    Les problèmes qui peuvent survenir sont les suivants
    - la formule de révision des prix n'est pas appliquée du tout => cela signifie que le prix initial (P0) ne sera jamais augmenté
    - la formule de révision des prix est erronée dans le SI/système de facturation
    
    Conséquence : les clients sont **sous-facturés**.
    
    Échantillons Contrats:
    """
)
with st.expander("Contrat conforme"):
    st.pdf("Contract-Reconciliation-OK.pdf")
with st.expander("Contrat dont la formule de révision est absente du SI"):
    st.pdf("Contract-Reconciliation-NOK-Formula-Not-Applied.pdf")
with st.expander("Contrat dont la formule de révision est erronée dans le SI"):
    st.pdf("Contract-Reconciliation-NOK-Wrong-Formula-Applied.pdf")

st.divider()

with st.chat_message("assistant"):
    st.markdown("Sélectionnez le contrat PDF à contrôler")

contract_type = st.radio(
    "Type de contrat",
    (
        "Contrat conforme",
        "Contrat dont la formule de révision est absente du SI",
        "Contrat dont la formule de révision est erronée dans le SI",
    ),
)
file_map = {
    "Contrat conforme": "Contract-Reconciliation-OK.pdf",
    "Contrat dont la formule de révision est absente du SI": "Contract-Reconciliation-NOK-Formula-Not-Applied.pdf",
    "Contrat dont la formule de révision est erronée dans le SI": "Contract-Reconciliation-NOK-Wrong-Formula-Applied.pdf",
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
if st.button("Charger le contrat sélectionné", key="btn_load"):
    filepath = file_map[contract_type]
    try:
        with open(filepath, "rb") as f:
            file_bytes = f.read()
        st.session_state["contract_filename"] = filepath
        st.session_state["contract_bytes"] = file_bytes
        st.success(f"Contrat chargé")
    except FileNotFoundError:
        st.error(f"Fichier introuvable : {filepath}")

# --- 2) Only show the 'Lancer le Contrôle !' button if a contract is loaded ---
if "contract_bytes" in st.session_state:
    with st.chat_message("assistant"):
        st.markdown("Contrat prêt. Vous pouvez lancer le contrôle.")
    #st.info("Contrat prêt. Vous pouvez lancer le contrôle.")
    if st.button(":blue[Lancer le Contrôle!]", key="btn_run"):
        try:
            with st.spinner("Contrôle en cours entre le SI et le Contrat PDF ..."):
                headers = {
                    "Authorization": f"Bearer {BEARER_TOKEN}",
                    "Content-Type": "application/octet-stream",
                }
                # Use bytes directly (simpler); a BytesIO works too but ensure pointer at 0 if reused.
                response = requests.post(
                    url=f"{URL}?lang=fr",
                    data=st.session_state["contract_bytes"],
                    headers=headers,
                    timeout=timeout,
                    verify=False,
                )
                response.raise_for_status()

                payload = response.json()
                # Defensive parsing
                result = payload[0]["result"] if isinstance(payload, list) else payload["result"]

            message = (
                f"Contrôle terminé pour le contrat N˚ **{result['pdf']['referenceClient']}** "
                f"pour le client **{result['pdf']['nomClient']}**"
            )
            with st.chat_message("assistant"):
                typewriter(text=message, speed=10)
            with st.chat_message("assistant"):
                typewriter(text="Voici le résultat:", speed=10)

            if result["status"] == "OK":
                time.sleep(1.0)
                typewriter(text=f"✅ {result['message']}", speed=10)
                time.sleep(1.0)
                typewriter(text="La formule de révision du prix est la suivante:", speed=10)
                time.sleep(1.0)
                st.latex(f"{result['pdf']['revisionFormulaPDF']}")

            elif result["status"] == "NOK_WRONG_FORMULA":
                time.sleep(1.0)
                st.error(f"❌ {result['message']}")
                typewriter(text="La formule de révision du prix extraite du Contrat PDF est la suivante:", speed=10)
                st.latex(f"{result['pdf']['revisionFormulaPDF']}")
                typewriter(text="La formule de révision du prix extraite du SI/système de facturation est la suivante", speed=10)
                st.latex(f"{result['erp']['revisionFormulaERP']}")
                time.sleep(1.0)
                st.markdown("""<hr style="height:10px;border:none;color:#333;background-color:#333;" /> """, unsafe_allow_html=True)
                c1, c2, c3 = st.columns(3)
                with c1:
                    st.metric(label="Montant Facturé par le SI", value="462,39 €")
                with c2:
                    st.metric(label="Montant à facturer selon le contrat", value="569,63 €")
                with c3:
                    st.metric(label="Montant sous-facturé", value="107,24 €")

            elif result["status"] == "NOK_DISABLED_FORMULA":
                time.sleep(1.0)
                st.error(f"❌ {result['message']}")
                typewriter(text="La formule de révision du prix extraite du Contrat PDF est la suivante:", speed=10)
                st.latex(f"{result['pdf']['revisionFormulaPDF']}")
                time.sleep(1.0)
                st.markdown("""<hr style="height:10px;border:none;color:#333;background-color:#333;" /> """, unsafe_allow_html=True)
                c1, c2, c3 = st.columns(3)
                with c1:
                    st.metric(label="Montant Facturé par le SI", value="2500,00 €")
                with c2:
                    st.metric(label="Montant à facturer selon le contrat", value="3132,21 €")
                with c3:
                    st.metric(label="Montant sous-facturé", value="632,21 €")

        except requests.HTTPError as e:
            st.error(f"Erreur HTTP: {e} – Détails: {getattr(e, 'response', None)}")
        except Exception as e:
            st.exception(e)
