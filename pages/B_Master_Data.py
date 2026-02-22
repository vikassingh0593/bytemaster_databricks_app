import streamlit as st
import pandas as pd
from datetime import datetime
import time
from database_query import getData, writeData 
from config.configuration import DATASET_CONFIG

# --- 1. DYNAMIC CATEGORY ASSIGNMENT ---
# Defines exactly what shows up on the screen for this Master Data page
MASTER_TABLES = ["ComponentExclusion", "DimSubstitution"]

# --- 2. DATA LOADER ---
def load_data(master_name):
    try:
        table_name = DATASET_CONFIG[master_name]["table"]
        # Assuming Master tables just need Active records, but adjust SqlStr if needed
        data = getData(tb_nm=table_name, SqlStr='where ActiveFlag = "Y" ')
        
        # Ensure timestamp format
        ts_col = "UpdatedTimestamp"
        if ts_col in data.columns:
            data[ts_col] = pd.to_datetime(data[ts_col]).dt.strftime("%Y-%m-%d %H:%M:%S")
        
        # Ensure ActiveFlag exists
        if "ActiveFlag" not in data.columns:
            data["ActiveFlag"] = "Y"
        
        st.session_state.df_to_edit = data.copy()
        st.session_state.original_df = data.copy()
        st.session_state.loaded_master_type = master_name
        
    except Exception as e:
        st.error(f"Error loading data for {master_name}: {e}")

# --- 3. MAIN UI FUNCTION ---
def run_master_ui():
    # 🆕 SAFETY CHECK: Ensure selected master is one of the allowed tables
    if "master_selection" not in st.session_state or st.session_state.master_selection not in MASTER_TABLES:
        st.session_state.master_selection = MASTER_TABLES[0]
    
    # Initialize Editor Key for resetting the widget
    if "master_editor_key" not in st.session_state:
        st.session_state.master_editor_key = 0

    # Check for data mismatch or missing data
    is_data_mismatch = st.session_state.get("loaded_master_type") != st.session_state.master_selection
    
    if "df_to_edit" not in st.session_state or st.session_state.df_to_edit is None or is_data_mismatch:
        load_data(st.session_state.master_selection)
        st.session_state.master_editor_key += 1 # Reset editor on load
        st.rerun()

    current_data = st.session_state.master_selection
    current_cfg = DATASET_CONFIG[current_data]

    # ==========================================
    # 🆕 UI NAVIGATION (Filtered to MASTER_TABLES)
    # ==========================================
    # Added a spacer [5.0] at the end so buttons don't stretch
    nav_cols = st.columns([0.5, 0.5] + [1.5] * len(MASTER_TABLES) + [5.0])

    with nav_cols[0]:
        if st.button("🏠", use_container_width=False):
            st.session_state.page = "home"
            # Optional cleanup
            if "df_to_edit" in st.session_state: del st.session_state.df_to_edit
            if "loaded_master_type" in st.session_state: del st.session_state.loaded_master_type
            st.rerun()

    # Loop ONLY through the specific master tables
    for i, model in enumerate(MASTER_TABLES):
        is_active = st.session_state.get("master_selection") == model
        if nav_cols[i+2].button(model, use_container_width=True, type="primary" if is_active else "secondary"):
            st.session_state.master_selection = model
            st.rerun()

    st.markdown("<hr style='margin: 0px 0px 10px 0px; border-top: 1px solid #ddd;'>", unsafe_allow_html=True)

    # --- 4. LAYOUT: FILTERS (Compact Left) - SPACE - ADD RECORD (Right) ---
    if st.session_state.df_to_edit is not None:
        df_display = st.session_state.df_to_edit.copy()

        col_filters, col_spacer, col_add = st.columns([4.5, 5.7, 0.8], gap="small")
        
        # --- LEFT: FILTERS ---
        with col_filters:
            # Safely exclude RunID just in case it ever appears in a master table
            filter_cols = [col for col in current_cfg.get("filter_columns", []) if col != "RunID"]
            
            if filter_cols:
                f_ui_cols = st.columns(len(filter_cols))
                for idx, col_name in enumerate(filter_cols):
                    if col_name in df_display.columns:
                        unique_vals = sorted(df_display[col_name].dropna().unique().tolist())
                        selected = f_ui_cols[idx].multiselect(
                            f"{col_name}", 
                            options=unique_vals, 
                            key=f"f_{current_data}_{col_name}",
                            label_visibility="collapsed",
                            placeholder=f"{col_name}"
                        )
                        if selected:
                            df_display = df_display[df_display[col_name].isin(selected)]
        
        # --- MIDDLE: SPACER ---
        with col_spacer:
            st.empty() 

        # --- RIGHT: ADD RECORD POPUP ---
        with col_add:
            with st.popover("➕ Add", use_container_width=False):
                st.write(f"**Add to {current_data}**")
                with st.form("add_master_record", clear_on_submit=True):
                    # DYNAMIC FIELDS
                    new_comp_id = st.text_input("ComponentId", placeholder="Required")
                    new_plant_id = st.text_input("PlantId", placeholder="Required")
                    
                    new_sub_of = None
                    # 🆕 Updated to check for DimSubstitution
                    if current_data == "DimSubstitution":
                        new_sub_of = st.text_input("SubstituteOf", placeholder="Required")
                    
                    new_active = st.selectbox("ActiveFlag", options=["Y", "N"])
                    
                    submitted = st.form_submit_button("Add Row", type="primary")
                    
                    if submitted:
                        # Validation
                        valid = True
                        if not new_comp_id or not new_plant_id:
                            valid = False
                        if current_data == "DimSubstitution" and not new_sub_of:
                            valid = False
                            
                        if valid:
                            user_email = st.context.headers.get("X-Forwarded-Email", "user@example.com")
                            ts_col = "UpdatedTimestamp"
                            
                            new_row_data = {
                                "ComponentId": new_comp_id,
                                "PlantId": new_plant_id,
                                "ActiveFlag": new_active,
                                "UserEmail": user_email,
                                ts_col: datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            }
                            
                            if current_data == "DimSubstitution":
                                new_row_data["SubstituteOf"] = new_sub_of

                            new_row_df = pd.DataFrame([new_row_data])
                            st.session_state.df_to_edit = pd.concat(
                                [st.session_state.df_to_edit, new_row_df], 
                                ignore_index=True
                            )
                            
                            st.toast("✅ Row added! Click Save to Database.", icon="💾")
                            st.session_state.master_editor_key += 1
                            time.sleep(0.5)
                            st.rerun()
                        else:
                            st.error("Please fill in all required fields.")

        # --- 5. DATA EDITOR ---
        column_configuration = {}
        for col in st.session_state.df_to_edit.columns:
            if col == "ActiveFlag":
                column_configuration[col] = st.column_config.SelectboxColumn(
                    label="ActiveFlag",
                    width="medium",
                    options=["Y", "N"],
                    required=True
                )
            else:
                column_configuration[col] = st.column_config.Column(disabled=True)

        editor_key = f"editor_{current_data}_{st.session_state.master_editor_key}"

        st.data_editor(
            df_display,
            key=editor_key,
            column_config=column_configuration,
            use_container_width=True,
            height=388,
            hide_index=True 
        )

        # --- 6. PROCESS EDITS ---
        state = st.session_state.get(editor_key)
        
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
        st.markdown("<hr style='margin: 0px 0px 10px 0px; border-top: 1px solid #ddd;'>", unsafe_allow_html=True)
        if st.button("Save to Database", type="primary", use_container_width=False):
            df_curr = st.session_state.df_to_edit.reset_index(drop=True)
            df_orig = st.session_state.original_df.reset_index(drop=True)
            
            rows_to_save = pd.DataFrame()
            
            # 1. Identify New Rows
            len_orig = len(df_orig)
            len_curr = len(df_curr)
            
            if len_curr > len_orig:
                new_rows = df_curr.iloc[len_orig:]
                rows_to_save = pd.concat([rows_to_save, new_rows])
            
            # 2. Identify Modified Rows
            df_curr_overlap = df_curr.iloc[:len_orig]
            
            if not df_curr_overlap.empty and not df_orig.empty:
                changed_mask = ~(df_curr_overlap.fillna('').astype(str).eq(df_orig.fillna('').astype(str))).all(axis=1)
                modified_rows = df_curr_overlap[changed_mask]
                rows_to_save = pd.concat([rows_to_save, modified_rows])

            if not rows_to_save.empty:
                try:
                    with st.spinner(f"Updating {len(rows_to_save)} rows..."):
                        writeData(rows_to_save, current_cfg)
                        st.success(f"Successfully updated/inserted {len(rows_to_save)} rows!")
                        st.session_state.original_df = df_curr.copy()
                        st.session_state.master_editor_key += 1
                        st.rerun()
                except Exception as e:
                    st.error(f"Failed to save: {e}")
            else:
                st.info("No changes detected to save.")
    else:
        st.warning("No data found.")