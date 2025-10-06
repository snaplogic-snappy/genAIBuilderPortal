import streamlit as st
import requests
from docx import Document
import json
import os
from PIL import Image
import base64

# DEMO_METADATA - REQUIRED FOR SEARCH FUNCTIONALITY
DEMO_METADATA = {
    "categories": ["Industry"],
    "tags": ["HR", "Employees", "Human Resources", "Mainframe", "VSAM", "Ostia"]
}

# ===============================
# Streamlit Page Setup
# ===============================
st.set_page_config(page_title="💬 Ask your question about your employees:", layout="wide")


# ===============================
# Extract text and images from Word document
# ===============================
def extract_doc_content(docx_path, image_dir="extracted_images"):
    doc = Document(docx_path)
    content = ""
    os.makedirs(image_dir, exist_ok=True)

    # Extract text
    for para in doc.paragraphs:
        if para.style.name.startswith("Heading"):
            content += f"\n### {para.text}\n"
        else:
            content += f"{para.text}\n\n"

    # Extract images
    images = []
    for rel in doc.part.rels.values():
        if "image" in rel.target_ref:
            image_data = rel.target_part.blob
            image_filename = os.path.join(image_dir, os.path.basename(rel.target_ref))
            with open(image_filename, "wb") as img_file:
                img_file.write(image_data)
            images.append(image_filename)

    return content, images

# Load content and graphics
doc_text, doc_images = extract_doc_content("assets/Mainframe VSAM Employee Data Query Tool V1.docx")

# ===============================
# Display full document with graphics
# ===============================
st.markdown("<h1 style='text-align:center;'>💡 Ask your question about your employees</h1>", unsafe_allow_html=True)
st.markdown("---")
st.markdown(doc_text)

if doc_images:
    for img_path in doc_images:
        if img_path.lower().endswith(".svg"):
            # Render SVG using HTML
            st.markdown("---")
#            with open(img_path, "rb") as f:
#                svg_data = f.read()
#                b64 = base64.b64encode(svg_data).decode("utf-8")
#                st.markdown(f'<img src="data:image/svg+xml;base64,{b64}" width="100%">', unsafe_allow_html=True)
        else:
            st.image(Image.open(img_path), use_container_width=True)

st.markdown("---")
st.markdown("### 💬 Chat with the Assistant")

# Initialize messages with unique key for this demo
if "vsam_employees_messages" not in st.session_state:
    st.session_state.vsam_employees_messages = []

# Show previous messages using proper chat interface
for message in st.session_state.vsam_employees_messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])


# ===============================
# User input
# ===============================
if prompt := st.chat_input("Ask me about your employees..."):
    # Add user message
    st.session_state.vsam_employees_messages.append({"role": "user", "content": prompt})

    with st.spinner("Processing your employee query..."):
        try:
            response = requests.post(
                url="https://elastic.snaplogic.com/api/1/rest/slsched/feed/ConnectFasterInc/.Rich/mainframe_accelerator/Employees_Batch_Retriever%20Task",
                headers={
                    "Authorization": "Bearer wJKtWIlhJpMkcJDtJzBvoi618PG6KjES",
                    "Content-Type": "application/json"
                },
                json={"Question": prompt},
                timeout=300
            )

            if response.status_code == 200:
                api_result = response.json()
                formatted_result = api_result[0].get("response", "No valid response from the API.")
                bot_reply = f"✅ **Results for:** `{prompt}`\n\n{formatted_result}"
            else:
                bot_reply = f"⚠️ API request failed with status {response.status_code}"

        except Exception as e:
            bot_reply = f"❌ Error contacting the API: {str(e)}"

        bot_reply += "\n\n💡 *Tip:* Ask 'How many employees are called John ?'."

        # Add assistant response to chat history
        st.session_state.vsam_employees_messages.append({"role": "assistant", "content": bot_reply})

    # Rerun to display the new messages
    st.rerun()
