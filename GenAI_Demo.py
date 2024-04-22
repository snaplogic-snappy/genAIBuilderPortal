import streamlit as st
from dotenv import dotenv_values


# Load environment
env = dotenv_values(".env")
# Streamlit Page Properties
page_title=env["PAGE_TITLE"]
title=env["TITLE"]


st.set_page_config(page_title=page_title)
st.title(title)


st.sidebar.success("Select a demo above.")

st.markdown(
    """
    
    ## SnapLogic GenAI Builder allows you to create LLM-based applications in no time! 
    
    ### **👈 Select a demo from the sidebar** to see some examples of what GenAI Builder can do!
    ## Want to learn more?
    - Check out [GenAI Builder](https://www.snaplogic.com/products/genai-builder)
    - Jump into our [documentation](https://docs-snaplogic.atlassian.net/wiki/spaces/SD/overview?homepageId=34537)
    - Ask a question in our [community](https://community.snaplogic.com)
"""
)