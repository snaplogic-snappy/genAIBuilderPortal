import streamlit as st
import pandas as pd
import json
import requests
import time
from dotenv import dotenv_values

# Demo metadata for search and filtering
DEMO_METADATA = {
    "categories": ["Content"],
    "tags": ["Wine", "Data Analysis", "Analytics"]
}

st.title("SnapLogic Workshop - GenAI Wine DB")

url = "https://emea.snaplogic.com/api/1/rest/slsched/feed/ConnectFasterInc/0_StanGPT/GenAI/Winery_GetResults_Task"
token = "VclswzviMBM7ejrKrkqr9cOO1INdx2zJ"
st.header("")

st.header("The Purpose")
st.write("This showcase demonstrates how you can find the perfect wine by simply asking questions in plain English. Ask for \"a bold Argentinian Malbec under £25\" or \"a crisp Sauvignon Blanc from New Zealand that pairs well with seafood,\" and our AI will instantly search our entire database to find exactly what you're looking for.")

st.header("The Challenge")
st.write("Vast, structured databases are incredibly valuable but often inaccessible to non-technical users. This tool bridges the gap between human curiosity and complex database schemas. It removes the need for expertise in SQL, democratizing data access and allowing anyone to perform nuanced, powerful searches.")


st.header("")
st.header("Sample Queries")

st.write("What are the top 10 highest-rated French wines")

st.write("What are the top rated wines under £20?")

st.write("What are the top 5 regions with highest average wine prices?")

st.write("What is the number of different wine varieties per country?")

st.write("What are the top 3 most expensive wines with the words hint of caramel in their description?")

st.write("Can you recommend a light rose wine with a hint of peach?")

st.write()

st.header("")
st.header("The Results!")

prompt = st.text_input("Your prompt goes here",placeholder="What are the top 10 highest-rated French wines over £300? Include the price")

headers = {
    "Authorization": f"Bearer {token}"
}

if st.button("Send Query"):
    with st.spinner("In Progress"):
        response = requests.get(
            url=url,
            headers=headers,
            params={
                "prompt":prompt
            }
        )
        
        if response.status_code==200:
            result=response.content
            wines=json.loads(result)
            query = wines[0]["original"]["queryToExecute"]
            for each in wines:
                del each["original"]
            # st.write(result)
            # for each in wines:
            #     st.write(each)
                
            df = pd.DataFrame(wines)
            st.write(df)
            st.info(query)
        else:
            st.error("Something went wrong")
            st.error(response.content)
