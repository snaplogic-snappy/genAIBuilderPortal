import streamlit as st
import requests
import time

def fetch_svg_from_api(url, token):
    """Fetch SVG content from API endpoint with attachment handling."""
    headers = {
        'Authorization': f'Bearer {token}',
        'Accept': '*/*'  # Accept any content type
    }
    
    try:
        response = requests.get(url, headers=headers, stream=True)
        response.raise_for_status()
        
        # Retrieve the entire SVG content
        svg_content = response.content.decode('utf-8')
        
        # Stream the content in chunks
        for i in range(0, len(svg_content), 100):
            yield svg_content[i:i+100]
            time.sleep(0.1)  # Simulate streaming
    
    except requests.RequestException as e:
        st.error(f"API Request Failed: {e}")
        st.error(f"Response headers: {response.headers}")

def main():
    st.title("SE Management Agents")
    
    api_url = "https://elastic.snaplogic.com/api/1/rest/slsched/feed/ConnectFasterInc/Matt%20Sager%27s%20Project%20Space/SE%20Team%20Mgmt/SEMonthlyActivitiesFetcher_Task"
    bearer_token = "12345"
    
    svg_placeholder = st.empty()
    
    # Collect and display full SVG
    full_svg = ""
    for svg_chunk in fetch_svg_from_api(api_url, bearer_token):
        full_svg += svg_chunk
        svg_placeholder.markdown(full_svg, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
