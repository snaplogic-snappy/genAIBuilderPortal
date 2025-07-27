import streamlit as st
import requests
import time
import json
from dotenv import dotenv_values

# Demo metadata for search and filtering
DEMO_METADATA = {
    "categories": ["Business"],
    "tags": ["Events", "Communication"]
}

# Constants for the API
URL = "https://emea.snaplogic.com/api/1/rest/slsched/feed/ConnectFasterInc/snapLogic4snapLogic/EventFollowUpAgent/EventFollowUpAgent"
BEARER_TOKEN = "2xKsMjjAGTwRJp4I4dltIiZQfUCL43Sv"
timeout = 300

st.set_page_config(page_title="Email Generator Assistant")
st.title("Email Generator Assistant")
st.markdown("""
### AI-powered follow-up email generator
Generate personalized follow-up emails based on event information and LinkedIn profiles.
""")

# Initialize session state for form values if they don't exist
if "prompt" not in st.session_state:
    st.session_state.prompt = "Please create a follow-up email for this event & individual"
if "event_url" not in st.session_state:
    st.session_state.event_url = ""
if "linkedin_profile_url" not in st.session_state:
    st.session_state.linkedin_profile_url = ""
if "employee_name" not in st.session_state:
    st.session_state.employee_name = ""
if "employee_email" not in st.session_state:
    st.session_state.employee_email = ""
if "response" not in st.session_state:
    st.session_state.response = ""
if "show_copy_message" not in st.session_state:
    st.session_state.show_copy_message = False

# Function to generate email
def generate_email():
    with st.spinner("Generating email..."):
        data = {
            "prompt": st.session_state.prompt,
            "input": {
                "event_url": st.session_state.event_url,
                "linkedin_profile_url": st.session_state.linkedin_profile_url,
                "employee_name": st.session_state.employee_name,
                "employee_email": st.session_state.employee_email
            }
        }
        
        headers = {
            'Authorization': f'Bearer {BEARER_TOKEN}',
            'Content-Type': 'application/json'
        }
        
        try:
            response = requests.post(
                url=URL,
                json=data,
                headers=headers,
                timeout=timeout
            )
            
            if response.status_code == 200:
                try:
                    result = response.json()
                    if "response" in result:
                        st.session_state.response = result["response"]
                    else:
                        st.error("❌ Invalid response format from API")
                except ValueError:
                    st.error("❌ Invalid JSON response from API")
            else:
                st.error(f"❌ Error while calling the API: {response.status_code}")
        except Exception as e:
            st.error(f"❌ Exception occurred: {str(e)}")

# Function to handle copy button click
def copy_button_clicked():
    st.session_state.show_copy_message = True

# Create form
with st.form(key="email_form"):
    st.text_area("Prompt", value=st.session_state.prompt, height=150, key="prompt")
    
    col1, col2 = st.columns(2)
    with col1:
        st.text_input("Event URL", key="event_url")
        st.text_input("LinkedIn Profile URL", key="linkedin_profile_url")
    with col2:
        st.text_input("Employee Name", key="employee_name")
        st.text_input("Employee Email", key="employee_email")
    
    submit_button = st.form_submit_button(label="Generate Email")
    
    if submit_button:
        generate_email()

# Display response
if st.session_state.response:
    st.subheader("Generated Email")
    
    # Display editable text area with the response
    response_text = st.text_area("", value=st.session_state.response, height=400, key="email_response")
    
    # Update the response in session state when edited
    if response_text != st.session_state.response:
        st.session_state.response = response_text
    
    # Add a copy button
    if st.button("Copy Text", key="copy_button"):
        st.session_state.show_copy_message = True
    
    # Show copy message if button was clicked
    if st.session_state.show_copy_message:
        st.info("📋 To copy: Press Ctrl+A (or Cmd+A) to select all text, then Ctrl+C (or Cmd+C)")
