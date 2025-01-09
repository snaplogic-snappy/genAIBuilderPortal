import streamlit as st
import requests
import time
import json

# Configuration
URL = "https://emea.snaplogic.com/api/1/rest/slsched/feed/ConnectFasterInc/snapLogic4snapLogic/LinkedinAgent/linkedinPostGenerator"
BEARER_TOKEN = "wiQo4jZU3ZWz8DooozDBiQzIztsZGZXV"
TIMEOUT = 180

def typewriter(text: str, speed: int):
    tokens = text.split()
    container = st.empty()
    for index in range(len(tokens) + 1):
        curr_full_text = " ".join(tokens[:index])
        container.markdown(curr_full_text)
        time.sleep(1 / speed)

# Page configuration
st.set_page_config(page_title="LinkedIn Post Generator", layout="wide")
st.title("LinkedIn Post Generator")

# App description
st.markdown(
    """
    ### AI-powered LinkedIn Post Generator
    Create engaging LinkedIn posts with AI assistance. You can optionally upload a document 
    to use as a source of information for your post.
    
    Sample prompts:
    - Create a post about our new product launch
    - Write a thought leadership post about AI in enterprise
    - Generate a post highlighting our recent customer success
    - Create an engaging post about industry trends
    """
)

# File upload
uploaded_file = st.file_uploader("Upload a document (optional)", type=['txt', 'pdf', 'docx'])
if uploaded_file is not None:
    st.success("File uploaded successfully!")

# Initialize chat history
if "linkedin_generator" not in st.session_state:
    st.session_state.linkedin_generator = []

# Display chat messages from history on app rerun
for message in st.session_state.linkedin_generator:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# React to user input
prompt = st.chat_input("Enter your post requirements")

if prompt:
    # Display user message
    st.chat_message("user").markdown(prompt)
    st.session_state.linkedin_generator.append({"role": "user", "content": prompt})
    
    with st.spinner("Generating post..."):
        # Prepare the request data
        data = {"prompt": prompt}
        
        # If a file was uploaded, add it to the request
        if uploaded_file is not None:
            file_content = uploaded_file.read()
            # Convert to base64 if it's binary content
            if isinstance(file_content, bytes):
                import base64
                encoded_content = base64.b64encode(file_content).decode('utf-8')
                data["document"] = encoded_content
                data["filename"] = uploaded_file.name  # Add filename to help with file type detection
            else:
                data["document"] = file_content
        
        # Make API request
        headers = {
            'Authorization': f'Bearer {BEARER_TOKEN}',
            'Content-Type': 'application/json'
        }
        
        try:
            # Add prompt as query parameter
            url_with_params = f"{URL}?PROMPT={requests.utils.quote(prompt)}"
            
            # Set up basic headers
            headers = {
                'Authorization': f'Bearer {BEARER_TOKEN}'
            }
            
            # If there's a file, send it as raw bytes with octet-stream
            if uploaded_file is not None:
                headers['Content-Type'] = 'application/octet-stream'
                file_bytes = uploaded_file.getvalue()
                response = requests.post(
                    url=url_with_params,
                    data=file_bytes,
                    headers=headers,
                    timeout=TIMEOUT
                )
            else:
                # No file, just send empty request with prompt in URL
                response = requests.post(
                    url=url_with_params,
                    headers=headers,
                    timeout=TIMEOUT
                )
            
            if response.status_code == 200:
                try:
                    result = response.json()
                    if isinstance(result, list) and len(result) > 0 and "content" in result[0]:
                        post_content = result[0]["content"]
                        
                        # Display the generated post in a nice format
                        with st.chat_message("assistant"):
                            st.markdown("### Generated LinkedIn Post")
                            st.markdown("---")
                            typewriter(text=post_content, speed=30)
                            
                            # Add copy button
                            st.markdown("---")
                            if st.button("📋 Copy to clipboard"):
                                st.write("Post copied to clipboard!")
                                st.session_state["clipboard"] = post_content
                        
                        st.session_state.linkedin_generator.append({
                            "role": "assistant",
                            "content": post_content
                        })
                    else:
                        st.error("❌ Invalid response format from API")
                except ValueError:
                    st.error("❌ Invalid JSON response from API")
            else:
                st.error(f"❌ Error while calling the API: {response.status_code}")
        except requests.exceptions.RequestException as e:
            st.error(f"❌ Request failed: {str(e)}")
        
        st.rerun()
