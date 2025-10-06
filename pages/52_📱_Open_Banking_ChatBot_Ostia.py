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
    "tags": ["Banking", "Open Banking", "Financial", "Mainframe", "VSAM", "Ostia"]
}


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
doc_text, doc_images = extract_doc_content("assets/Open Banking Query Tool V1.docx")

# ===============================
# Streamlit Page Setup
# ===============================
st.set_page_config(page_title="💬 Open Banking Assistant", layout="wide")

# ===============================
# Display full document with graphics
# ===============================
st.markdown("<h1 style='text-align:center;'>💡 Open Banking Query Tool</h1>", unsafe_allow_html=True)
st.markdown("---")
st.markdown(doc_text)

if doc_images:
    for img_path in doc_images:
        if img_path.lower().endswith(".svg"):
            # Render SVG using HTML
            with open(img_path, "rb") as f:
                svg_data = f.read()
                b64 = base64.b64encode(svg_data).decode("utf-8")
                st.markdown(f'<img src="data:image/svg+xml;base64,{b64}" width="100%">', unsafe_allow_html=True)
#        else:
#            st.image(Image.open(img_path), use_container_width=True)

st.markdown("---")
st.markdown("### 💬 Chat with the Assistant")

# Initialize messages with unique key for this demo
if "openbanking_messages" not in st.session_state:
    st.session_state.openbanking_messages = []

# Show previous messages using proper chat interface
for message in st.session_state.openbanking_messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])


# ===============================
# User input
# ===============================
if prompt := st.chat_input("Ask me about transactions, direct debits, or balances..."):
    # Add user message
    st.session_state.openbanking_messages.append({"role": "user", "content": prompt})

    with st.spinner("Processing your banking query..."):
        try:
            response = requests.post(
                url="https://elastic.snaplogic.com/api/1/rest/slsched/feed/ConnectFasterInc/.Rich/mainframe_accelerator/Open%20Banking%20Driver%20Task",
                headers={
                    "Authorization": "Bearer rNZFKayKbCaydnseadwlxFdPxtQsnbLI",
                    "Content-Type": "application/json"
                },
                json={"prompt": prompt},
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

        bot_reply += "\n\n💡 *Tip:* Ask 'Show transactions over 100 USD last month' or 'List standing orders above 200 USD'."

        # Add assistant response to chat history
        st.session_state.openbanking_messages.append({"role": "assistant", "content": bot_reply})

    # Rerun to display the new messages
    st.rerun()











