import streamlit as st
import pandas as pd
from database_query import getData

# --- 1. CACHED DATA FETCHING ---
# This prevents the app from re-querying Databricks on every button click
# @st.cache_data(ttl=600)  # Cache results for 10 minutes
def get_cached_master_data(table_name):
    return getData(tb_nm=table_name)

def run_master_ui():
    # Initialize selection state
    if "master_selection" not in st.session_state:
        st.session_state.master_selection = "DimComponentExclusion"

    # CSS for Buttons
    st.markdown("""
        <style>
        div.stButton > button {
            height: 50px;
            border-radius: 10px;
            font-size: 18px;
            font-weight: bold;
        }
        </style>
    """, unsafe_allow_html=True)

    # 2. Navigation Tabs
    col1, col2 = st.columns(2)

    with col1:
        # Use type="primary" to highlight the active selection
        btn_type = "primary" if st.session_state.master_selection == "DimComponentExclusion" else "secondary"
        if st.button("🔄 DimComponentExclusion", use_container_width=True, type=btn_type):
            st.session_state.master_selection = "DimComponentExclusion"
            st.rerun() # Force immediate refresh
    
    with col2:
        btn_type = "primary" if st.session_state.master_selection == "DimSubstitution" else "secondary"
        if st.button("📉 DimSubstitution", use_container_width=True, type=btn_type):
            st.session_state.master_selection = "DimSubstitution"
            st.rerun() # Force immediate refresh

    st.divider() 

    # 3. MAPPING TABLES
    table_map = {
        "DimComponentExclusion": "bytemaster.appdata.DimComponentExclusion",
        "DimSubstitution": "bytemaster.appdata.DimSubstitution"
    }

    current_selection = st.session_state.master_selection
    target_table = table_map.get(current_selection)

    # 4. DYNAMIC DATA DISPLAY
    if target_table:
        with st.spinner(f"Fetching {current_selection}..."):
            try:
                # Use the cached function here
                data = get_cached_master_data(target_table)
                
                # Display dataframe
                st.dataframe(data, use_container_width=True, hide_index=True)
                
                # Summary info
                st.caption(f"Showing {len(data)} rows from {target_table}")
                
            except Exception as e:
                st.error(f"Error loading data: {e}")

    st.write("") # Spacer

    # 5. Global Action
    if st.button("Save To Databricks", type="primary"):
        # Clear cache after saving to ensure the next view shows the updated data
        get_cached_master_data.clear()
        st.success(f"Successfully saved {st.session_state.master_selection} data to Databricks!")
