import streamlit as st
import requests
import json
import datetime

# --- Streamlit Page Config ---
st.set_page_config(page_title="MCP Healthcare Analysis", layout="wide")

# --- Initialize Session State for Chat History ---
if "mcp_healthcare_chat_history" not in st.session_state:
    st.session_state.mcp_healthcare_chat_history = []
    
if "mcp_healthcare_conversation_id" not in st.session_state:
    st.session_state.mcp_healthcare_conversation_id = f"conv-{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"

# --- Title and Info ---
st.title("🏥 MCP Healthcare Data Analysis 🩺")
st.markdown("""
Welcome to the **MCP Healthcare Data Analysis Platform** powered by SnapLogic.

**Ask questions about global healthcare trends, disease patterns, medical research, or health policy analysis.**

Info on this tool:
- This tools was created by **Angelica Tacca**. Reach out to atdughetti@snaplogic.com for any doubts or questions.
- The MCP server resides in a EC2 Ubuntu Machine in AWS and takes the code from https://github.com/cicatriiz/healthcare-mcp-public
- Our own GitHub repo for this demo lives here: [github/Healthcare-MCP-Demo](https://github.com/angietd94/Healthcare-MCP-Demo/tree/main)

- **Direct Pipelines Links**  
-- [Driver](https://cdn.emea.snaplogic.com/sl/designer.html?v=26808#pipe_snode=68aec550dee0c2a2a73bb1ce)  
-- [Worker](https://cdn.emea.snaplogic.com/sl/designer.html?v=26808#pipe_snode=68aec55b1899534695fee030)


Examples of simple questions:
- Give me the FDA label information for ibuprofen.
- Find the most recent clinical studies on Alzheimer’s disease treatment published in the last 2 years.
- Show me ongoing clinical trials for breast cancer.

More complex examples that force multiple tools:

- What are the FDA adverse events reported for metformin, and show me recent PubMed papers on its side effects?
- Give me the ICD-10 codes for asthma, find the most recent clinical trials recruiting for asthma, and summarize basic health information about asthma in Spanish.
- Find the FDA label for sildenafil, check PubMed for recent studies about its cardiovascular effects, and show ongoing clinical trials related to erectile dysfunction.
- Look up the FDA label for fluoxetine, list common adverse events, retrieve the last 3 PubMed papers about its efficacy in anxiety, and give me the ICD-10 code for generalized anxiety disorder.
""")

# --- API Configuration ---
API_ENDPOINT = "https://emea.snaplogic.com/api/1/rest/slsched/feed/ConnectFasterInc/Angelica/MCP_project_demo/AgentDriver%20Task"
BEARER_TOKEN = "mfxS74X1E0oQBSngK67KTdGALG0uDO17"  # Store securely in production!

headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {BEARER_TOKEN}"
}

# --- Function to add message to chat history ---
def add_message(role, content):
    st.session_state.mcp_healthcare_chat_history.append({"role": role, "content": content})

# --- Display Chat History ---
chat_container = st.container()
with chat_container:
    for message in st.session_state.mcp_healthcare_chat_history:
        if message["role"] == "user":
            st.markdown(f"**You:** {message['content']}")
        else:
            st.markdown(f"**MCP Healthcare Analyst:** {message['content']}")
            st.markdown("---")

# --- Input Field ---
user_question = st.text_input("📝 Ask about healthcare data:")

# --- Call API on Submit ---
if st.button("🔍 Send"):
    if not user_question.strip():
        st.warning("Please enter a valid question.")
    else:
        # Add user message to chat history
        add_message("user", user_question)
        
        # Prepare conversation history for context
        conversation_context = ""
        if len(st.session_state.mcp_healthcare_chat_history) > 1:  # If there's previous conversation
            for msg in st.session_state.mcp_healthcare_chat_history[:-1]:  # Exclude the current message
                prefix = "User: " if msg["role"] == "user" else "Assistant: "
                conversation_context += f"{prefix}{msg['content']}\n\n"
        
        # Create payload
        payload = [{
            "prompt": user_question,
            "conversation_id": st.session_state.mcp_healthcare_conversation_id,
            "conversation_history": conversation_context if conversation_context else None
        }]
        
        with st.spinner("Analyzing healthcare data with MCP..."):
            try:
                # Start timing
                start_time = datetime.datetime.now()
                
                response = requests.post(API_ENDPOINT, headers=headers, json=payload)
                if response.status_code == 200:
                    # End timing
                    end_time = datetime.datetime.now()
                    response_time_ms = (end_time - start_time).total_seconds() * 1000
                    
                    data = response.json()
                    response_text = data.get("response", "No response found.")
                    
                    # Add response time information
                    response_with_timing = f"{response_text}\n\n*Response time: {response_time_ms:.2f} ms*"
                    
                    # Add assistant response to chat history
                    add_message("assistant", response_with_timing)
                    
                    # Rerun to update the UI with the new messages
                    st.rerun()
                else:
                    error_msg = f"Error {response.status_code}: {response.text}"
                    add_message("assistant", f"⚠️ {error_msg}")
                    st.error(error_msg)
            except Exception as e:
                error_msg = f"An unexpected error occurred:\n{e}"
                add_message("assistant", f"⚠️ {error_msg}")
                st.error(error_msg)

# --- Clear Chat Button ---
if st.button("🗑️ Clear Chat"):
    st.session_state.mcp_healthcare_chat_history = []
    st.session_state.mcp_healthcare_conversation_id = f"conv-{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
    st.rerun()
