import streamlit as st
import requests
from typing import Optional
import json
import re

def call_api(text: str, api_url: str, bearer_token: str, request_type: str, scipab_notes: Optional[dict] = None) -> Optional[str]:
    headers = {
        "Authorization": f"Bearer {bearer_token}",
        "Content-Type": "application/json"
    }
    data = {
        "prompt": text,
        "requestType": request_type
    }
    if scipab_notes:
        data["scipabNotes"] = scipab_notes

    try:
        response = requests.post(api_url, json=data, headers=headers)
        response.raise_for_status()
        return response.text
    except requests.exceptions.RequestException as e:
        st.error(f"API call failed: {e}")
        return None

def process_request(request_type: str, text_input: str, api_url: str, bearer_token: str, genre: str, tone: str, email: Optional[str] = None):
    if not text_input:
        st.warning("Please enter text notes.")
        return

    if not bearer_token:
        st.warning("Please enter your API token.")
        return

    # Extract genre and tone from the prompt if specified
    genre_match = re.search(r"genre:\s*(\w+)", text_input, re.IGNORECASE)
    tone_match = re.search(r"tone:\s*(\w+)", text_input, re.IGNORECASE)

    if genre_match:
        extracted_genre = genre_match.group(1).capitalize()  # Capitalize for consistency
        if extracted_genre in ["Business", "Technical", "Educational"]:
            genre = extracted_genre
            st.write(f"Using genre from prompt: {genre}")
        else:
            st.warning(f"Invalid genre '{extracted_genre}' in prompt. Using default genre: {genre}")

    if tone_match:
        extracted_tone = tone_match.group(1).capitalize() # Capitalize for consistency
        if extracted_tone in ["Professional", "Conversational", "Tutorial"]:
            tone = extracted_tone
            st.write(f"Using tone from prompt: {tone}")
        else:
            st.warning(f"Invalid tone '{extracted_tone}' in prompt. Using default tone: {tone}")


    # Construct the prompt with genre and tone
    prompt = f"{text_input} genre:{genre}, tone:{tone}"

    scipab_notes = None
    if request_type == "Complete Blog":
        if st.session_state.scipab_content:  # Check if scipab_content exists
            scipab_notes = st.session_state.scipab_content.copy()
        else:
            scipab_notes = {}  # Initialize if it doesn't exist

        if email:
            scipab_notes["recipient"] = email

        # Update scipab_notes with values from text areas
        for key in ["situation", "complication", "implication", "position", "action", "benefit"]:
            scipab_notes[key] = st.session_state[key]

    with st.spinner("Processing..."):
        result = call_api(prompt, api_url, bearer_token, request_type, scipab_notes)

    if result:
        try:
            result_json = json.loads(result)
            response_data = result_json.get("response", {})
            st.session_state.scipab_content = response_data.get("scipab_content", {})

            if request_type == "Complete Blog":
                blog_url = result_json.get("blog_url")
                if blog_url:
                    st.success(f"Blog generated successfully! Blog URL: {blog_url}")
                else:
                    st.success("Blog generated successfully!")
            else:
                st.success("SCIPAB notes generated successfully!")

        except json.JSONDecodeError:
            st.error("Failed to parse API response. Raw response:")
            st.text(result)

def main():
    st.title("Blog Post Generator") # Changed header

    # Configuration inputs
    with st.sidebar:
        api_url = st.text_input("API URL", "https://emea.snaplogic.com/api/1/rest/slsched/feed/ConnectFasterInc/snapLogic4snapLogic/BlogWriterAgent/AgentBlogWriterTask")
        bearer_token = st.text_input("Bearer Token", "fY4hcH59Xy7FQbrjXiycPxch6PsmPADw", type="password")

    # Main interface
    st.write("")

    email_input = st.text_input("Recipient Email:", help="Enter the recipient's email address. Required for blog generation.")
    email_regex = r"[^@]+@[^@]+\.[^@]+"
    if email_input and not re.match(email_regex, email_input):
        st.error("Invalid email format. Please enter a valid email address.")
        valid_email = False
    else:
        valid_email = True

    genre = st.selectbox("Genre", ["Business", "Technical", "Educational"], index=0)
    tone = st.selectbox("Tone", ["Professional", "Conversational", "Tutorial"], index=0)

    text_input = st.text_area("Enter text notes:", height=150, placeholder="Please enter notes for your blog...  (Default genre: Business, tone: Professional). Example: 'Write a blog post about AI in healthcare, genre:Technical, tone:Tutorial'")

    if 'scipab_content' not in st.session_state:
        st.session_state.scipab_content = {}  # Initialize as empty dictionary

    # Initialize SCIPAB variables in session state
    for key in ["situation", "complication", "implication", "position", "action", "benefit"]:
        if key not in st.session_state:
            st.session_state[key] = ""

    if st.button("Generate SCIPAB notes"):
        process_request("SCIPAB Only", text_input, api_url, bearer_token, genre, tone)

    if st.button("Generate Blog"):
        if valid_email:  # Check email validity before proceeding
            process_request("Complete Blog", text_input, api_url, bearer_token, genre, tone, email_input)
        else:
            st.warning("Please enter a valid email address before generating the blog.")

    # Display the SCIPAB fields if content is available and only after SCIPAB notes have been generated
    if st.session_state.scipab_content:
        st.subheader("Generated SCIPAB Content (Verify before generating blog)")
        for key, value in st.session_state.scipab_content.items():
            st.text_area(key.capitalize() + ":", value=value, height=100, key=key)


if __name__ == "__main__":
    main()
