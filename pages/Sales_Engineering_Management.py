import streamlit as st
import requests

st.set_page_config(layout="wide")

def fetch_svg_from_api(url, token):
    """Fetch SVG content from API endpoint."""
    headers = {
        'Authorization': f'Bearer {token}',
        'Accept': '*/*'
    }
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        return response.text
    
    except requests.RequestException as e:
        st.error(f"API Request Failed: {e}")
        return None

def main():
    st.title("SE Management Dashboard (N.A.)")
    st.markdown('<p style="color:red;">Under Construction</p>', unsafe_allow_html=True)
    
    refresh_url = "https://elastic.snaplogic.com/api/1/rest/slsched/feed/ConnectFasterInc/Matt%20Sager%27s%20Project%20Space/SE%20Team%20Mgmt/AgentDriverSEActivities%20Task"
    api_url = "https://elastic.snaplogic.com/api/1/rest/slsched/feed/ConnectFasterInc/Matt%20Sager%27s%20Project%20Space/SE%20Team%20Mgmt/SEMonthlyActivitiesFetcher_Task"
    bearer_token = "12345"
    
    col1, col2 = st.columns([.6,.4])
    
    with col1:
        # Initial load of SVG content
        if 'svg_content' not in st.session_state:
            st.session_state.svg_content = fetch_svg_from_api(api_url, bearer_token)
        
        if st.button('Refresh'):
            with st.spinner('Refreshing data...'):
                # First API call
                refresh_response = requests.get(f"{refresh_url}?bearer_token={bearer_token}&reportType=monthly")
            with st.spinner('Fetching Data'):  
                # Second API call
                st.session_state.svg_content = fetch_svg_from_api(api_url, bearer_token)
        
        if st.session_state.svg_content:
            import streamlit.components.v1 as components
            components.html(st.session_state.svg_content, height=600, scrolling=True)
    with col2:
        reportType = "statsBySE"
              # Initial load of SVG content
        if 'svg_content' not in st.session_state:
            st.session_state.svg_content = fetch_svg_from_api(api_url?reportType, bearer_token)
        
        if st.button('Refresh'):
            with st.spinner('Refreshing data...'):
                # First API call
                refresh_response = requests.get(f"{refresh_url}?bearer_token={bearer_token}&reportType=monthly")
            with st.spinner('Fetching Data'):  
                # Second API call
                st.session_state.svg_content = fetch_svg_from_api(api_url, bearer_token)
        
        if st.session_state.svg_content:
            import streamlit.components.v1 as components
            components.html(st.session_state.svg_content, height=600, scrolling=True)
if __name__ == "__main__":
    main()
