import streamlit as st

from statics import STATICS

st.set_page_config(
    layout="wide"
)

st.markdown(STATICS.readme.read_text())