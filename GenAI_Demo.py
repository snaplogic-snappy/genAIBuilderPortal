import streamlit as st
from dotenv import dotenv_values
import os
from pathlib import Path

# Load environment
env = dotenv_values(".env")

# Streamlit Page Properties
page_title = env["PAGE_TITLE"]
title = env["TITLE"]

# Configure page
st.set_page_config(page_title=page_title)
st.title(title)

def get_demo_sections():
    """
    Organize demo files into sections based on their prefixes or content.
    Returns a dictionary with section names as keys and lists of demo files as values.
    """
    pages_dir = Path("pages")
    demo_sections = {
        "🤖 Assistants": [],
        "🎯 Agents": [],
        "🔄 Others": []
    }
    
    if not pages_dir.exists():
        return demo_sections
    
    for file in pages_dir.glob("*.py"):
        file_name = file.name
        # You can customize these conditions based on your file naming convention
        if "assistant" in file_name.lower():
            demo_sections["🤖 Assistants"].append(file_name)
        elif "agent" in file_name.lower():
            demo_sections["🎯 Agents"].append(file_name)
        else:
            demo_sections["🔄 Others"].append(file_name)
            
    # Sort files within each section
    for section in demo_sections:
        demo_sections[section].sort()
        
    return demo_sections

# Create organized sidebar
st.sidebar.title("Demo Navigation")

# Get organized demo sections
demo_sections = get_demo_sections()

# Display sections in sidebar
for section, demos in demo_sections.items():
    if demos:  # Only show sections that have demos
        st.sidebar.header(section)
        for demo in demos:
            # Create a clean display name (remove .py and replace underscores)
            display_name = demo[:-3].replace('_', ' ').title()
            st.sidebar.page_link(f"pages/{demo}", label=display_name)

# Main page content
st.markdown(
    """
    ## SnapLogic GenAI App Builder allows you to create LLM-based applications in no time! 
    
    ### **👈 Select a demo from the sidebar** to see some examples of what GenAI App Builder can do!
    
    ## Want to learn more?
    - Check out [GenAI Builder](https://www.snaplogic.com/products/genai-builder)
    - Jump into our [documentation](https://docs-snaplogic.atlassian.net/wiki/spaces/SD/overview?homepageId=34537)
    - Ask a question in our [community](https://community.snaplogic.com)
    """
)

# Display demo statistics
total_demos = sum(len(demos) for demos in demo_sections.values())
st.sidebar.divider()
st.sidebar.caption(f"Total Demos: {total_demos}")
for section, demos in demo_sections.items():
    if demos:
        st.sidebar.caption(f"{section}: {len(demos)}")
