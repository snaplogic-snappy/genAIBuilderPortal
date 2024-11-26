import streamlit as st
import requests
import time
from dotenv import dotenv_values

# Load environment
env = dotenv_values(".env")
timeout = 300

# Agent configurations
AGENTS = {
    "Sales Auto Update Agent (not ready)": {
        "url": "https://api.com/salesforce_update",
        "token": "123",
        "description": "Automatically updates sales data and generates insights"
    },
    "Sentiment Analysis Agent": {
        "url": "https://emea.snaplogic.com/api/1/rest/slsched/feed/ConnectFasterInc/Agent%20Creator/Sentiment%20Analysis%20Agent/reviewAgent",
        "token": "tadYY9X0bG88raf3vVaWTwl37iR049VM",
        "description": "This pipeline processes customer reviews from a Google Sheet, analyzes their sentiment, and allocates them to relevant teams using a multi-agent system. It utilizes AWS Bedrock for prompt generation and executes sub-pipelines for planning and summarizing the reviews."
    }
}

def typewriter(text: str, speed: int):
    tokens = text.split()
    container = st.empty()
    for index in range(len(tokens) + 1):
        curr_full_text = " ".join(tokens[:index])
        container.markdown(curr_full_text)
        time.sleep(1 / speed)

st.set_page_config(page_title="Backend Agent Selector")
st.title("Backend Agent Selector")
st.markdown("""
    ### Select and trigger backend agents
    Choose an agent from the dropdown list and click 'Run Agent' to trigger the process.
    Each agent performs specific automated tasks and provides detailed results.
""")

# Initialize results history and current result
if "agent_results" not in st.session_state:
    st.session_state.agent_results = []
if "current_result" not in st.session_state:
    st.session_state.current_result = None
if "show_details" not in st.session_state:
    st.session_state.show_details = False
if "first_display" not in st.session_state:
    st.session_state.first_display = True

# Agent selector
selected_agent = st.selectbox(
    "Select Agent",
    options=list(AGENTS.keys()),
    key="agent_selector"
)

# Display agent description
st.markdown(f"**Description:** {AGENTS[selected_agent]['description']}")

# Trigger button
if st.button("Run Agent", type="primary"):
    with st.spinner(f"Running {selected_agent}..."):
        # Get agent configuration
        agent_config = AGENTS[selected_agent]
        
        headers = {
            'Authorization': f'Bearer {agent_config["token"]}'
        }
        
        try:
            response = requests.get(
                url=agent_config["url"],
                headers=headers,
                timeout=timeout,
                verify=False
            )
            
            if response.status_code == 200:
                try:
                    result = response.json()
                    if len(result) > 0 and isinstance(result[0], dict):
                        response_data = result[0]
                        answer = response_data.get("answer", "")
                        summary = response_data.get("summary", "")
                        
                        # Store current result in session state
                        st.session_state.current_result = {
                            "agent": selected_agent,
                            "answer": answer,
                            "summary": summary,
                            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
                        }
                        st.session_state.first_display = True  # Reset first_display flag
                        
                        # Add to results history
                        st.session_state.agent_results.append(st.session_state.current_result)
                        
                    else:
                        st.error("❌ Invalid response format from API")
                except ValueError:
                    st.error("❌ Invalid JSON response from API")
            else:
                st.error(f"❌ Error while calling the {selected_agent} API")
        except requests.exceptions.RequestException as e:
            st.error(f"❌ Error connecting to the agent: {str(e)}")

# Display current result if exists
if st.session_state.current_result:
    st.markdown("### Current Results")
    result_container = st.container()
    with result_container:
        if st.session_state.first_display:
            typewriter(text=st.session_state.current_result["answer"], speed=10)
            st.session_state.first_display = False  # Turn off typewriter for subsequent displays
        else:
            st.markdown(st.session_state.current_result["answer"])
        
        # Add toggle button for summary
        if st.session_state.current_result.get("summary"):
            show_details = st.toggle("Show process details", value=st.session_state.show_details, key="current_toggle")
            if show_details:
                st.markdown("### Agent's Process Details")
                st.markdown(st.session_state.current_result["summary"])
            st.session_state.show_details = show_details

# Display historical results
if len(st.session_state.agent_results) > 1:  # More than just the current result
    st.markdown("### Historical Results")
    for idx, result in enumerate(reversed(st.session_state.agent_results[:-1])):  # Exclude current result
        with st.expander(f"{result['agent']} - {result['timestamp']}"):
            st.markdown(result["answer"])
            if result.get("summary"):
                toggle_key = f"history_toggle_{idx}"
                if st.toggle("Show process details", False, key=toggle_key):
                    st.markdown("### Agent's Process Details")
                    st.markdown(result["summary"])
