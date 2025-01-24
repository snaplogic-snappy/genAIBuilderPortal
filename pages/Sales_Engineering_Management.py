import streamlit as st
import requests

def fetch_svg_from_api(url, token):
    """Fetch SVG content from API endpoint."""
    headers = {
        'Authorization': f'Bearer {token}',
        'Accept': '*/*'
    }
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        return response.content.decode('utf-8')
    
    except requests.RequestException as e:
        st.error(f"API Request Failed: {e}")
        return None

def main():
    st.title("SE Management Agents")
    
    api_url = "https://elastic.snaplogic.com/api/1/rest/slsched/feed/ConnectFasterInc/Matt%20Sager%27s%20Project%20Space/SE%20Team%20Mgmt/SEMonthlyActivitiesFetcher_Task"
    bearer_token = "12345"  # Replace with actual token
    
    svg_content = fetch_svg_from_api(api_url, bearer_token)
    
    if svg_content:
        import streamlit.components.v1 as components
        components.html(svg_content, height=600)

if __name__ == "__main__":
    main()
