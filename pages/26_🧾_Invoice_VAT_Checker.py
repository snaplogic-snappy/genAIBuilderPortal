import streamlit as st
import requests
import json
import time
from dotenv import dotenv_values

# Configuration
URL = "https://emea.snaplogic.com/api/1/rest/slsched/feed/ConnectFasterInc/Konstantin/shared/InvoiceChecker"
BEARER_TOKEN = "8jtHJpkQJYdpqvYaYfzZ19GtBuZYEn3i"
timeout = 30

# Page setup
st.set_page_config(page_title="Invoice VAT Checker")
st.title("Invoice VAT Verification System")

def typewriter(text: str, speed: int):
    tokens = text.split()
    container = st.empty()
    for index in range(len(tokens) + 1):
        curr_full_text = " ".join(tokens[:index])
        container.markdown(curr_full_text)
        time.sleep(1 / speed)

st.markdown(
    """
    ### Invoice VAT Verification System
    
    This tool helps you:
    - Verify if the VAT calculation on your invoice is correct
    - Check if the VAT amount can be reclaimed
    - Validate the VAT registration details of the seller
    
    Please upload your invoice in PDF format for analysis.
    """
)

with st.chat_message("assistant"):
    st.markdown("Hello! 👋 Let me help you verify your invoice.")

uploaded_file = st.file_uploader("Upload your invoice (PDF format)")

if uploaded_file is not None:
    file_bytes = uploaded_file.getvalue()
    
    with st.chat_message("assistant"):
        st.markdown("Invoice uploaded successfully! Click below to analyze the VAT details.")
    
    if st.button(":blue[Verify VAT]"):
        with st.spinner("Analyzing invoice..."):
            headers = {
                'Authorization': f'Bearer {BEARER_TOKEN}',
                'Content-Type': 'application/octet-stream'
            }
            
            try:
                response = requests.post(
                    url=URL,
                    data=file_bytes,
                    headers=headers,
                    timeout=timeout,
                    verify=False
                )
                
                result = response.json()[0]["output"]
                
                # Display results
                with st.chat_message("assistant"):
                    typewriter("Analysis complete! Here are the findings:", 10)
                
                time.sleep(1.0)
                
                # Create an expander for the detailed analysis
                with st.expander("See detailed analysis"):
                    st.markdown(result)
                
                # Extract key information using string parsing
                if "can be reclaimed" in result.lower():
                    st.success("✅ The VAT on this invoice can be reclaimed!")
                elif "cannot be reclaimed" in result.lower():
                    st.error("❌ The VAT on this invoice cannot be reclaimed.")
                    
                # Display VAT information in metrics
                if "19%" in result:  # Example of extracting VAT rate
                    st.markdown("### VAT Details")
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("VAT Rate", "19%")
                    with col2:
                        st.metric("Reclaim Status", "Eligible")
                
            except requests.exceptions.RequestException as e:
                st.error(f"An error occurred while processing the invoice: {str(e)}")
            except json.JSONDecodeError:
                st.error("Unable to parse the response from the server.")
            except Exception as e:
                st.error(f"An unexpected error occurred: {str(e)}")
