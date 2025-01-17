import streamlit as st
import requests
import json
import time
from dotenv import dotenv_values

# Environment config
env = dotenv_values(".env")
URL = "https://emea.snaplogic.com/api/1/rest/slsched/feed/ConnectFasterInc/snapLogic4snapLogic/AutoRecruiter/reviewCv"
BEARER_TOKEN = "JoY01uLt3hRe3fu9YpVKooJmhbhInfPi"
timeout = 120
page_title = "CV Screening Tool"
title = "CV Screening Tool"

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
    ### CV Analysis Tool
    This tool helps analyze candidate CVs against open positions by:
    - Analyzing CV content against job requirements
    - Evaluating experience level match
    - Assessing territorial fit
    """
)

with st.chat_message("assistant"):
    st.markdown("Please select the CV (PDF format)")

roles = ["Sales Engineer", "Solutions Architect", "Account Executive", "Customer Success Manager"]
seniorities = ["Junior", "Mid-level", "Senior", "Principal"]
territories = ["DACH", "UK&I", "Southern Europe", "Nordics"]

role = st.selectbox('Select Role', roles)
seniority = st.selectbox('Select Seniority Level', seniorities)
#territory = st.selectbox('Select Territory', territories)
territory = st.text_input('Territory description', value="", placeholder="DACH: Greenfield territory, 10 people including sales, presales, field marketing, BDR and channel. Need to hunt new logo and grow a few strategic accounts like Siemens and Syngenta.")

uploaded_file = st.file_uploader(' ')
if uploaded_file is not None:
    file_bytes = uploaded_file.getvalue()
    with st.chat_message("assistant"):
        st.markdown("CV uploaded successfully! Click below to analyze.")
    if st.button(":blue[Analyze CV]"):
        with st.spinner("Analyzing CV..."):
            headers = {
                'Authorization': f'Bearer {BEARER_TOKEN}',
                'Content-Type': 'application/octet-stream'
            }
            params = {
                'role': role,
                'seniority': seniority,
                'territory': territory
            }
            response = requests.post(
                url=URL,
                data=file_bytes,
                headers=headers,
                params=params,
                timeout=timeout,
                verify=False
            )
            result = response.json()
            
            with st.chat_message("assistant"):
                typewriter(text="Analysis complete. Here's the recommendation:", speed=10)
            
            sections = result["response"].split('\n')
            for section in sections:
                time.sleep(0.5)
                if section.startswith('Recommendation:'):
                    st.header(section)
                elif section.startswith('Reasoning:'):
                    st.subheader(section)
                elif section.strip().startswith(('1.', '2.', '3.', '4.')):
                    st.markdown(f"**{section}**")
                elif section.strip().startswith(('-', 'a)', 'b)', 'c)', 'd)')):
                    st.markdown(f"&nbsp;&nbsp;&nbsp;&nbsp;{section}")
                elif section.strip():
                    st.markdown(section)
