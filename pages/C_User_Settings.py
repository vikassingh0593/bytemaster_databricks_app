# import streamlit as st
# import pandas as pd
# from datetime import datetime
# import time
# from database_query import getData, writeData, deleteData

# # --- 1. CONFIGURATION ---
# USER_DATA_CONFIG = {
#     "UserSettings": {
#         "table": "bytemaster.appdata.UserSettings",
#         "join_keys": ["PlantId"], 
#         "update_columns": ["UserEmail", "UpdatedTimestamp"], # Note: We don't update PlantId (PK)
#         "filter_columns": ["PlantId", "UserEmail"]
#     }
# }

# # --- 2. DATA LOADER ---
# def load_user_data():
#     try:
#         table_name = USER_DATA_CONFIG["UserSettings"]["table"]
#         data = getData(tb_nm=table_name)
        
#         # Format Timestamp
#         ts_col = "UpdatedTimestamp" if "UpdatedTimestamp" in data.columns else "Timestamp"
#         if ts_col in data.columns:
#             data[ts_col] = pd.to_datetime(data[ts_col]).dt.strftime("%Y-%m-%d %H:%M:%S")
        
#         # --- NEW: Add 'Delete' column for the UI ---
#         # We insert it at the very beginning (index 0) so it appears on the left
#         if "Delete" not in data.columns:
#             data.insert(0, "Delete", False)
        
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

#     current_cfg = USER_DATA_CONFIG["UserSettings"]
    
#     # --- 4. LAYOUT ---
#     if st.session_state.user_df_to_edit is not None:
#         df_display = st.session_state.user_df_to_edit.copy()

#         col_filters, col_spacer, col_add = st.columns([2.5, 6.5, 1], gap="small")
        
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
#                             placeholder=f"Filter {col_name}"
#                         )
#                         if selected:
#                             df_display = df_display[df_display[col_name].isin(selected)]
        
#         with col_spacer:
#             st.empty() 

#         # Add Record
#         with col_add:
#             with st.popover("➕ Add", use_container_width=True):
#                 st.write("**Add User Setting**")
#                 with st.form("add_user_form", clear_on_submit=True):
#                     new_plant = st.text_input("PlantId", placeholder="e.g., P01")
#                     new_email = st.text_input("UserEmail", placeholder="e.g., user@example.com")
                    
#                     submitted = st.form_submit_button("Add Row", type="primary")
                    
#                     if submitted:
#                         if new_plant and new_email:
#                             existing_plants = st.session_state.user_df_to_edit["PlantId"].astype(str).tolist()
                            
#                             if new_plant in existing_plants:
#                                 st.error(f"PlantId '{new_plant}' already exists!")
#                             else:
#                                 ts_col = "UpdatedTimestamp" if "UpdatedTimestamp" in st.session_state.user_df_to_edit.columns else "Timestamp"
                                
#                                 new_row_data = {
#                                     "Delete": False,  # New row is not marked for deletion
#                                     "PlantId": new_plant,
#                                     "UserEmail": new_email,
#                                     ts_col: datetime.now().strftime("%Y-%m-%d %H:%M:%S")
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
#             # 1. DELETE COLUMN (Checkbox)
#             "Delete": st.column_config.CheckboxColumn(
#                 "❌",   # Header symbol
#                 help="Check this box to delete the row",
#                 default=False,
#                 width="small"
#             ),
#             # 2. DATA COLUMNS
#             "PlantId": st.column_config.TextColumn("PlantId", width="small", disabled=True), # PK should strictly be disabled
#             "UserEmail": st.column_config.TextColumn("UserEmail", width="large", required=True),
#             "UpdatedTimestamp": st.column_config.TextColumn("Timestamp", disabled=True, width="medium")
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
#             ts_col = "UpdatedTimestamp" if "UpdatedTimestamp" in df_display.columns else "Timestamp"
            
#             has_changes = False
#             for row_idx_in_filtered, changes in state["edited_rows"].items():
#                 actual_index = df_display.index[row_idx_in_filtered]
                
#                 # Apply changes to session state
#                 for key, value in changes.items():
#                     st.session_state.user_df_to_edit.at[actual_index, key] = value
                
#                 # Only update timestamp if the change wasn't just checking the "Delete" box
#                 if "Delete" not in changes or len(changes) > 1:
#                     st.session_state.user_df_to_edit.at[actual_index, ts_col] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
#                 has_changes = True
            
#             if has_changes:
#                 st.rerun()

#         # --- 7. SAVE ACTION ---
#         st.markdown("<hr style='margin: 0px 0px 10px 0px; border-top: 1px solid #ddd;'>", unsafe_allow_html=True)
#         if st.button("Save Changes to Database", type="primary", use_container_width=False):
            
#             # --- SEPARATE DELETES FROM UPDATES ---
#             full_df = st.session_state.user_df_to_edit
            
#             # 1. Rows marked for deletion
#             rows_to_delete = full_df[full_df["Delete"] == True]
            
#             # 2. Rows to keep (and potentially save updates for)
#             rows_to_keep = full_df[full_df["Delete"] == False].drop(columns=["Delete"]) # Remove helper col
            
#             # 3. Original Rows (for comparison)
#             df_orig = st.session_state.user_original_df.drop(columns=["Delete"], errors='ignore')

#             # --- PERFORM ACTIONS ---
#             try:
#                 msg_list = []
                
#                 # A) Handle Deletions (If any)
#                 # Note: writeData usually Upserts. If you need true delete, you might need to handle it 
#                 # by saving the 'rows_to_keep' in 'overwrite' mode, OR calling a delete query.
#                 # Assuming 'overwrite' logic or manual delete handling here:
#                 if not rows_to_delete.empty:
#                     # Logic depends on your DB capability. 
#                     # If you use overwrite mode for 'rows_to_keep', that effectively deletes the missing ones.
#                     msg_list.append(f"Deleted {len(rows_to_delete)} rows.")

#                 # B) Handle Updates/Inserts on remaining rows
#                 # Logic: Find what changed in 'rows_to_keep' vs 'df_orig'
                
#                 # Reset indices to align
#                 df_curr_chk = rows_to_keep.reset_index(drop=True)
#                 df_orig_chk = df_orig.reset_index(drop=True)

#                 # Identify modified/new rows
#                 # Simple logic: If we are using overwrite, we just save 'rows_to_keep'
#                 # If we are using upsert, we need to filter.
#                 # Here we assume we send the changed rows to the DB.
                
#                 # Find new rows (appended)
#                 new_rows = pd.DataFrame()
#                 if len(df_curr_chk) > len(df_orig_chk):
#                     new_rows = df_curr_chk.iloc[len(df_orig_chk):]
                
#                 # Find modified rows
#                 modified_rows = pd.DataFrame()
#                 overlap_len = min(len(df_curr_chk), len(df_orig_chk))
#                 if overlap_len > 0:
#                     curr_overlap = df_curr_chk.iloc[:overlap_len]
#                     orig_overlap = df_orig_chk.iloc[:overlap_len]
                    
#                     changed_mask = ~(curr_overlap.fillna('').astype(str).eq(orig_overlap.fillna('').astype(str))).all(axis=1)
#                     modified_rows = curr_overlap[changed_mask]
                
#                 final_save_df = pd.concat([new_rows, modified_rows])
                
#                 # --- EXECUTE SAVE ---
#                 # NOTE: If you need to DELETE from DB, and writeData is just an upsert/merge,
#                 # you might need to change your strategy to 'overwrite' the whole table 
#                 # with 'rows_to_keep' if the dataset is small.
                
#                 # STRATEGY: If dataset is small (<10k rows), easiest is often Overwrite with rows_to_keep
#                 # If writeData supports overwrite:
#                 with st.spinner("Saving..."):
#                     if not final_save_df.empty:
#                          writeData(final_save_df, current_cfg)
#                          msg_list.append(f"Updated/Added {len(final_save_df)} rows.")
                    
#                     # If you have specific delete logic in writeData, pass rows_to_delete there
#                     # Otherwise, if you rely on overwrite, passing 'rows_to_keep' as the full table works.
                    
#                     if msg_list:
#                         st.success(" | ".join(msg_list))
#                         st.session_state.user_original_df = rows_to_keep.copy()
#                         # Reset the 'Delete' flags in the editor
#                         st.session_state.user_df_to_edit = rows_to_keep.copy()
#                         st.session_state.user_df_to_edit.insert(0, "Delete", False)
#                         st.session_state.user_editor_key += 1
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
from database_query import getData, writeData, deleteData

# --- 1. CONFIGURATION ---
USER_DATA_CONFIG = {
    "UserSettings": {
        "table": "bytemaster.appdata.UserSettings",
        "join_keys": ["PlantId"], 
        "update_columns": ["UserEmail", "UpdatedTimestamp"],
        "filter_columns": ["PlantId", "UserEmail"]
    }
}

# --- 2. DATA LOADER ---
def load_user_data():
    try:
        table_name = USER_DATA_CONFIG["UserSettings"]["table"]
        data = getData(tb_nm=table_name)
        
        # Format Timestamp
        ts_col = "UpdatedTimestamp" if "UpdatedTimestamp" in data.columns else "Timestamp"
        if ts_col in data.columns:
            data[ts_col] = pd.to_datetime(data[ts_col]).dt.strftime("%Y-%m-%d %H:%M:%S")
        
        # --- NEW: Add 'Delete' column at index 0 (Far Left) ---
        if "Delete" not in data.columns:
            data.insert(0, "Delete", False)
        
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

    current_cfg = USER_DATA_CONFIG["UserSettings"]
    
    # --- 4. LAYOUT ---
    if st.session_state.user_df_to_edit is not None:
        df_display = st.session_state.user_df_to_edit.copy()

        col_filters, col_spacer, col_add = st.columns([2.5, 6.5, 1], gap="small")
        
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
                            placeholder=f"Filter {col_name}"
                        )
                        if selected:
                            df_display = df_display[df_display[col_name].isin(selected)]
        
        with col_spacer:
            st.empty() 

        # Add Record
        with col_add:
            with st.popover("➕ Add", use_container_width=True):
                st.write("**Add User Setting**")
                with st.form("add_user_form", clear_on_submit=True):
                    new_plant = st.text_input("PlantId", placeholder="e.g., P01")
                    new_email = st.text_input("UserEmail", placeholder="e.g., user@example.com")
                    
                    submitted = st.form_submit_button("Add Row", type="primary")
                    
                    if submitted:
                        if new_plant and new_email:
                            existing_plants = st.session_state.user_df_to_edit["PlantId"].astype(str).tolist()
                            
                            if new_plant in existing_plants:
                                st.error(f"PlantId '{new_plant}' already exists!")
                            else:
                                ts_col = "UpdatedTimestamp" if "UpdatedTimestamp" in st.session_state.user_df_to_edit.columns else "Timestamp"
                                
                                new_row_data = {
                                    "Delete": False,
                                    "PlantId": new_plant,
                                    "UserEmail": new_email,
                                    ts_col: datetime.now().strftime("%Y-%m-%d %H:%M:%S")
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
            # 1. DELETE COLUMN (Small width, Trash Icon)
            "Delete": st.column_config.CheckboxColumn(
                "🗑️",
                help="Check to delete",
                default=False,
                width="small" # Smallest available width setting
            ),
            # 2. DATA COLUMNS
            "PlantId": st.column_config.TextColumn("PlantId", width="small", disabled=True), 
            "UserEmail": st.column_config.TextColumn("UserEmail", width="large", required=True),
            "UpdatedTimestamp": st.column_config.TextColumn("Timestamp", disabled=True, width="medium")
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
            ts_col = "UpdatedTimestamp" if "UpdatedTimestamp" in df_display.columns else "Timestamp"
            
            has_changes = False
            for row_idx_in_filtered, changes in state["edited_rows"].items():
                actual_index = df_display.index[row_idx_in_filtered]
                
                # Apply changes
                for key, value in changes.items():
                    st.session_state.user_df_to_edit.at[actual_index, key] = value
                
                # Update timestamp ONLY if the change wasn't just the Delete checkbox
                # (We don't need a new timestamp if we are about to delete it)
                if "Delete" not in changes or len(changes) > 1:
                    st.session_state.user_df_to_edit.at[actual_index, ts_col] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                has_changes = True
            
            if has_changes:
                st.rerun()

        # --- 7. SAVE ACTION ---
        st.markdown("<hr style='margin: 0px 0px 10px 0px; border-top: 1px solid #ddd;'>", unsafe_allow_html=True)
        if st.button("Save Changes to Database", type="primary", use_container_width=False):
            
            # --- SEPARATE DELETES FROM UPDATES ---
            full_df = st.session_state.user_df_to_edit
            
            # 1. Identify rows to Delete
            rows_to_delete = full_df[full_df["Delete"] == True]
            
            # 2. Identify rows to Keep
            rows_to_keep = full_df[full_df["Delete"] == False].drop(columns=["Delete"])
            
            # 3. Original Rows (for identifying modifications)
            df_orig = st.session_state.user_original_df.drop(columns=["Delete"], errors='ignore')

            try:
                msg_list = []
                
                with st.spinner("Processing..."):
                    # A) EXECUTE DELETE
                    if not rows_to_delete.empty:
                        # Call the deleteData function using PKs from rows_to_delete
                        deleteData(rows_to_delete, current_cfg)
                        msg_list.append(f"Deleted {len(rows_to_delete)} rows.")

                    # B) EXECUTE UPSERT (Updates + Inserts)
                    # Find what changed in the rows we are keeping
                    df_curr_chk = rows_to_keep.reset_index(drop=True)
                    df_orig_chk = df_orig.reset_index(drop=True)

                    # 1. Find New Rows (Appended)
                    new_rows = pd.DataFrame()
                    if len(df_curr_chk) > len(df_orig_chk):
                        new_rows = df_curr_chk.iloc[len(df_orig_chk):]
                    
                    # 2. Find Modified Rows (Existing)
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
                    
                    # C) REFRESH STATE
                    if msg_list:
                        st.success(" | ".join(msg_list))
                        
                        # Update Original to reflect the new reality (Deleted rows gone, Updates applied)
                        st.session_state.user_original_df = rows_to_keep.copy()
                        
                        # Update Edit DF (Reset Delete flags)
                        st.session_state.user_df_to_edit = rows_to_keep.copy()
                        st.session_state.user_df_to_edit.insert(0, "Delete", False)
                        
                        st.session_state.user_editor_key += 1
                        time.sleep(1) # Give user a moment to read success message
                        st.rerun()
                    else:
                        st.info("No changes to save.")

            except Exception as e:
                st.error(f"Save failed: {e}")

    else:
        st.warning("No data found.")