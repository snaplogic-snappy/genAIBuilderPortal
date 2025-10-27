# 57_🕸️_Graph_Intelligence_Dashboard.py

import streamlit as st
import pandas as pd
import json
import requests
import time

# ==========================================================
# DEMO_METADATA - REQUIRED FOR SEARCH FUNCTIONALITY
# ==========================================================
DEMO_METADATA = {
    "categories": ["Technical"],
    "tags": ["GraphDB", "Neo4j", "Agent Creator", "AI Agent", "Sales", "Support", "Customer", "Product"]
}

# ==========================================================
# PAGE CONFIGURATION
# ==========================================================
st.set_page_config(
    page_title="Graph Intelligence Dashboard (GraphDB-agnostic)",
    page_icon="🕸️",
    layout="wide"
)

page_title = "🕸️ Graph Intelligence Dashboard"
st.title(page_title)
st.markdown("*(Currently tested with **Neo4j**, but fully agnostic to any GraphDB such as TigerGraph or Memgraph.)*")

# ==========================================================
# HOMEPAGE OVERVIEW SECTION
# ==========================================================
st.markdown("""
### 🔍 About This Demo
This **Graph Intelligence Dashboard** illustrates the relationships between **Customers**, **Products**, **Opportunities**, and **Support Cases** in a unified business knowledge graph.

It supports both **sales** and **service** intelligence scenarios such as:
- Cross-sell and upsell detection  
- Case clustering and priority insights  
- Customer 360° and product performance analysis  

Built with **SnapLogic Agent Creator** and designed to connect with any graph database via a pluggable adapter.
""")

# ==========================================================
# SCHEMA IMAGE DISPLAY
# ==========================================================
st.markdown("---")
st.subheader("📈 Schema Overview – Data Relationships")

st.image("Screenshot_2025-10-24_at_10.41.35.png", caption="Customer–Product–Opportunity–Case Data Model", use_container_width=True)

st.markdown("""
**Legend**
- 🧑‍💼 **Customer** connects to **Opportunities**, **Cases**, and **Products**  
- 💼 **Opportunities** link to **Products** and **Sales Stages**  
- 🧰 **Cases** represent support requests linked to **Issue Types**, **Status**, and **Priority**  
- 🌍 **Customers** belong to **Regions**, **Industries**, and **Tiers**, and are managed by an **Account Manager**
""")

# ==========================================================
# DATABASE CONNECTION SELECTION
# ==========================================================
st.markdown("---")
st.subheader("⚙️ Connect to Your Graph Database")

db_choice = st.selectbox(
    "Select Graph Database Type",
    ["Neo4j", "TigerGraph", "Memgraph", "Custom API"],
    index=0
)

with st.expander("🔌 Connection Parameters", expanded=False):
    st.text_input("Host / Endpoint", placeholder="e.g., bolt://localhost:7687 or https://api.tigergraph.com")
    st.text_input("Username", placeholder="neo4j / tg_user / memgraph")
    st.text_input("Password / Token", type="password", placeholder="Enter credentials")
    st.text_input("Database Name (optional)", placeholder="neo4j, graph, or namespace")

st.info(f"✅ Selected database type: **{db_choice}**. Use this to test connectivity via your SnapLogic agent or direct driver.")

# ==========================================================
# EXAMPLE QUERY INTERFACE
# ==========================================================
st.markdown("---")
st.subheader("💬 Try a Sample Query")

sample_query = st.text_area(
    "Enter your graph query (Cypher, GSQL, or open format):",
    value="MATCH (c:Customer)-[:HAS_OPPORTUNITY]->(o:Opportunity) RETURN c.name, COUNT(o) AS opportunities LIMIT 10"
)

if st.button("▶️ Run Query", type="primary", use_container_width=True):
    st.info("This demo is front-end only – replace this with your SnapLogic pipeline or API call for execution.")
    st.code(sample_query, language="cypher")

    # Mock result preview
    mock_data = [
        {"Customer": "Gamma Connect Solutions", "Opportunities": 5},
        {"Customer": "OmniTech Europe", "Opportunities": 3},
        {"Customer": "BlueWave Medical", "Opportunities": 7},
    ]
    df = pd.DataFrame(mock_data)
    st.dataframe(df, use_container_width=True)

# ==========================================================
# FUTURE EXTENSION SECTION
# ==========================================================
st.markdown("---")
col1, col2 = st.columns([1, 1])

with col1:
    st.markdown("""
    ### 🔮 Planned Extensions
    - Agentic reasoning over graph data  
    - Cross-graph unification via **SnapLogic pipelines**  
    - Natural language query orchestration  
    - Predictive account health scoring  
    - Real-time case escalation alerts
    """)

with col2:
    st.markdown("""
    ### 🧠 Technology Stack
    - **Frontend**: Streamlit (Demo Portal)  
    - **Backend**: SnapLogic Agent Creator  
    - **Graph Layer**: Any GraphDB (Neo4j, TigerGraph, Memgraph)  
    - **AI Orchestration**: OpenAI / LangChain  
    - **Visualization**: Graph Data Science + Streamlit Charts  
    """)

# ==========================================================
# FOOTER
# ==========================================================
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666; font-size: 0.9em;'>
    <p>🕸️ Graph Intelligence Dashboard – powered by SnapLogic Agent Creator</p>
    <p>Supports Neo4j (reference), TigerGraph, and Memgraph integrations</p>
</div>
""", unsafe_allow_html=True)
