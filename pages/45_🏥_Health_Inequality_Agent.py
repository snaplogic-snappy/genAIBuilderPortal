import streamlit as st
import requests
import time
import threading

# API details
API_URL = "https://emea.snaplogic.com/api/1/rest/slsched/feed/ConnectFasterInc/snapLogic4snapLogic/Bootcamp_EMEA_June_2025/story_clch_twoFiles%20Task"
HEADERS = {
    "Authorization": "Bearer ddWuVLmouogJVJIkexcddl9wAXH24aHM",
    "Content-Type": "application/json"
}

# Streamlit page config
st.set_page_config(page_title="Health Inequality: Asthma", page_icon="🤖")

# Centered logo with website link below
st.markdown(
    """
    <div style='text-align: center; padding-top: 10px; padding-bottom: 0px;'>
        <img src='https://allot.123-web.uk/wp-content/uploads/2018/12/logo-2.png' width='300'/>
        <div style='margin-top: 10px;'>
            <a href='https://www.allotltd.com/' target='_blank' style='text-decoration: none; font-size: 18px;'>www.allotltd.com</a>
        </div>
    </div>
    """,
    unsafe_allow_html=True
)

# App title and description
st.title("Health Inequality Report - Asthma")

st.markdown("""
**Overview**

This application offers an in-depth analysis of health inequalities related to asthma across England. It includes a comprehensive executive summary, a detailed assessment of asthma-related disparities, an exploration of the social and environmental factors contributing to these gaps, and a series of evidence-based recommendations aimed at reducing them.

**Data Limitations**

The data presented in this application centre on total patients, asthma patients, and prevalence segmented by GP practices and geographic regions. It also integrates Air Quality Index (annual mean PM2.5)data, acknowledging the critical role of air pollution as a contributing factor to asthma outcomes.

**Sample Questions**

1. Which five GP practices in Hertfordshire have the most asthma patients, and what are the best strategies for managing and controlling asthma?
2. Which GP practice in the England has the highest number of registered asthma patients? Please include the total patient population, the number of asthma patients, and the current air quality in that region?
3. What is the average asthma prevalence across each region, and what are the main barriers to effective asthma control in these areas?
""")



# Warning about the processing time
st.warning("""
⚠️ This process will take **up to 5 minutes** to return a result.

Why it takes time:
- Queries **external data sources** and applies **logic and analysis** on asthma prevalence and contributing factors like air quality and healthcare access.
- **Heavy processing and data integration** are handled by the Large Language Model behind the scenes for experimental purposes, which will take several minutes.
""")

# Initialize session state
if 'processing' not in st.session_state:
    st.session_state.processing = False
if 'result' not in st.session_state:
    st.session_state.result = None

# User question input
user_input = st.text_input("Ask a question:", placeholder="e.g., What are the asthma prevalence rates in different regions?")

# Button interaction
if st.button("Ask", disabled=st.session_state.processing):
    if not user_input.strip():
        st.warning("Please enter a question.")
    else:
        st.session_state.processing = True
        st.session_state.result = None
        st.rerun()

# Show loading indicator when processing
if st.session_state.processing:
    # Define cycling activities
    activities = [
        "🔍 Analyzing your question...",
        "📊 Connecting to health databases...",
        "🏥 Retrieving GP practice data...",
        "🌍 Fetching air quality measurements...",
        "📈 Calculating asthma prevalence rates...",
        "🗺️ Mapping regional disparities...",
        "🧠 Processing with AI models...",
        "📋 Cross-referencing healthcare access...",
        "🔬 Analyzing environmental factors...",
        "📝 Generating comprehensive insights...",
        "🎯 Formulating recommendations...",
        "✨ Finalizing your personalized report..."
    ]
    
    # Create centered loading indicator
    with st.container():
        # Center everything
        st.markdown("""
            <div style="display: flex; flex-direction: column; align-items: center; text-align: center; padding: 20px;">
                <div style="
                    border: 4px solid #f3f3f3;
                    border-top: 4px solid #ff6b6b;
                    border-radius: 50%;
                    width: 60px;
                    height: 60px;
                    animation: spin 1s linear infinite;
                    margin-bottom: 20px;
                "></div>
            </div>
            <style>
            @keyframes spin {
                0% { transform: rotate(0deg); }
                100% { transform: rotate(360deg); }
            }
            </style>
        """, unsafe_allow_html=True)
        
        status_placeholder = st.empty()
        
        # Show initial message and make API call
        import random
        current_activity = random.choice(activities)
        status_placeholder.markdown(f"<div style='text-align: center;'><h3>{current_activity}</h3><em>This may take 5-10 minutes...</em></div>", unsafe_allow_html=True)
        
        # Make the API call
        try:
            payload = {"Prompt": user_input}
            response = requests.post(API_URL, headers=HEADERS, json=payload)
            
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list) and len(data) > 0:
                    answer = data[0].get("Customer_Story", "No answer received.")
                else:
                    answer = "No answer received."
                st.session_state.result = answer
                st.session_state.processing = False
                st.rerun()
            else:
                st.error(f"API returned status code {response.status_code}")
                st.session_state.processing = False
                st.rerun()
        except Exception as e:
            st.error(f"An error occurred: {e}")
            st.session_state.processing = False
            st.rerun()

# Display result if available
if st.session_state.result:
    st.success("✅ Analysis Complete!")
    st.markdown("### Your Health Inequality Report")
    st.markdown(st.session_state.result)
    
    # Add a button to ask another question
    if st.button("Ask Another Question"):
        st.session_state.result = None
        st.rerun()
