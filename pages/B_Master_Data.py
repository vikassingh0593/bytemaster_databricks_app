import streamlit as st
import pandas as pd
from datetime import datetime
from database_query import getData, writeData 

# --- 1. CONFIGURATION ---
DATASET_CONFIG = {
    "ComponentExclusion": {
        "table": "bytemaster.appdata.DimComponentExclusion",
        "join_keys": ["ComponentId", "PlantId"],
        "update_columns": ["ActiveFlag", "UpdatedTimestamp", "UserEmail"],
        "filter_columns": ["ComponentId", "PlantId", "UserEmail"]
    },
    "Substitution": {
        "table": "bytemaster.appdata.DimSubstitution",
        "join_keys": ["ComponentId", "PlantId", "SubstituteOf"],
        "update_columns": ["ActiveFlag", "UpdatedTimestamp", "UserEmail"],
        "filter_columns": ["ComponentId", "PlantId", "MaterialId", "UserEmail"]
    },
}

# --- 2. DATA LOADER ---
def load_data(master_name):
    try:
        table_name = DATASET_CONFIG[master_name]["table"]
        data = getData(tb_nm=table_name)
        
        ts_col = "UpdatedTimestamp" if "UpdatedTimestamp" in data.columns else "Timestamp"
        if ts_col in data.columns:
            data[ts_col] = pd.to_datetime(data[ts_col]).dt.strftime("%Y-%m-%d %H:%M:%S")
        
        st.session_state.df_to_edit = data.copy()
        st.session_state.original_df = data.copy()
    except Exception as e:
        st.error(f"Error loading data for {master_name}: {e}")

# --- 3. MAIN UI FUNCTION ---
def run_master_ui():
    if "master_selection" not in st.session_state:
        st.session_state.master_selection = "ComponentExclusion"
    
    if "df_to_edit" not in st.session_state or st.session_state.df_to_edit is None:
        load_data(st.session_state.master_selection)

    # --- UI NAVIGATION ---

    # 1. Create columns: 1 for Back + number of models in your config
    # Example: if you have 3 models, this creates 4 columns total.
    # Ratios explained: 
    # 0.6: Very small Back button
    # 0.5: Empty space (the "gap" to move models right)
    # [1.5] * len: The model buttons
    nav_cols = st.columns([0.5, 0.5] + [1.5] * len(DATASET_CONFIG))
    # nav_cols = st.columns([1] + [1.5] * len(DATASET_CONFIG))

    # 2. Place the Back Button in the very first column
    with nav_cols[0]:
        if st.button("🏠", use_container_width=False):
            st.session_state.page = "home"
            st.rerun()

    # 3. Place the Model Tabs (Starting from index 2)
    for i, model in enumerate(DATASET_CONFIG.keys()):
        is_active = st.session_state.get("master_selection") == model
        # Use i + 2 to skip both the Back button and the Spacer
        if nav_cols[i+2].button(model, use_container_width=True, type="primary" if is_active else "secondary"):
            st.session_state.master_selection = model
            load_data(model)
            st.rerun()

    # 4. IMPORTANT: Exit the columns block here. 
    # Anything written below this will automatically be "Full Width" 
    # spanning from the left edge of the Back button to the right edge of the last Model tab.

    # st.divider() # Thin line to separate the nav from the data
    st.markdown("<hr style='margin: 0px 0px 10px 0px; border-top: 1px solid #ddd;'>", unsafe_allow_html=True)

    current_data = st.session_state.master_selection
    current_cfg = DATASET_CONFIG[current_data]
    
    # --- 4. DYNAMIC FILTER SECTION (No Dropdown) ---
    df_display = st.session_state.df_to_edit.copy()
    
    filter_cols = current_cfg.get("filter_columns", [])
    if filter_cols:
        # st.write(f"### Filters for {current_data}")
        f_ui_cols = st.columns(len(filter_cols))
        for idx, col_name in enumerate(filter_cols):
            if col_name in df_display.columns:
                unique_vals = sorted(df_display[col_name].dropna().unique().tolist())
                selected = f_ui_cols[idx].multiselect(
                    f"{col_name}", 
                    options=unique_vals, 
                    key=f"f_{current_data}_{col_name}"
                )
                if selected:
                    df_display = df_display[df_display[col_name].isin(selected)]

    # --- 5. DATA EDITOR ---
    if st.session_state.df_to_edit is not None:
        column_configuration = {}
        for col in st.session_state.df_to_edit.columns:
            if col == "ActiveFlag":
                column_configuration[col] = st.column_config.TextColumn("ActiveFlag", width="large")
            else:
                column_configuration[col] = st.column_config.Column(disabled=True)

        st.data_editor(
            df_display,
            key="editor_widget",
            column_config=column_configuration,
            use_container_width=True,
            hide_index=False 
        )

        # --- 6. PROCESS EDITS ---
        state = st.session_state.get("editor_widget")
        if state and state.get("edited_rows"):
            user_email = st.context.headers.get("X-Forwarded-Email", "local_user")
            ts_col = "UpdatedTimestamp" if "UpdatedTimestamp" in df_display.columns else "Timestamp"
            
            has_changes = False
            for row_idx_in_filtered, changes in state["edited_rows"].items():
                if "ActiveFlag" in changes:
                    actual_index = df_display.index[row_idx_in_filtered]
                    st.session_state.df_to_edit.at[actual_index, "ActiveFlag"] = changes["ActiveFlag"]
                    st.session_state.df_to_edit.at[actual_index, ts_col] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    st.session_state.df_to_edit.at[actual_index, "UserEmail"] = user_email
                    has_changes = True
            
            if has_changes:
                st.rerun()

        # --- 7. SAVE ACTION ---
        # st.divider()
        st.markdown("<hr style='margin: 0px 0px 10px 0px; border-top: 1px solid #ddd;'>", unsafe_allow_html=True)
        if st.button("Save Changes to Databricks", type="primary", use_container_width=False):
            df_curr = st.session_state.df_to_edit.reset_index(drop=True)
            df_orig = st.session_state.original_df.reset_index(drop=True)
            
            changed_mask = ~(df_curr.fillna('').eq(df_orig.fillna(''))).all(axis=1)
            changed_rows = df_curr[changed_mask].copy()

            if not changed_rows.empty:
                try:
                    with st.spinner(f"Updating {len(changed_rows)} rows..."):
                        writeData(changed_rows, current_cfg)
                        st.success(f"Successfully updated {len(changed_rows)} rows!")
                        st.session_state.original_df = df_curr.copy()
                except Exception as e:
                    st.error(f"Failed to save: {e}")
            else:
                st.info("No changes detected to save.")
    else:
        st.warning("No data found.")