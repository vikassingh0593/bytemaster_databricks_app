# model_logic.py
import streamlit as st
import pandas as pd
from database_query import getData

def run_user_setting_ui():
    """All the complex logic for the UserSettings page goes here"""
    # st.subheader("Deep Dive Analysis")
    # st.write("Processing data...")
    
    # Example logic

    data = getData(tb_nm = 'bytemaster.appdata.UserSettings')
    st.table(data)
    
    if st.button("Save To Database"):
        st.success("Saved!")