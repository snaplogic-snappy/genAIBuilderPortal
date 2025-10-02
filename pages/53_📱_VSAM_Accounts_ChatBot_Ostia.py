import streamlit as st
import requests
from docx import Document 
import re
import spacy
from spacy.cli import download
import tempfile
import json
import os
from PIL import Image
import base64

# ===============================
# Streamlit Page Setup
# ===============================
st.set_page_config(page_title="💬 Ask your question about a customer account:", layout="wide")

# ===============================
# Load NLP model with fallback
# ===============================
#try:
#    nlp = spacy.load("en_core_web_sm")
#except OSError:
#    import subprocess
#    subprocess.run(["python", "-m", "spacy", "download", "en_core_web_sm"])
#    nlp = spacy.load("en_core_web_sm")
@st.cache_resource
def load_spacy_model():
    nlp = spacy.load("en_core_web_sm")
    return nlp

nlp = load_spacy_model()


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
doc_text, doc_images = extract_doc_content("assets/Mainframe VSAM Accounts and Customer Data Query Tool V1.docx")

# ===============================
# Display full document with graphics
# ===============================
st.markdown("<h1 style='text-align:center;'>💡 Ask your question about a customer account:</h1>", unsafe_allow_html=True)
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

# Initialize messages
if "messages" not in st.session_state:
    st.session_state.messages = []

# Show previous messages
for message in st.session_state.messages:
    if message["role"] == "user":
        st.markdown(f"""
        <div style='background-color:#DCF8C6; padding:10px; border-radius:10px; margin-bottom:5px; text-align:right'>
        <b>👤 You:</b> {message["content"]}
        </div>""", unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div style='background-color:#F1F0F0; padding:10px; border-radius:10px; margin-bottom:5px; text-align:left'>
        <b>🤖 Assistant:</b> {message["content"]}
        </div>""", unsafe_allow_html=True)

# ===============================
# User input
# ===============================
if prompt := st.chat_input("Ask me about your accounts or balances..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    refined_query = prompt

    # API call
    try:
        response = requests.post(
            url="https://elastic.snaplogic.com/api/1/rest/slsched/feed/ConnectFasterInc/.Rich/mainframe_accelerator/Accounts_Batch_Retriever%20Task",
            headers={
                "Authorization": "Bearer bPZFJR6UugxvRNEgkqcIZsOHXFMd2x5F",
                "Content-Type": "application/json"
            },
            json={"Question": refined_query}
        )

        if response.status_code == 200:
            api_result = response.json()
            formatted_result = api_result[0].get("response", "No valid response from the API.")
            st.markdown(formatted_result)
            bot_reply = f"✅ **Results for:** `{refined_query}`\n\n```json\n{formatted_result}\n```"
        else:
            bot_reply = f"⚠️ API request failed with status {response.status_code}"

    except Exception as e:
        bot_reply = f"❌ Error contacting the API: {str(e)}"

    bot_reply += "\n\n💡 *Tip:* Ask 'What transactions are there on my accounts ?'."

    st.session_state.messages.append({"role": "assistant", "content": bot_reply})

    st.rerun()
