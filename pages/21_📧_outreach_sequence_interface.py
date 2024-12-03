import streamlit as st
import requests
import time
import json
from dotenv import dotenv_values

# Load environment
env = dotenv_values(".env")
URL = "https://emea.snaplogic.com/api/1/rest/slsched/feed/ConnectFasterInc/snapLogic4snapLogic/OutreachSequenceAgent/EmailSequenceAgentApi"
BEARER_TOKEN = "Qdko51Jlb50v1RDz8lc5vBjMH7uli0tF"
timeout = 300

def typewriter(text: str, speed: int):
    tokens = text.split()
    container = st.empty()
    for index in range(len(tokens) + 1):
        curr_full_text = " ".join(tokens[:index])
        container.markdown(curr_full_text)
        time.sleep(1 / speed)

def parse_email_sequence(json_response):
    try:
        emails = []
        data = json.loads(json_response)
        for item in data:
            if isinstance(item, dict) and 'email_number' in item:
                emails.append(item)
        return sorted(emails, key=lambda x: int(x['email_number']))
    except:
        return None

st.set_page_config(page_title="Email Sequence Generator")
st.title("Email Sequence Generator")
st.markdown("""
    ### AI-powered email sequence generator
    Generate personalized email sequences for your outreach campaigns.
    
    Sample prompts:
    - Create a 5-email sequence for targeting CIOs about SnapLogic's API management capabilities
    - Generate an outreach sequence for healthcare IT leaders focusing on data integration
    - Design a follow-up sequence for prospects after a demo
""")

if "sequence_generator" not in st.session_state:
    st.session_state.sequence_generator = []

for message in st.session_state.sequence_generator:
    with st.chat_message(message["role"]):
        if message["role"] == "user":
            st.markdown(message["content"])
        else:
            emails = message.get("emails", [])
            if emails:
                for email in emails:
                    with st.expander(f"Email {email['email_number']}: {email['subject_line']}", expanded=False):
                        st.markdown("**Subject:** " + email['subject_line'])
                        st.markdown("**Purpose:** " + email['narrative_purpose'])
                        st.markdown("**Timing:** " + email['timing'])
                        st.markdown("**Body:**")
                        st.markdown(email['body'])
                        st.markdown("**Key Insight:** " + email['key_insight'])
                        st.markdown("**Call to Action:** " + email['call_to_action'])
                        if st.button(f"Copy Email {email['email_number']}", key=f"copy_{message['timestamp']}_{email['email_number']}"):
                            st.write('📋 Email content copied!')

prompt = st.chat_input("Describe the email sequence you need")
if prompt:
    st.chat_message("user").markdown(prompt)
    st.session_state.sequence_generator.append({
        "role": "user",
        "content": prompt,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    })
    
    with st.spinner("Generating sequence..."):
        data = {"prompt": prompt}
        headers = {'Authorization': f'Bearer {BEARER_TOKEN}'}
        response = requests.post(
            url=URL,
            headers=headers,
            data=data,
            timeout=timeout,
            verify=False
        )
        
        if response.status_code == 200:
            try:
                result = response.json()
                if "response" in result:
                    response_data = result["response"]
                    emails = parse_email_sequence(response_data)
                    
                    if emails:
                        st.session_state.sequence_generator.append({
                            "role": "assistant",
                            "emails": emails,
                            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
                        })
                    else:
                        st.error("❌ Could not parse email sequence from response")
                else:
                    st.error("❌ Invalid response format from API")
            except ValueError:
                st.error("❌ Invalid JSON response from API")
        else:
            st.error("❌ Error while calling the API")
        
        st.rerun()
