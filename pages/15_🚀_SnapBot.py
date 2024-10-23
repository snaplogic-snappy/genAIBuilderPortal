import streamlit as st

#st.header("SnapBot - You flexible Chatbot")
#st.subheader("You flexible Chatbot - powered by SnapLogic")
#st.image("https://raw.githubusercontent.com/mpentzek/SnapBot/2fa63755e3bfda29e83163fb13577289f456b8e7/images/SnapBot-small-transbackg.png", caption="You flexible Chatbot - powered by SnapLogic",width=300)
#st.link_button("Launch SnapBot", "https://snapbot.streamlit.app/")


# Access the theme settings
primary_color = st.get_option("theme.primaryColor")



st.markdown(
    f"""
    <style>
    .centered {{
        display: flex;
        flex-direction: column;
        justify-content: flex-start;
        align-items: center;
        text-align: center;
        margin-top: 20px;
    }}
    .centered ul {{
        text-align: left; /* Ensure the list items are left-aligned */
        list-style-position: inside; /* Ensure bullets are inside the content box */
        padding-left: 0; /* Remove default padding for ul */
    }}
    .centered li {{
        margin-left: 20px; /* Optional: Add space before list items */
    }}
    .custom-button {{
        font-size: 20px; 
        text-decoration: none; 
        color: white !important;  /* Force text color to white */
        background-color: #FF8831; 
        padding: 10px 20px; 
        border-radius: 5px;
    }}
    </style>
    <div class="centered">
        <h1>SnapBot - Your flexible Chatbot</h1>
        <p>SnapBot is a Retrieval-Augmented Generation (RAG) chatbot that allows you to upload PDF documents and ask specific questions about their content. It retrieves relevant information from one or multiple documents and generates dynamic, context-based responses derived from the text data.</p>
        <img src="https://raw.githubusercontent.com/mpentzek/SnapBot/2fa63755e3bfda29e83163fb13577289f456b8e7/images/SnapBot-small-transbackg.png" alt="SnapBot Logo" width="200">
        <br>
        <h3>Some highlights:</h3>
        <ul>
            <li>Manage your documents in seperate namespaces</li>
            <li>Select several documents for comparison, e.g.</li>
            <li>Download the documents for reference</li>
        </ul>
        <a href="https://snapbot.streamlit.app/" target="_blank" class="custom-button">Launch SnapBot</a>
    </div>
    """, 
    unsafe_allow_html=True
)
