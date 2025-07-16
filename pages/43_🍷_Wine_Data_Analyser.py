import streamlit as st
import pandas as pd
import json
import requests

injected_prompt="""

You are given a SNOWFLAKE Table called SO_WINERY on the schema SEDEMO with the following description:
{"name":"country","type":"VARCHAR(32700)","kind":"COLUMN","null?":"Y","default":null,"primary key":"N","unique key":"N","check":null,"expression":null,"comment":null,"policy name":null,"privacy domain":null},{"name":"description","type":"VARCHAR(32700)","kind":"COLUMN","null?":"Y","default":null,"primary key":"N","unique key":"N","check":null,"expression":null,"comment":null,"policy name":null,"privacy domain":null},{"name":"designation","type":"VARCHAR(32700)","kind":"COLUMN","null?":"Y","default":null,"primary key":"N","unique key":"N","check":null,"expression":null,"comment":null,"policy name":null,"privacy domain":null},{"name":"points","type":"VARCHAR(32700)","kind":"COLUMN","null?":"Y","default":null,"primary key":"N","unique key":"N","check":null,"expression":null,"comment":null,"policy name":null,"privacy domain":null},{"name":"price","type":"VARCHAR(32700)","kind":"COLUMN","null?":"Y","default":null,"primary key":"N","unique key":"N","check":null,"expression":null,"comment":null,"policy name":null,"privacy domain":null},{"name":"province","type":"VARCHAR(32700)","kind":"COLUMN","null?":"Y","default":null,"primary key":"N","unique key":"N","check":null,"expression":null,"comment":null,"policy name":null,"privacy domain":null},{"name":"region_1","type":"VARCHAR(32700)","kind":"COLUMN","null?":"Y","default":null,"primary key":"N","unique key":"N","check":null,"expression":null,"comment":null,"policy name":null,"privacy domain":null},{"name":"region_2","type":"VARCHAR(32700)","kind":"COLUMN","null?":"Y","default":null,"primary key":"N","unique key":"N","check":null,"expression":null,"comment":null,"policy name":null,"privacy domain":null},{"name":"variety","type":"VARCHAR(32700)","kind":"COLUMN","null?":"Y","default":null,"primary key":"N","unique key":"N","check":null,"expression":null,"comment":null,"policy name":null,"privacy domain":null},{"name":"winery","type":"VARCHAR(32700)","kind":"COLUMN","null?":"Y","default":null,"primary key":"N","unique key":"N","check":null,"expression":null,"comment":null,"policy name":null,"privacy domain":null}

Think step by step.
Your task is to generate valid SQL Queries to query this table.
Make sure they are SNOWFLAKE compliant by adding double quotes around all relevant field names.
When building a query, make sure to also include the values being filtered on as part of the output.
Make sure you escape all the quote symbols when returning the JSON output.
Take your time.


Here are some example queries:
<ExampleQueries>
<ExampleQuery>
-- Query 1: Top 10 highest-rated French wines
SELECT "winery", "variety", "designation", "points"
FROM SEDEMO.SO_WINERY
WHERE LOWER("country") = 'france'
ORDER BY TRY_CAST("points" AS INT) DESC
LIMIT 10;
</ExampleQuery>

<ExampleQuery>
-- Query 2: Highest-rated wines under $20
SELECT "winery", "variety", "designation", "points", "price"
FROM SEDEMO.SO_WINERY
WHERE TRY_CAST("price" AS FLOAT) < 20
ORDER BY TRY_CAST("points" AS INT) DESC
LIMIT 10;
</ExampleQuery>

<ExampleQuery>
-- Query 3: Top 5 regions with highest average wine prices
SELECT "region_1", AVG(TRY_CAST("price" AS FLOAT)) as avg_price
FROM SEDEMO.SO_WINERY
WHERE "region_1" IS NOT NULL AND "region_1" != ''
GROUP BY "region_1"
ORDER BY avg_price DESC
LIMIT 5;
</ExampleQuery>

<ExampleQuery>
-- Query 4: Number of different wine varieties per country
SELECT "country", COUNT(DISTINCT "variety") as variety_count
FROM SEDEMO.SO_WINERY
WHERE "country" IS NOT NULL AND "country" != ''
GROUP BY "country"
ORDER BY variety_count DESC;
</ExampleQuery>

<ExampleQuery>
-- Query 5: Top 10 wineries with highest average points (min 5 wines)
SELECT "winery", AVG(TRY_CAST("points" AS FLOAT)) as avg_points, COUNT(*) as wine_count
FROM SEDEMO.SO_WINERY
WHERE "winery" IS NOT NULL AND "winery" != ''
GROUP BY "winery"
HAVING COUNT(*) > 5
ORDER BY avg_points DESC
LIMIT 10;
</ExampleQuery>
</ExampleQueries>

Generate a query for the following prompt:
{{prompt}}

Respond with a JSON object with the property "queryToExecute" and the value being the SQL query"""

st.title("SnapLogic Workshop - GenAI Wine DB")

url = "https://emea.snaplogic.com/api/1/rest/slsched/feed/ConnectFasterInc/0_StanGPT/GenAI/Winery_GetResults_Task"
token = "VclswzviMBM7ejrKrkqr9cOO1INdx2zJ"
st.header("")


if st.checkbox("Show SnapGPT Empty Value Prompts"):
    st.info("Set empty Region to 'Unknown'")
    st.text("$region_1==''?'Unknown':$region_1")
    st.text("$region_2==''?'Unknown':$region_2")
    st.write()
    st.info("Set empty designations to 'Unknown'")
    st.text("$designation == '' ? 'Unknown' : $designation")
    
    st.write()
if st.checkbox("Show Empty Property Filter"):
    st.info("This solves the empty header issue")
    st.text("$.filter((value, key) => key != '')")
    

if st.checkbox("Show Product Query Prompt"):
    st.text(injected_prompt)

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
