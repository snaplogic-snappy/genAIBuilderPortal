import streamlit as st
import requests
import json
import time
import os
from dotenv import dotenv_values



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

    """
)

with st.chat_message("assistant"):
    st.markdown("Bienvenue! 👋")

with st.chat_message("assistant"):
    st.markdown("Sélectionnez le contrat PDF à contrôler")
    
uploaded_file = st.file_uploader(' ')
if uploaded_file is not None:
    #file_bytes = uploaded_file.getvalue()
    #time.sleep(0.5)
    if st.button(":blue[Lancer le Contrôle!]"):
        with st.spinner("Contrôle en cours entre le SI et le Contrat PDF ..."):
            headers = {
                'Authorization': f'Bearer {BEARER_TOKEN}',
                'Content-Type': 'application/octet-stream'
            }
            response = requests.post(
                url=URL,
                #data=file_bytes,
                data=uploaded_file.getvalue(),
                headers=headers,
                timeout=timeout,
                verify=False
            )
            os.write(1, f"{response}\n".encode()) 
            result = response.json()[0]["result"]
            message = f"Contrôle terminé pour le contrat N˚ **{result['pdf']['referenceClient']}** pour le client **{result['pdf']['nomClient']}**"
            with st.chat_message("assistant"):
                typewriter(text=message,speed=10)
            with st.chat_message("assistant"):
                typewriter(text="Voici le résultat:", speed=10)
            if result["status"] == "OK":
                time.sleep(1.0)
                typewriter(text=f"✅ {result['message']}", speed=10)            
                time.sleep(1.0)
                typewriter(text="La formule de révision du prix est la suivante:", speed=10)            
                time.sleep(1.0)
                st.latex(f"{result['pdf']['revisionFormulaPDF']}")
                time.sleep(1.0)
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
                    #typewriter(text="Le montant actuellement facturé est: 462,39 €. Le montant à facturer devrait être: 569,63 €", speed=10)
                    #typewriter(text="Le client est sous-facturé à la hauteur de : 107,24 €", speed=10)
                    
            elif result["status"] == "NOK_DISABLED_FORMULA":
                    time.sleep(1.0)
                    st.error(f"❌ {result['message']}")            
                    typewriter(text="La formule de révision du prix extraite du Contrat PDF est la suivante:", speed=10)
                    st.latex(f"{result['pdf']['revisionFormulaPDF']}")
