


import streamlit as st
import requests
import time
from dotenv import dotenv_values

def fetch_svg_from_api(url, token):
    """Fetch SVG content from specified API endpoint."""
    headers = {
        'Authorization': f'Bearer {token}',
        'Accept': 'image/svg+xml'
    }
    
    try:
        response = requests.get(url, headers=headers, stream=True)
        response.raise_for_status()
        
        for chunk in response.iter_content(chunk_size=1024):
            if chunk:
                yield chunk.decode('utf-8')
                time.sleep(0.5)  # Simulated streaming delay
    
    except requests.RequestException as e:
        st.error(f"API Request Failed: {e}")

def main():
    st.title("SE Management Agents")
    
    api_url = "https://snaplogic.com/api/rest/1/blah"
    bearer_token = "12345"
    
    svg_placeholder = st.empty()
    
    for svg_chunk in fetch_svg_from_api(api_url, bearer_token):
        svg_placeholder.markdown(svg_chunk, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
