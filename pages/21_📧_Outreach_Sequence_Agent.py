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

def parse_email_sequence(response_data):
    try:
        if isinstance(response_data, str):
            data = json.loads(response_data)
        else:
            data = response_data
            
        email_sequence = data.get('response', {}).get('email_sequence', [])
        if not email_sequence:
            st.error("No email sequence found in response")
            return None
            
        return sorted(email_sequence, key=lambda x: int(x['email_number']))
    except Exception as e:
        st.error(f"Error processing response: {str(e)}")
        st.write("Debug - Response data:", response_data)
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

# Display chat history
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
                emails = parse_email_sequence(result)
                if emails:
                    st.session_state.sequence_generator.append({
                        "role": "assistant",
                        "emails": emails,
                        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
                    })
                else:
                    st.error("❌ Could not parse email sequence from response")
                    st.write("Debug - Raw response:", result)
            except Exception as e:
                st.error(f"❌ Error processing response: {str(e)}")
                st.write("Response content:", response.text)
        else:
            st.error(f"❌ Error calling API (Status {response.status_code})")
            st.write("Response content:", response.text)
        
        st.rerun()
