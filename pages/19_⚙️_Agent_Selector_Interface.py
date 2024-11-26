import streamlit as st
import requests
import time
from dotenv import dotenv_values

# Load environment
env = dotenv_values(".env")
timeout = 300

# Agent configurations
AGENTS = {
    "Sample Analysis Agent": {
        "url": "https://emea.snaplogic.com/api/1/rest/slsched/feed/ConnectFasterInc/Jocelyn/shared/sampleBackendAnalysis",
        "token": "fR8nGueztyAi5kGTJssZ3pWrHPFkOGcS",
        "description": "Sample analysis agent"
    },
    "Sales Auto Update Agent": {
        "url": "https://api.com/salesforce_update",
        "token": "123",
        "description": "Automatically updates sales data and generates insights"
    },
    "User Review Analyzer": {
        "url": "https://api.com/user_review",
        "token": "456",
        "description": "Analyzes user reviews and provides sentiment analysis"
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

# Initialize results history
if "agent_results" not in st.session_state:
    st.session_state.agent_results = []

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
            response = requests.get(  # Changed from post to get
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
                        
                        # Create container for results
                        result_container = st.container()
                        with result_container:
                            st.markdown("### Results")
                            
                            # Display answer
                            typewriter(text=answer, speed=10)
                            
                            # Add toggle button for summary
                            if summary:
                                toggle_key = f"toggle_{len(st.session_state.agent_results)}"
                                if st.toggle("Show process details", False, key=toggle_key):
                                    st.markdown("### Agent's Process Details")
                                    st.markdown(summary)
                        
                        # Add to results history
                        st.session_state.agent_results.append({
                            "agent": selected_agent,
                            "answer": answer,
                            "summary": summary,
                            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
                        })
                    else:
                        st.error("❌ Invalid response format from API")
                except ValueError:
                    st.error("❌ Invalid JSON response from API")
            else:
                st.error(f"❌ Error while calling the {selected_agent} API")
        except requests.exceptions.RequestException as e:
            st.error(f"❌ Error connecting to the agent: {str(e)}")

# Display historical results
if st.session_state.agent_results:
    st.markdown("### Historical Results")
    for idx, result in enumerate(reversed(st.session_state.agent_results)):
        with st.expander(f"{result['agent']} - {result['timestamp']}"):
            st.markdown(result["answer"])
            if result.get("summary"):
                toggle_key = f"history_toggle_{idx}"
                if st.toggle("Show process details", False, key=toggle_key):
                    st.markdown("### Agent's Process Details")
                    st.markdown(result["summary"])
