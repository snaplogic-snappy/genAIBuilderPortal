import streamlit as st
from dotenv import dotenv_values


# Load environment
env = dotenv_values(".env")
# Streamlit Page Properties
page_title=env["PAGE_TITLE"]
title=env["TITLE"]


st.set_page_config(page_title=page_title)
st.title(title)

st.sidebar.title("Agent Creator Catalog")
st.sidebar.success("Select a demo above.")

st.markdown(
    """
    
    ## SnapLogic Agent Creator allows you to create LLM-based applications in no time! 
    
    ### **👈 Select a demo from the sidebar** to see some examples of what Agent Creator can do!
    ## Want to learn more?
    - Check out [Agent Creator](https://www.snaplogic.com/products/agent-creator)
    - Jump into our [documentation](https://docs-snaplogic.atlassian.net/wiki/spaces/SD/overview?homepageId=34537)
    - Ask a question in our [community](https://community.snaplogic.com)
"""
)
