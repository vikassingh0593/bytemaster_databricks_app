# import streamlit as st
# import pandas as pd
# from datetime import datetime
# import time
# from database_query import getData, writeData, deleteData

# # --- 1. CONFIGURATION ---
# DATASET_CONFIG = {
#     "UserSettings": {
#         "table": "bytemaster.appdata.UserSettings",
#         "join_keys": ["PlantId"], 
#         "update_columns": ["ApprovedMailID", "UserEmail", "UpdatedTimestamp"],
#         "filter_columns": ["PlantId", "ApprovedMailID"]
#     }
# }

# # --- 2. DATA LOADER ---
# def load_user_data():
#     try:
#         table_name = DATASET_CONFIG["UserSettings"]["table"]
#         data = getData(tb_nm=table_name, ActiveFlag = None)
        
#         # Format Timestamp
#         ts_col = "UpdatedTimestamp"
#         if ts_col in data.columns:
#             data[ts_col] = pd.to_datetime(data[ts_col]).dt.strftime("%Y-%m-%d %H:%M:%S")
        
#         # --- MODIFIED: Add 'Delete' column at the END (Far Right) ---
#         if "Delete" not in data.columns:
#             data["Delete"] = False  # Appends to the end of the DataFrame
        
#         st.session_state.user_df_to_edit = data.copy()
#         st.session_state.user_original_df = data.copy()
        
#     except Exception as e:
#         st.error(f"Error loading UserSettings: {e}")

# # --- 3. MAIN UI FUNCTION ---
# def run_user_setting_ui():
    
#     # Initialize Session State
#     if "user_editor_key" not in st.session_state:
#         st.session_state.user_editor_key = 0
        
#     if "user_df_to_edit" not in st.session_state or st.session_state.user_df_to_edit is None:
#         load_user_data()
#         st.rerun()

#     current_cfg = DATASET_CONFIG["UserSettings"]
    
#     # --- 4. LAYOUT ---
#     if st.session_state.user_df_to_edit is not None:
#         df_display = st.session_state.user_df_to_edit.copy()

#         col_filters, col_spacer, col_add = st.columns([2.5, 6.7, 0.8], gap="small")
        
#         # Filters
#         with col_filters:
#             filter_cols = current_cfg.get("filter_columns", [])
#             if filter_cols:
#                 f_ui_cols = st.columns(len(filter_cols))
#                 for idx, col_name in enumerate(filter_cols):
#                     if col_name in df_display.columns:
#                         unique_vals = sorted(df_display[col_name].dropna().unique().tolist())
#                         selected = f_ui_cols[idx].multiselect(
#                             f"{col_name}", 
#                             options=unique_vals, 
#                             key=f"user_filter_{col_name}",
#                             label_visibility="collapsed",
#                             placeholder=f"{col_name}"
#                         )
#                         if selected:
#                             df_display = df_display[df_display[col_name].isin(selected)]
        
#         with col_spacer:
#             st.empty() 

#         # Add Record
#         with col_add:
#             with st.popover("➕ Add", use_container_width=False):
#                 st.write("**Add User Setting**")
#                 with st.form("add_user_form", clear_on_submit=True):
#                     new_plant = st.text_input("PlantId", placeholder="e.g., P01")
#                     new_email = st.text_input("ApprovedMailID", placeholder="e.g., user@example.com")
                    
#                     submitted = st.form_submit_button("Add Row", type="primary")
                    
#                     if submitted:
#                         if new_plant and new_email:
#                             existing_plants = st.session_state.user_df_to_edit["PlantId"].astype(str).tolist()
                            
#                             if new_plant in existing_plants:
#                                 st.error(f"PlantId '{new_plant}' already exists!")
#                             else:
#                                 ts_col = "UpdatedTimestamp" if "UpdatedTimestamp" in st.session_state.user_df_to_edit.columns else "Timestamp"
                                
#                                 new_row_data = {
#                                     "PlantId": new_plant,
#                                     "ApprovedMailID": new_email,
#                                     "UserEmail": st.context.headers.get("X-Forwarded-Email", "user@example.com"),
#                                     ts_col: datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
#                                     "Delete": False # Ensure this is last to match structure
#                                 }
                                
#                                 new_row_df = pd.DataFrame([new_row_data])
#                                 st.session_state.user_df_to_edit = pd.concat(
#                                     [st.session_state.user_df_to_edit, new_row_df], 
#                                     ignore_index=True
#                                 )
                                
#                                 st.toast("Row added! Click 'Save' to commit.", icon="💾")
#                                 st.session_state.user_editor_key += 1
#                                 time.sleep(0.5)
#                                 st.rerun()
#                         else:
#                             st.error("Both PlantId and Email are required.")

#         # --- 5. DATA EDITOR ---
#         column_configuration = {
#             "PlantId": st.column_config.TextColumn("PlantId", width="medium", disabled=True), 
#             "ApprovedMailID": st.column_config.TextColumn("ApprovedMailID", width="large", required=True),
#             "UserEmail": st.column_config.TextColumn("UserEmail", width="large", disabled=True),
#             "UpdatedTimestamp": st.column_config.TextColumn("Timestamp", disabled=True, width="medium"),
            
#             # --- DELETE COLUMN CONFIGURATION ---
#             "Delete": st.column_config.CheckboxColumn(
#                 "❌",
#                 help="Check to delete",
#                 default=False,
#                 width="small" 
#             )
#         }

#         editor_key = f"user_editor_{st.session_state.user_editor_key}"

#         num_rows = len(df_display)
#         calculated_height = (num_rows + 1) * 35 + 3 
#         final_height = min(calculated_height, 388)

#         st.data_editor(
#             df_display,
#             key=editor_key,
#             column_config=column_configuration,
#             use_container_width=True,
#             height=final_height,
#             hide_index=True 
#         )

#         # --- 6. PROCESS EDITS ---
#         state = st.session_state.get(editor_key)
        
#         if state and state.get("edited_rows"):
#             ts_col = "UpdatedTimestamp"
            
#             has_changes = False
#             for row_idx_in_filtered, changes in state["edited_rows"].items():
#                 actual_index = df_display.index[row_idx_in_filtered]
                
#                 # Apply changes
#                 for key, value in changes.items():
#                     st.session_state.user_df_to_edit.at[actual_index, key] = value
                
#                 # Update timestamp ONLY if the change wasn't just the Delete checkbox
#                 if "Delete" not in changes or len(changes) > 1:
#                     st.session_state.user_df_to_edit.at[actual_index, ts_col] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
#                 has_changes = True
            
#             if has_changes:
#                 st.rerun()

#         # --- 7. SAVE ACTION ---
#         st.markdown("<hr style='margin: 0px 0px 10px 0px; border-top: 1px solid #ddd;'>", unsafe_allow_html=True)
#         if st.button("Save Changes to Database", type="primary", use_container_width=False):
            
#             full_df = st.session_state.user_df_to_edit
            
#             rows_to_delete = full_df[full_df["Delete"] == True]
#             rows_to_keep = full_df[full_df["Delete"] == False].drop(columns=["Delete"])
#             df_orig = st.session_state.user_original_df.drop(columns=["Delete"], errors='ignore')

#             try:
#                 msg_list = []
                
#                 with st.spinner("Processing..."):
#                     # A) EXECUTE DELETE
#                     if not rows_to_delete.empty:
#                         deleteData(rows_to_delete, current_cfg)
#                         msg_list.append(f"Deleted {len(rows_to_delete)} rows.")

#                     # B) EXECUTE UPSERT
#                     df_curr_chk = rows_to_keep.reset_index(drop=True)
#                     df_orig_chk = df_orig.reset_index(drop=True)

#                     new_rows = pd.DataFrame()
#                     if len(df_curr_chk) > len(df_orig_chk):
#                         new_rows = df_curr_chk.iloc[len(df_orig_chk):]
                    
#                     modified_rows = pd.DataFrame()
#                     overlap_len = min(len(df_curr_chk), len(df_orig_chk))
#                     if overlap_len > 0:
#                         curr_overlap = df_curr_chk.iloc[:overlap_len]
#                         orig_overlap = df_orig_chk.iloc[:overlap_len]
#                         changed_mask = ~(curr_overlap.fillna('').astype(str).eq(orig_overlap.fillna('').astype(str))).all(axis=1)
#                         modified_rows = curr_overlap[changed_mask]
                    
#                     final_save_df = pd.concat([new_rows, modified_rows])
                    
#                     if not final_save_df.empty:
#                          writeData(final_save_df, current_cfg)
#                          msg_list.append(f"Updated/Added {len(final_save_df)} rows.")
                    
#                     # C) REFRESH STATE
#                     if msg_list:
#                         st.success(" | ".join(msg_list))
#                         st.session_state.user_original_df = rows_to_keep.copy()
                        
#                         # Reset Delete flags and put column at the end again
#                         rows_to_keep["Delete"] = False
#                         st.session_state.user_df_to_edit = rows_to_keep.copy()
                        
#                         st.session_state.user_editor_key += 1
#                         time.sleep(1)
#                         st.rerun()
#                     else:
#                         st.info("No changes to save.")

#             except Exception as e:
#                 st.error(f"Save failed: {e}")

#     else:
#         st.warning("No data found.")

import streamlit as st
import pandas as pd
from datetime import datetime
import time
import re # 🆕 Added for Regex validation
from database_query import getData, writeData, deleteData

# --- 1. CONFIGURATION ---
DATASET_CONFIG = {
    "UserSettings": {
        "table": "bytemaster.appdata.UserSettings",
        "join_keys": ["PlantId"], 
        "update_columns": ["ApprovedMailID", "UserEmail", "UpdatedTimestamp"],
        "filter_columns": ["PlantId", "ApprovedMailID"]
    }
}

# --- 🆕 1.5 EMAIL VALIDATOR HELPER ---
def validate_email_input(email_str):
    """
    Validates a comma-separated string of email addresses.
    Returns: (is_valid: bool, error_message: str)
    """
    if not email_str or str(email_str).strip() == "":
        return False, "Email field cannot be empty."
        
    emails = [e.strip() for e in str(email_str).split(',')]
    email_regex = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")
    
    for e in emails:
        if not e:
            return False, "Detected an empty email. Please remove extra commas."
        if " " in e:
            return False, "Please separate multiple email IDs with a comma (,)."
        if not email_regex.match(e):
            return False, f"Invalid email format: '{e}'. Example: vikas@gmail.com"
            
    return True, ""

# --- 2. DATA LOADER ---
def load_user_data():
    try:
        table_name = DATASET_CONFIG["UserSettings"]["table"]
        data = getData(tb_nm=table_name, ActiveFlag = None)
        
        # Format Timestamp
        ts_col = "UpdatedTimestamp"
        if ts_col in data.columns:
            data[ts_col] = pd.to_datetime(data[ts_col]).dt.strftime("%Y-%m-%d %H:%M:%S")
        
        # Add 'Delete' column at the END
        if "Delete" not in data.columns:
            data["Delete"] = False  
        
        st.session_state.user_df_to_edit = data.copy()
        st.session_state.user_original_df = data.copy()
        
    except Exception as e:
        st.error(f"Error loading UserSettings: {e}")

# --- 3. MAIN UI FUNCTION ---
def run_user_setting_ui():
    
    # Initialize Session State
    if "user_editor_key" not in st.session_state:
        st.session_state.user_editor_key = 0
        
    if "user_df_to_edit" not in st.session_state or st.session_state.user_df_to_edit is None:
        load_user_data()
        st.rerun()

    current_cfg = DATASET_CONFIG["UserSettings"]
    
    # --- 4. LAYOUT ---
    if st.session_state.user_df_to_edit is not None:
        df_display = st.session_state.user_df_to_edit.copy()

        col_filters, col_spacer, col_add = st.columns([2.5, 6.7, 0.8], gap="small")
        
        # Filters
        with col_filters:
            filter_cols = current_cfg.get("filter_columns", [])
            if filter_cols:
                f_ui_cols = st.columns(len(filter_cols))
                for idx, col_name in enumerate(filter_cols):
                    if col_name in df_display.columns:
                        unique_vals = sorted(df_display[col_name].dropna().unique().tolist())
                        selected = f_ui_cols[idx].multiselect(
                            f"{col_name}", 
                            options=unique_vals, 
                            key=f"user_filter_{col_name}",
                            label_visibility="collapsed",
                            placeholder=f"{col_name}"
                        )
                        if selected:
                            df_display = df_display[df_display[col_name].isin(selected)]
        
        with col_spacer:
            st.empty() 

        # Add Record
        with col_add:
            with st.popover("➕ Add", use_container_width=False):
                st.write("**Add User Setting**")
                with st.form("add_user_form", clear_on_submit=False): # Changed to False to keep input if error occurs
                    new_plant = st.text_input("PlantId", placeholder="e.g., P01")
                    new_email = st.text_input("ApprovedMailID", placeholder="e.g., user1@email.com, user2@email.com")
                    
                    submitted = st.form_submit_button("Add Row", type="primary")
                    
                    if submitted:
                        if new_plant and new_email:
                            # 🆕 1. Validate the email input first
                            is_valid, err_msg = validate_email_input(new_email)
                            
                            if not is_valid:
                                st.error(err_msg)
                            else:
                                existing_plants = st.session_state.user_df_to_edit["PlantId"].astype(str).tolist()
                                
                                if new_plant in existing_plants:
                                    st.error(f"PlantId '{new_plant}' already exists!")
                                else:
                                    ts_col = "UpdatedTimestamp" if "UpdatedTimestamp" in st.session_state.user_df_to_edit.columns else "Timestamp"
                                    
                                    # Format the emails properly (removes accidental spaces around commas)
                                    clean_emails = ", ".join([e.strip() for e in new_email.split(',')])

                                    new_row_data = {
                                        "PlantId": new_plant,
                                        "ApprovedMailID": clean_emails,
                                        "UserEmail": st.context.headers.get("X-Forwarded-Email", "user@example.com"),
                                        ts_col: datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                        "Delete": False 
                                    }
                                    
                                    new_row_df = pd.DataFrame([new_row_data])
                                    st.session_state.user_df_to_edit = pd.concat(
                                        [st.session_state.user_df_to_edit, new_row_df], 
                                        ignore_index=True
                                    )
                                    
                                    st.toast("Row added! Click 'Save' to commit.", icon="💾")
                                    st.session_state.user_editor_key += 1
                                    time.sleep(0.5)
                                    st.rerun()
                        else:
                            st.error("Both PlantId and Email are required.")

        # --- 5. DATA EDITOR ---
        column_configuration = {
            "PlantId": st.column_config.TextColumn("PlantId", width="medium", disabled=True), 
            "ApprovedMailID": st.column_config.TextColumn("ApprovedMailID", width="large", required=True),
            "UserEmail": st.column_config.TextColumn("UserEmail", width="large", disabled=True),
            "UpdatedTimestamp": st.column_config.TextColumn("Timestamp", disabled=True, width="medium"),
            "Delete": st.column_config.CheckboxColumn("❌", help="Check to delete", default=False, width="small")
        }

        editor_key = f"user_editor_{st.session_state.user_editor_key}"

        num_rows = len(df_display)
        calculated_height = (num_rows + 1) * 35 + 3 
        final_height = min(calculated_height, 388)

        st.data_editor(
            df_display,
            key=editor_key,
            column_config=column_configuration,
            use_container_width=True,
            height=final_height,
            hide_index=True 
        )

        # --- 6. PROCESS EDITS ---
        state = st.session_state.get(editor_key)
        
        if state and state.get("edited_rows"):
            ts_col = "UpdatedTimestamp"
            has_changes = False
            has_error = False
            
            for row_idx_in_filtered, changes in state["edited_rows"].items():
                actual_index = df_display.index[row_idx_in_filtered]
                
                # 🆕 2. Validate edits made directly in the data editor
                if "ApprovedMailID" in changes:
                    is_valid, err_msg = validate_email_input(changes["ApprovedMailID"])
                    if not is_valid:
                        st.error(f"Row edit failed: {err_msg}")
                        has_error = True
                        continue # Skip applying this change
                
                # Apply changes if valid
                for key, value in changes.items():
                    if key == "ApprovedMailID":
                        # Clean it up before saving
                        value = ", ".join([e.strip() for e in value.split(',')])
                    st.session_state.user_df_to_edit.at[actual_index, key] = value
                
                if "Delete" not in changes or len(changes) > 1:
                    st.session_state.user_df_to_edit.at[actual_index, ts_col] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                has_changes = True
            
            if has_changes and not has_error:
                st.rerun()

        # --- 7. SAVE ACTION ---
        st.markdown("<hr style='margin: 0px 0px 10px 0px; border-top: 1px solid #ddd;'>", unsafe_allow_html=True)
        if st.button("Save Changes to Database", type="primary", use_container_width=False):
            
            full_df = st.session_state.user_df_to_edit
            
            rows_to_delete = full_df[full_df["Delete"] == True]
            rows_to_keep = full_df[full_df["Delete"] == False].drop(columns=["Delete"])
            df_orig = st.session_state.user_original_df.drop(columns=["Delete"], errors='ignore')

            try:
                msg_list = []
                
                with st.spinner("Processing..."):
                    if not rows_to_delete.empty:
                        deleteData(rows_to_delete, current_cfg)
                        msg_list.append(f"Deleted {len(rows_to_delete)} rows.")

                    df_curr_chk = rows_to_keep.reset_index(drop=True)
                    df_orig_chk = df_orig.reset_index(drop=True)

                    new_rows = pd.DataFrame()
                    if len(df_curr_chk) > len(df_orig_chk):
                        new_rows = df_curr_chk.iloc[len(df_orig_chk):]
                    
                    modified_rows = pd.DataFrame()
                    overlap_len = min(len(df_curr_chk), len(df_orig_chk))
                    if overlap_len > 0:
                        curr_overlap = df_curr_chk.iloc[:overlap_len]
                        orig_overlap = df_orig_chk.iloc[:overlap_len]
                        changed_mask = ~(curr_overlap.fillna('').astype(str).eq(orig_overlap.fillna('').astype(str))).all(axis=1)
                        modified_rows = curr_overlap[changed_mask]
                    
                    final_save_df = pd.concat([new_rows, modified_rows])
                    
                    if not final_save_df.empty:
                         writeData(final_save_df, current_cfg)
                         msg_list.append(f"Updated/Added {len(final_save_df)} rows.")
                    
                    if msg_list:
                        st.success(" | ".join(msg_list))
                        st.session_state.user_original_df = rows_to_keep.copy()
                        
                        rows_to_keep["Delete"] = False
                        st.session_state.user_df_to_edit = rows_to_keep.copy()
                        
                        st.session_state.user_editor_key += 1
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.info("No changes to save.")

            except Exception as e:
                st.error(f"Save failed: {e}")

    else:
        st.warning("No data found.")