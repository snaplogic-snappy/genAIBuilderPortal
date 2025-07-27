import streamlit as st
import os
import re
import importlib.util
from dotenv import dotenv_values

# Load environment
env = dotenv_values(".env")
# Streamlit Page Properties
page_title = env.get("PAGE_TITLE", "SnapLogic GenAI Builder Portal")
title = env.get("TITLE", "SnapLogic GenAI Builder Portal")

def get_demo_metadata():
    """Get comprehensive demo metadata including categories and tags"""
    demos = []
    pages_dir = "pages"
    
    if not os.path.exists(pages_dir):
        return demos
    
    for filename in sorted(os.listdir(pages_dir)):
        if filename.endswith('.py') and filename != '__init__.py':
            try:
                # Extract basic info from filename using simple string parsing
                # Format: number_emoji_name.py (with underscores or spaces)
                parts = filename.replace('.py', '').split('_')
                if len(parts) >= 3:
                    number = int(parts[0])
                    emoji = parts[1]
                    title = ' '.join(parts[2:]).replace('_', ' ')
                    
                    # Get metadata from the demo file
                    metadata = get_metadata_from_file(os.path.join(pages_dir, filename))
                    
                    demos.append({
                        'filename': filename,
                        'number': number,
                        'emoji': emoji,
                        'title': title,
                        'url_path': filename[:-3],
                        'categories': metadata.get('categories', []),
                        'tags': metadata.get('tags', []),
                        'searchable_text': create_searchable_text(title, metadata)
                    })
            except Exception as e:
                st.warning(f"Could not parse metadata for {filename}: {str(e)}")
    
    # Sort demos by demo number to ensure proper numerical ordering
    demos.sort(key=lambda x: x['number'])
    
    return demos

def get_metadata_from_file(filepath):
    """Extract DEMO_METADATA from a demo file without importing it"""
    try:
        with open(filepath, 'r', encoding='utf-8') as file:
            content = file.read()
            
        # Find DEMO_METADATA dictionary
        metadata_match = re.search(r'DEMO_METADATA\s*=\s*{([^}]+)}', content, re.DOTALL)
        if metadata_match:
            metadata_str = metadata_match.group(1)
            
            # Extract categories
            categories_match = re.search(r'"categories":\s*\[([^\]]*)\]', metadata_str)
            categories = []
            if categories_match:
                categories_str = categories_match.group(1)
                categories = [cat.strip().strip('"\'') for cat in categories_str.split(',') if cat.strip()]
            
            # Extract tags
            tags_match = re.search(r'"tags":\s*\[([^\]]*)\]', metadata_str)
            tags = []
            if tags_match:
                tags_str = tags_match.group(1)
                tags = [tag.strip().strip('"\'') for tag in tags_str.split(',') if tag.strip()]
            
            return {
                'categories': categories,
                'tags': tags
            }
    except Exception as e:
        st.warning(f"Error reading metadata from {filepath}: {str(e)}")
    
    return {'categories': [], 'tags': []}

def create_searchable_text(title, metadata):
    """Create comprehensive searchable text from title, categories, and tags"""
    searchable_parts = []
    
    # Add title words
    searchable_parts.extend(title.lower().split())
    
    # Add categories
    searchable_parts.extend([cat.lower() for cat in metadata.get('categories', [])])
    
    # Add tags
    searchable_parts.extend([tag.lower() for tag in metadata.get('tags', [])])
    
    return ' '.join(searchable_parts)

def filter_demos(demos, search_term):
    """Advanced filtering based on search term across all metadata"""
    if not search_term:
        return demos
    
    search_lower = search_term.lower()
    filtered = []
    
    for demo in demos:
        # Check if search term matches any part of the searchable text
        if search_lower in demo['searchable_text']:
            filtered.append(demo)
        # Also check exact matches for demo number
        elif str(demo['number']) == search_lower:
            filtered.append(demo)
        # Check emoji
        elif search_lower in demo['emoji'].lower():
            filtered.append(demo)
    
    return filtered

def render_demo_grid(filtered_demos, all_demos_count):
    """Display filtered demos using pure Streamlit components"""
    if not filtered_demos:
        st.info("No demos match your search. Try a different keyword.")
        return

    # Add custom CSS for styling the pure Streamlit components
    st.markdown("""
    <style>
    /* Style Streamlit page links to look like our custom buttons */
    [data-testid="stPageLink"] {
        background: #3b82f6 !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 0.75rem 1.5rem !important;
        text-decoration: none !important;
        display: block !important;
        font-weight: 700 !important;
        text-align: center !important;
        font-size: 1.2rem !important;
        transition: all 0.2s ease !important;
        width: 100% !important;
        box-sizing: border-box !important;
        cursor: pointer !important;
        margin-top: 0.5rem !important;
    }
    [data-testid="stPageLink"]:hover {
        background: #2563eb !important;
        transform: translateY(-1px) !important;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1) !important;
        border: 2px solid #1d4ed8 !important;
    }
    
    /* Force white text on all page link elements */
    [data-testid="stPageLink"] * {
        color: white !important;
    }
    [data-testid="stPageLink"] a {
        color: white !important;
    }
    [data-testid="stPageLink"] span {
        color: white !important;
    }
    
    /* Border for demo cards using a wrapper div */
    .demo-card {
        border: 3px solid #e0e0e0 !important;
        border-radius: 8px !important;
        padding: 1rem !important;
        margin-bottom: 1rem !important;
        background: white !important;
        height: 280px !important;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1) !important;
    }
    .demo-card:hover {
        border-color: #3b82f6 !important;
        box-shadow: 0 4px 8px rgba(0,0,0,0.15) !important;
    }
    </style>
    """, unsafe_allow_html=True)

    # Create a responsive grid using Streamlit columns
    cols = st.columns(2)
    
    for i, demo in enumerate(filtered_demos):
        with cols[i % 2]:
            # Clean up title by replacing underscores with spaces
            clean_title = demo['title'].replace('_', ' ')
            
            # Wrap everything in a demo card container
            st.markdown(f"""
            <div class="demo-card">
                <h3>{demo['emoji']} {clean_title}</h3>
                <p><em>Demo #{demo['number']}</em></p>
                {f'<p><strong>Categories:</strong> {", ".join(demo["categories"])}</p>' if demo.get('categories') else ''}
                {f'<p><strong>Tags:</strong> {", ".join(demo["tags"])}</p>' if demo.get('tags') else ''}
            </div>
            """, unsafe_allow_html=True)
            
            # Button using native Streamlit navigation
            st.page_link(f"pages/{demo['filename']}", label="Open Demo", use_container_width=True)

# Main page setup
st.set_page_config(
    page_title=page_title,
    initial_sidebar_state="expanded"
)
st.title(title)

st.sidebar.title("Agent Creator Catalog")
st.sidebar.success("Select a demo above.")

# Enhanced search functionality
st.markdown("## 🔍 Search Demos")
st.markdown("Search by **any word** in the demo title, **categories**, or **tags**")

search_term = st.text_input(
    "Search demos...", 
    placeholder="e.g., HR, Business, Analytics, Healthcare, Sales, SnapLogic...",
    key="search_input"
)

# Get and filter demos
demos = get_demo_metadata()
filtered_demos = filter_demos(demos, search_term)

# Display results
if search_term:
    st.caption(f"Showing {len(filtered_demos)} of {len(demos)} demos")
else:
    st.caption(f"All {len(demos)} demos")

render_demo_grid(filtered_demos, len(demos))

# Show search tips
if search_term:
    st.markdown("---")
    st.markdown("### 💡 Search Tips")
    st.markdown(f"""
    - **Title words**: Search for any word in demo titles
    - **Categories**: Try "Business", "Content", "Technical", "Industry"  
    - **Tags**: Search specific tags like "HR", "Sales", "Analytics", "Healthcare"
    - **Functions**: Look for "Assistant", "Agent", "Bot", "Tool"
    - **Industries**: Search "Healthcare", "Finance", "Government", "Education"
    """)

# Original landing page content
st.markdown("---")
st.markdown(
    """
    ## 🚀 Welcome to SnapLogic GenAI Builder Portal
    
    This portal showcases **44 powerful AI agents** built with SnapLogic Agent Creator, demonstrating the incredible capabilities of LLM-based applications.
    
    ### 🎯 What You'll Find Here
    
    **Business Solutions** (8 demos)
    - HR assistants, billing reconciliation, CRM analytics
    - Sales agents, invoice processing, customer intelligence
    
    **Content Creation** (15 demos)  
    - Chatbots, blog writers, social media agents
    - Content generation, outreach sequences, document processing
    
    **Technical Tools** (10 demos)
    - Data science assistants, SnapLogic expert agents
    - Technical evaluations, support log analysis, runtime tools
    
    **Industry Solutions** (11 demos)
    - Healthcare, government, law enforcement, military
    - Manufacturing, insurance, education applications
    
    ### 🔍 How to Explore
    
    1. **Search Above**: Use the search box to find specific demos by any word in the title, categories, or tags
    2. **Browse by Category**: Use the sidebar to navigate through different demo categories
    3. **Search by Function**: Look for specific capabilities like "HR", "Sales", "Analytics"
    4. **Find by Technology**: Search for "SnapLogic", "SQL", "PDF" to find relevant tools
    5. **Industry Focus**: Explore healthcare, government, or manufacturing solutions
    
    ### 💡 Getting Started
    
    **👈 Select any demo from the sidebar** to see Agent Creator in action!
    
    Each demo showcases:
    - Real-world use cases
    - Natural language interaction
    - Integration with various data sources
    - Professional-grade AI capabilities
    
    ---
    
    ## 🛠️ About SnapLogic Agent Creator
    
    **SnapLogic Agent Creator** allows you to create LLM-based applications in no time! 
    
    ### Key Features:
    - **No-Code Development**: Build AI agents without writing complex code
    - **Enterprise Integration**: Connect to any data source or API
    - **Natural Language**: Interact with your data using plain English
    - **Scalable Architecture**: Deploy production-ready AI applications
    
    ### Want to Learn More?
    - 📚 [Agent Creator Documentation](https://docs.snaplogic.com/agentcreator/agentcreator-about.html)
    - 🏢 [SnapLogic Platform Docs](https://docs.snaplogic.com)
    - 💬 [Community Forum](https://community.snaplogic.com)
    - 🎥 [Video Tutorials](https://www.youtube.com/@snaplogic)
    
    ---
    
    *Ready to explore? Choose a demo from the sidebar or search above to get started!*
    """
)

# Add some visual elements
col1, col2, col3 = st.columns(3)

with col1:
    st.info("**44 AI Agents**\nReady to explore")

with col2:
    st.success("**4 Categories**\nBusiness, Content, Technical, Industry")

with col3:
    st.warning("**100+ Tags**\nFind exactly what you need")
