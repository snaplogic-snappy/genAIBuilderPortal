import streamlit as st
import requests
import base64
import uuid
import os
from dotenv import load_dotenv
from PIL import Image

# Demo metadata for search and filtering
DEMO_METADATA = {
    "categories": ["Content"],
    "tags": ["RAG", "Retrieval", "Knowledge Base"]
}

# Load environment variables
load_dotenv()

# API configurations - separate URLs for upload and query
SNAPLOGIC_UPLOAD_URL = os.getenv("SNAPLOGIC_UPLOAD_URL", "http://snaplogic-upload-url.com")
SNAPLOGIC_QUERY_URL = os.getenv("SNAPLOGIC_QUERY_URL", "http://snaplogic-query-url.com")
SNAPLOGIC_API_KEY = os.getenv("SNAPLOGIC_API_KEY", "your-snaplogic-api-key")

# Page setup
st.set_page_config(page_title="AgentCreator", layout="wide")

# Custom CSS for styling (keeping your original styling)
st.markdown("""
<style>
    /* Main content area */
    .main {
        background-color: #f5f7f9;
    }
    
    /* Sidebar with Hello gradient */
    section[data-testid="stSidebar"] > div {
        background: linear-gradient(to bottom, #ff0083, #ffd700);
        color: white;
    }
    
    /* Make sidebar text white */
    section[data-testid="stSidebar"] h1, 
    section[data-testid="stSidebar"] h2, 
    section[data-testid="stSidebar"] h3, 
    section[data-testid="stSidebar"] p,
    section[data-testid="stSidebar"] label {
        color: white !important;
    }
    
    /* Fix file uploader text color in gradient sidebar */
    .css-9ycgxx, .css-1aehpvj {
        color: white !important;
    }
    
    /* Fix input field in sidebar */
    section[data-testid="stSidebar"] .stTextInput > div {
        padding: 0 !important;
        margin: 0 !important;
    }
    
    /* Fix file uploader in sidebar */
    section[data-testid="stSidebar"] .stFileUploader > div {
        padding: 0;
    }
    
    /* Fix document name input field */
    section[data-testid="stSidebar"] .stTextInput > div > div > input {
        border: 1px solid rgba(255,255,255,0.4);
        background-color: rgba(255,255,255,0.2);
        color: black;
        background: white;
        border-radius: 4px;
        padding: 8px 12px;
        height: 36px;
        font-size: 14px;
        width: 100%;
        box-sizing: border-box;
    }
    
    /* Button styling with SnapLogic Blue */
    .stButton > button {
        background-color: #003399; /* SnapLogic Blue */
        color: white;
        border-radius: 20px;
        border: none;
        padding: 0.5rem 1rem;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        width: 100%;
        font-weight: bold;
    }
    
    .stButton > button:hover {
        background-color: #0e1831; /* SnapLogic Midnight */
    }
    
    /* Header with SnapLogic Blue */
    .header {
        text-align: center;
        padding: 1.2rem;
        background: #0e1831; /* SnapLogic Midnight */
        color: white;
        border-radius: 10px;
        margin-bottom: 2rem;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        display: flex;
        justify-content: center;
        align-items: center;
    }
    
    /* Logo container */
    .logo-container {
        display: flex;
        justify-content: center;
        margin-bottom: 15px;
    }
    
    /* Input styling */
    .stTextInput > div > div > input {
        border-radius: 20px;
        border: 1px solid #003399; /* SnapLogic Blue */
        padding: 10px 15px;
    }
    
    /* Footer */
    .footer {
        text-align: center;
        padding: 1rem;
        color: #666;
        font-size: 0.8rem;
        border-top: 1px solid #eee;
        margin-top: 2rem;
    }
    
    /* Document status */
    .document-status {
        background: rgba(255,255,255,0.2);
        border-radius: 8px;
        padding: 1rem;
        margin-bottom: 20px;
    }
    
    /* Separator in sidebar */
    hr {
        margin-top: 1rem;
        margin-bottom: 1rem;
        border: 0;
        border-top: 1px solid rgba(255,255,255,0.3);
    }
    
    /* File list in sidebar */
    .file-list {
        background: rgba(255,255,255,0.15);
        border-radius: 8px;
        padding: 0.8rem;
        margin-top: 10px;
        max-height: 200px;
        overflow-y: auto;
    }
    
    .file-item {
        background: rgba(255,255,255,0.2);
        border-radius: 4px;
        padding: 5px 10px;
        margin-bottom: 5px;
        font-size: 0.9rem;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if "ragbot_messages" not in st.session_state:
    # Initialize with empty message list for Streamlit's native chat UI
    st.session_state.ragbot_messages = []
    
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
    
if "document_id" not in st.session_state:
    st.session_state.document_id = None
    
if "files" not in st.session_state:
    st.session_state.files = []

# Function to upload multiple files to SnapLogic
def upload_files_to_snaplogic(files, session_name_str):
    """
    Upload multiple files to SnapLogic for S3 storage
    Uses the dedicated upload URL
    Returns the document_id (session ID) if successful, None otherwise
    """
    try:
        # Generate a unique document/session ID
        document_id = str(uuid.uuid4())
        
        # Process each file
        file_data_list = []
        for file_obj in files:
            # Encode file data as base64
            encoded_content = base64.b64encode(file_obj.getvalue()).decode('utf-8')
            
            file_data_list.append({
                "file_name": file_obj.name,
                "content": encoded_content
            })
        
        # Send to SnapLogic for S3 storage using the upload URL
        response = requests.post(
            SNAPLOGIC_UPLOAD_URL,  # Using the specific upload URL
            headers={
                "Authorization": f"Bearer {SNAPLOGIC_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "operation": "store_documents",
                "document_id": document_id,    # This will be used as prefix in S3: sessions/{document_id}/
                "session_name": session_name_str,
                "files": file_data_list,
                "session_id": st.session_state.session_id
            }
        )
        
        if response.status_code == 200:
            return document_id
        else:
            st.error(f"Failed to upload documents: {response.status_code}")
            if hasattr(response, 'text'):
                st.error(response.text)
            return None
    except Exception as e:
        st.error(f"Error uploading documents: {str(e)}")
        return None

# Modified function to query the chatbot with message history
def query_chatbot(query, document_id):
    """
    Sends a query to the SnapLogic pipeline with the document ID and conversation history
    Uses the dedicated query URL
    SnapLogic will retrieve the documents from S3 using the document_id prefix
    """
    try:
        # Create a formatted message history for the API call
        # Convert from Streamlit format to SnapLogic expected format
        sl_messages = []
        for message in st.session_state.ragbot_messages:
            sl_role = "user" if message["role"] == "user" else "assistant"
            sl_messages.append({
                "sl_role": sl_role,
                "content": message["content"]
            })
        
        # Add the current query
        sl_messages.append({
            "sl_role": "user",
            "content": query
        })
        
        # Format for expected SnapLogic LLM input
        payload = {
            "messages": sl_messages,
            "document_id": document_id,  # SnapLogic will use this to find files in S3
            "session_id": st.session_state.session_id,
            "deployment_id": "end_turn",
            "session_documents": []
        }
        
        response = requests.post(
            SNAPLOGIC_QUERY_URL,  # Using the specific query URL
            headers={
                "Authorization": f"Bearer {SNAPLOGIC_API_KEY}",
                "Content-Type": "application/json"
            },
            json=payload
        )
        
        if response.status_code == 200:
            resp_data = response.json()
            return resp_data
        else:
            return {"error": f"Error: {response.status_code}", "response": response.text if hasattr(response, 'text') else "Unknown error"}
    except Exception as e:
        return {"error": str(e)}

# Function to process response from SnapLogic
def process_response(result):
    """
    Process different types of responses from SnapLogic
    Returns the assistant's message text
    """
    assistant_response = ""
    
    if isinstance(result, dict):
        if "error" in result:
            assistant_response = f"I encountered an error: {result['error']}"
        else:
            # Extract response based on expected format from LLM
            if "response" in result:
                assistant_response = result["response"]
            elif "content" in result:
                assistant_response = result["content"]
            elif "assistant" in result and "content" in result["assistant"]:
                assistant_response = result["assistant"]["content"]
            else:
                assistant_response = "No response received."
    elif isinstance(result, list):
        # If result is a list, use the first item if available
        if result and len(result) > 0:
            if isinstance(result[0], dict):
                if "response" in result[0]:
                    assistant_response = result[0]["response"]
                elif "content" in result[0]:
                    assistant_response = result[0]["content"]
            else:
                assistant_response = str(result[0])
        else:
            assistant_response = "Received empty list response"
    else:
        # Handle any other type of response
        assistant_response = str(result) if result else "No response received."
    
    return assistant_response

# Sidebar for document upload
with st.sidebar:
    # Use text header instead of logo
    st.markdown("<h1 style='text-align: center; color: white;'>AgentCreator</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: white;'>Create your agentic enterprise with SnapLogic</p>", unsafe_allow_html=True)
    
    st.markdown("<hr>", unsafe_allow_html=True)
    
    # When documents are loaded, don't show any session information
    if st.session_state.document_id is not None:
        # No session info displayed
        pass
    
    # Upload new documents section
    st.markdown("<p style='color: white;'>Upload Documents</p>", unsafe_allow_html=True)
    uploaded_files = st.file_uploader(
        "Choose PDF files",
        type=["pdf"],  # Restrict to PDF files only
        accept_multiple_files=True,
        label_visibility="collapsed"
    )
    
    if uploaded_files:
        # Show how many files are selected
        st.markdown(f"<p style='color: white;'>{len(uploaded_files)} file(s) selected</p>", unsafe_allow_html=True)
        
        if st.button("Use These Documents"):
            with st.spinner("Processing documents..."):
                # Upload all files to SnapLogic with a default session name
                document_id = upload_files_to_snaplogic(uploaded_files, "Default Session")
                
                if document_id:
                    # Store in session state
                    st.session_state.document_id = document_id
                    st.session_state.files = [file.name for file in uploaded_files]
                    
                    # Clear chat history
                    st.session_state.ragbot_messages = []
                    
                    st.success("Documents processed successfully!")
                    st.rerun()
                else:
                    st.error("Failed to process documents.")

# Main chat interface
# Use text header instead of logo
st.markdown("<div class='header'><h1>AgentCreator</h1></div>", unsafe_allow_html=True)

# We'll add the tool description in the welcome message instead

if st.session_state.document_id is not None:
    # No message about files or session name - clean UI
    
    # Display chat messages from history on app rerun
    if not st.session_state.ragbot_messages:
        # Display initial welcome message if no messages yet
        with st.chat_message("assistant"):
            st.write("Ask me anything about the uploaded documents.")
    else:
        # Display all previous messages using Streamlit's native chat UI
        for message in st.session_state.ragbot_messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
    
    # User input
    if prompt := st.chat_input("Ask a question about your documents..."):
        # Add user message to chat history
        st.session_state.ragbot_messages.append({"role": "user", "content": prompt})
        
        # Display user message
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Get and display assistant response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                # Query using document_id and message history
                result = query_chatbot(prompt, st.session_state.document_id)
                
                # Process the response
                response = process_response(result)
                
                # Display the response
                st.markdown(response)
                
                # Add assistant response to chat history
                st.session_state.ragbot_messages.append({"role": "assistant", "content": response})
else:
    # No document selected - use Streamlit native components instead of HTML
    # Only show the tool description without welcome messages
    st.markdown("### How Our Tool Works")
    
    st.subheader("Document Upload")
    st.markdown("- Upload PDF files (PDF only for now)")
    st.markdown("- Files are saved in an S3 bucket")
    st.markdown("- Document content becomes available to the AI")
    
    st.subheader("Advanced Context")
    st.markdown("- The AI remembers what's in your documents during the current session")
    st.markdown("- The AI saves your conversation history from the current session only")
    st.markdown("- Both document content and conversation history reset when you refresh the page")
    
    st.markdown("*You'll need to re-upload documents if you refresh the page or start a new session.*")

# Footer
st.markdown(
    """
    <div class="footer">
        <p>AgentCreator by SnapLogic uses your documents to provide contextual answers.</p>
    </div>
    """, 
    unsafe_allow_html=True
)
