import streamlit as st
import requests
import urllib.parse
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
    #st.title("Sales Engineering Management Dashboard (North America)")
    st.markdown("<h2 style='font-size: 24px; color:#00A859; text-align: center;'>SE Management Dashboard (N.A.)</h2>", unsafe_allow_html=True)
    st.markdown('<p style="color:red;">Under Construction</p>', unsafe_allow_html=True)
    # Add a blinking subheading
    blinking_subheading = """
    <h4 style="color:#5F5F5F;text-align: center; animation: blink 1s step-start 3;">
        Powered by AgentCreator
    </h4>
    <style>
    @keyframes blink {
        50% { opacity: 0; }
    }
    </style>
    """
    st.markdown(blinking_subheading, unsafe_allow_html=True)
    
    
    refresh_url = "https://elastic.snaplogic.com/api/1/rest/slsched/feed/ConnectFasterInc/Matt%20Sager%27s%20Project%20Space/SE%20Team%20Mgmt/AgentDriverSEActivities%20Task"
    api_url = "https://elastic.snaplogic.com/api/1/rest/slsched/feed/ConnectFasterInc/Matt%20Sager%27s%20Project%20Space/SE%20Team%20Mgmt/SEMonthlyActivitiesFetcher_Task"
    bearer_token = "12345"
    
    col1, col2 = st.columns([.6,.4])
    
    with col1:
        params = {'reportType': 'monthlyRollup'}
        api_url_with_params = f"{api_url}?{urllib.parse.urlencode(params)}"
        # Initial load of SVG content
        if 'svg_content_col1' not in st.session_state:
            st.session_state.svg_content_col1 = fetch_svg_from_api(api_url_with_params, bearer_token)
        
        if st.button('Refresh', disabled=True):
            with st.spinner('Refreshing data...'):
                # First API call
                refresh_response = requests.get(f"{refresh_url}?bearer_token={bearer_token}&reportType=monthly")
            with st.spinner('Fetching Data'):  
                # Second API call
                st.session_state.svg_content_col1 = fetch_svg_from_api(api_url, bearer_token)
        
        if st.session_state.svg_content_col1:
            import streamlit.components.v1 as components
            components.html(st.session_state.svg_content_col1, height=500, scrolling=True)
        #2nd api call    
        params = {'reportType': 'monthlyProductPercentages'}
        api_url_with_params = f"{api_url}?{urllib.parse.urlencode(params)}"
              # Initial load of SVG content
        if 'svg_content_col1_second' not in st.session_state:
            st.session_state.svg_content_col1_second = fetch_svg_from_api(api_url_with_params, bearer_token)     
        if st.session_state.svg_content_col1_second:
            components.html(st.session_state.svg_content_col1_second, height=700, scrolling=True)
    with col2:
        params = {'reportType': 'statsBySE'}
        api_url_with_params = f"{api_url}?{urllib.parse.urlencode(params)}"
              # Initial load of SVG content
        if 'svg_content_col2' not in st.session_state:
            st.session_state.svg_content_col2 = fetch_svg_from_api(api_url_with_params, bearer_token)
        
        if st.button('Refreshx',disabled=True):
            with st.spinner('Refreshing data...'):
              #First API call
              refresh_response = requests.get(f"{refresh_url}?bearer_token={bearer_token}&reportType=monthly")
            with st.spinner('Fetching Data'):  
              # Second API call
              st.session_state.svg_content_col2 = fetch_svg_from_api(api_url, bearer_token)
        
        if st.session_state.svg_content_col2:
            import streamlit.components.v1 as components
            components.html(st.session_state.svg_content_col2, height=600, scrolling=True)


if __name__ == "__main__":
    main()
