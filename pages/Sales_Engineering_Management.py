


import streamlit as st
import requests
import time
from dotenv import dotenv_values

def fetch_svg_from_api(url, token):
    """Fetch SVG content from specified API endpoint with enhanced headers."""
    headers = {
        'Authorization': f'Bearer {token}',
        'Accept': 'image/svg+xml',
        'Content-Type': 'application/json'  # Add this if API expects JSON
    }
    
    try:
        response = requests.get(url, headers=headers, stream=True)
        response.raise_for_status()
        
        # Check content type to ensure it's SVG
        content_type = response.headers.get('Content-Type', '')
        if 'image/svg+xml' not in content_type:
            st.error(f"Unexpected content type: {content_type}")
            return
        
        # Stream SVG content
        for chunk in response.iter_content(chunk_size=1024):
            if chunk:
                yield chunk.decode('utf-8')
                time.sleep(0.5)  # Simulated streaming delay
    
    except requests.RequestException as e:
        st.error(f"API Request Failed: {e}")
        st.error(f"Response headers: {response.headers}")
        st.error(f"Response content: {response.text}")



def main():
    st.title("SE Management Agents")
    
    api_url = "https://elastic.snaplogic.com/api/1/rest/slsched/feed/ConnectFasterInc/Matt%20Sager%27s%20Project%20Space/SE%20Team%20Mgmt/SEMonthlyActivitiesFetcher_Task"
    bearer_token = "12345"
    
    svg_placeholder = st.empty()
    
    for svg_chunk in fetch_svg_from_api(api_url, bearer_token):
        svg_placeholder.markdown(svg_chunk, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
