import streamlit as st

st.set_page_config(layout="wide")
st.title("Page 3: Manual Data Entry")

st.markdown("""
Paste the measured values from the CSV (Page 1) into the Excel template (Page 2).

1. Open the CSV downloaded from **Page 1**
2. Open the Excel template downloaded from **Page 2**
3. Paste the Ids values into the blank cells of each table
4. Upload the filled Excel on **Page 4**
""")