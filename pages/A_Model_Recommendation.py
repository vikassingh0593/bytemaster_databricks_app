import streamlit as st
import pandas as pd
from datetime import datetime
from database_query import getData, writeData 
import time 

# --- 1. CONFIGURATION ---
DATASET_CONFIG = {
    "Substitution": {
        "table": "bytemaster.appdata.Substitution",
        "join_keys": ["ComponentId", "PlantId", "MaterialId"],
        "update_columns": ["QtyAtRisk", "PotentialSaving", "ActualSaving", "Feedback", "CreatedTimestamp", "UserEmail"],
        "filter_columns": ["ComponentId", "PlantId", "MaterialId", "UserEmail"]
    },
    "BatchReplacement": {
        "table": "bytemaster.appdata.BatchReplacement",
        "join_keys": ["ComponentId", "PlantId", "MaterialId"],
        "update_columns": ["QtyAtRisk", "PotentialSaving", "ActualSaving", "Feedback", "CreatedTimestamp", "UserEmail"],
        "filter_columns": ["ComponentId", "PlantId", "MaterialId", "UserEmail"]
    },
    "ProdIncrease": {
        "table": "bytemaster.appdata.ProdIncrease",
        "join_keys": ["ComponentId", "PlantId", "MaterialId"],
        "update_columns": ["QtyAtRisk", "PotentialSaving", "ActualSaving", "Feedback", "CreatedTimestamp", "UserEmail"],
        "filter_columns": ["ComponentId", "PlantId", "MaterialId", "UserEmail"]
    }
}

# --- 2. DATA LOADER ---
def load_data(model_name):
    try:
        table_name = DATASET_CONFIG[model_name]["table"]
        data = getData(tb_nm=table_name)
        
        # --- NEW CODE START ---
        # Ensure the column exists first
        if "Feedback" not in data.columns:
            data["Feedback"] = "Unactioned"
        
        # Fill missing (NaN) or empty strings with "Unactioned"
        data["Feedback"] = data["Feedback"].fillna("Unactioned")
        data["Feedback"] = data["Feedback"].replace("", "Unactioned")
        # --- NEW CODE END ---

        ts_col = "CreatedTimestamp" if "CreatedTimestamp" in data.columns else "Timestamp"
        if ts_col in data.columns:
            data[ts_col] = pd.to_datetime(data[ts_col]).dt.strftime("%Y-%m-%d %H:%M:%S")
        
        st.session_state.df_to_edit = data.copy()
        st.session_state.original_df = data.copy()
    except Exception as e:
        st.error(f"Error loading data for {model_name}: {e}")

# --- 3. MAIN UI FUNCTION ---
def run_model_ui():
    if "selected_model" not in st.session_state:
        st.session_state.selected_model = "Substitution"
    
    # Initialize a counter for the data_editor key to handle resets
    if "editor_key" not in st.session_state:
        st.session_state.editor_key = 0
    
    if "df_to_edit" not in st.session_state or st.session_state.df_to_edit is None:
        load_data(st.session_state.selected_model)

    # --- UI NAVIGATION ---
    nav_cols = st.columns([0.5, 0.5] + [1.5] * len(DATASET_CONFIG))

    with nav_cols[0]:
        if st.button("🏠", use_container_width=False):
            st.session_state.page = "home"
            st.rerun()

    for i, model in enumerate(DATASET_CONFIG.keys()):
        is_active = st.session_state.get("selected_model") == model
        if nav_cols[i+2].button(model, use_container_width=True, type="primary" if is_active else "secondary"):
            st.session_state.selected_model = model
            load_data(model)
            # Reset the editor key when switching tabs so we start fresh
            st.session_state.editor_key += 1
            st.rerun()

    st.markdown("<hr style='margin: 0px 0px 10px 0px; border-top: 1px solid #ddd;'>", unsafe_allow_html=True)

    current_model = st.session_state.selected_model
    current_cfg = DATASET_CONFIG[current_model]
    
    # --- 4. DYNAMIC FILTER SECTION ---
    df_display = st.session_state.df_to_edit.copy()
    
    # filter_cols = current_cfg.get("filter_columns", [])
    # if filter_cols:
    #     f_ui_cols = st.columns(len(filter_cols))
    #     for idx, col_name in enumerate(filter_cols):
    #         if col_name in df_display.columns:
    #             unique_vals = sorted(df_display[col_name].dropna().unique().tolist())
    #             selected = f_ui_cols[idx].multiselect(
    #                 f"{col_name}", 
    #                 options=unique_vals, 
    #                 key=f"f_{current_model}_{col_name}"
    #             )
    #             if selected:
    #                 df_display = df_display[df_display[col_name].isin(selected)]
    filter_cols = current_cfg.get("filter_columns", [])
    if filter_cols:
        # Create columns: Left (3 parts) for Filters, Right (1 part) Empty
        col_filters, col_empty = st.columns([4.5, 6.5])
        
        with col_filters:
            # Create sub-columns for each filter inside the Left block
            f_ui_cols = st.columns(len(filter_cols))
            for idx, col_name in enumerate(filter_cols):
                if col_name in df_display.columns:
                    unique_vals = sorted(df_display[col_name].dropna().unique().tolist())
                    selected = f_ui_cols[idx].multiselect(
                        f"{col_name}", 
                        options=unique_vals, 
                        key=f"f_{current_model}_{col_name}",
                        label_visibility="collapsed",
                        placeholder=f"{col_name}"
                    )
                    if selected:
                        df_display = df_display[df_display[col_name].isin(selected)]
        
        # Right side remains empty
        with col_empty:
            st.empty()

    # --- 5. DATA EDITOR ---
    if st.session_state.df_to_edit is not None:
        column_configuration = {}
        for col in st.session_state.df_to_edit.columns:
            
            # CONFIG: Feedback Dropdown
            if col == "Feedback":
                column_configuration[col] = st.column_config.SelectboxColumn(
                    label="Feedback",
                    width="small",
                    options=["Accept", "Reject", "Under Review", "Unactioned"],
                    required=True,
                    help="Select the final status for this item"
                )
            
            # CONFIG: ActualSaving (Make Editable)
            elif col == "ActualSaving":
                column_configuration[col] = st.column_config.NumberColumn(
                    label="Actual Saving",
                    width="small",
                    disabled=False, 
                    help="Value can only be edited if Feedback is NOT 'Unactioned'"
                )
            
            # CONFIG: All other columns disabled
            elif col == "UserEmail":
                column_configuration[col] = st.column_config.TextColumn(
                    label="User Email",
                    width="medium", 
                    disabled=True
                )
            else:
                column_configuration[col] = st.column_config.Column(disabled=True)

        # ---------------------------------------------------------
        # FIX: Use a Dynamic Key to allow resetting the widget
        # ---------------------------------------------------------
        dynamic_widget_key = f"editor_{current_model}_{st.session_state.editor_key}"

        st.data_editor(
            df_display,
            key=dynamic_widget_key,  # <--- Use the dynamic key here
            column_config=column_configuration,
            use_container_width=True,
            height=400,
            hide_index=True 
        )

        # # --- 6. PROCESS EDITS ---

        # --- 6. PROCESS EDITS ---
        # Retrieve state using the dynamic key
        dynamic_widget_key = f"editor_{current_model}_{st.session_state.editor_key}"
        state = st.session_state.get(dynamic_widget_key)
        
        if state and state.get("edited_rows"):
            user_email = st.context.headers.get("X-Forwarded-Email", "local_user")
            ts_col = "CreatedTimestamp" if "CreatedTimestamp" in df_display.columns else "Timestamp"
            
            valid_update_occurred = False
            validation_error = False
            
            for row_idx_in_filtered, changes in state["edited_rows"].items():
                actual_index = df_display.index[row_idx_in_filtered]
                
                # 1. Determine Effective Feedback Status
                current_feedback = changes.get("Feedback", st.session_state.df_to_edit.at[actual_index, "Feedback"])

                # 2. Validate ActualSaving Edit
                if "ActualSaving" in changes:
                    if current_feedback == "Unactioned":
                        # ERROR: User tried to edit saving without changing status
                        validation_error = True 
                    else:
                        st.session_state.df_to_edit.at[actual_index, "ActualSaving"] = changes["ActualSaving"]
                        valid_update_occurred = True

                # 3. Apply Feedback Edit
                if "Feedback" in changes:
                    st.session_state.df_to_edit.at[actual_index, "Feedback"] = changes["Feedback"]
                    valid_update_occurred = True
                
                # 4. Update Metadata
                if valid_update_occurred:
                    st.session_state.df_to_edit.at[actual_index, ts_col] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    st.session_state.df_to_edit.at[actual_index, "UserEmail"] = user_email
            
            # ---------------------------------------------------------
            # LOGIC: Handle Reruns & Errors
            # ---------------------------------------------------------
            if validation_error:
                # SHOW ERROR
                st.toast("⚠️ You must update 'Feedback' status (e.g., to 'Accept') before entering Actual Saving!", icon="🚫")
                
                # DELAY: Pause for 2 seconds so the user sees the toast
                time.sleep(2)
                
                # RESET: Increment key to wipe the invalid input
                st.session_state.editor_key += 1
                st.rerun()

            elif valid_update_occurred:
                # SUCCESS: Immediate rerun to reflect changes
                st.rerun()

        # --- 7. SAVE ACTION ---
        st.markdown("<hr style='margin: 0px 0px 10px 0px; border-top: 1px solid #ddd;'>", unsafe_allow_html=True)
        if st.button("Save to Database", type="primary", use_container_width=False):
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
                        # Optional: Reset key after save to be clean
                        st.session_state.editor_key += 1
                        st.rerun() 
                except Exception as e:
                    st.error(f"Failed to save: {e}")
            else:
                st.info("No changes detected to save.")
    else:
        st.warning("No data found.")