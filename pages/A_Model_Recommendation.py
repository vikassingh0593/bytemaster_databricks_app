import streamlit as st
import pandas as pd
from datetime import datetime
from database_query import getData, writeData 
import time 
from config.configuration import DATASET_CONFIG

# --- 1. CONFIGURATION IS IMPORTED ---
# MODEL_TABLES defines exactly what shows up on the screen for this page
MODEL_TABLES = ["SourcingIntelligence", "BatchConsolidation", "VolumeExpansion"]


# --- 2. DATA LOADER ---
def load_data(model_name):
    try:        
        user_email = st.context.headers.get("X-Forwarded-Email", "user@example.com").lower()

        table_name = DATASET_CONFIG[model_name]["table"]
        data = getData(tb_nm=table_name, SqlStr=' where RunID = (select max(RunID) from bytemaster.appdata.SourcingIntelligence)')

        us_df = getData(DATASET_CONFIG['UserSettings']["table"])
        user_email_lower = str(user_email).strip().lower()

        my_perms = us_df[
            us_df['ApprovedMailID'].astype(str).str.lower().apply(
                lambda x: user_email_lower in [email.strip() for email in x.split(',')]
            )
        ]

        if my_perms.empty:
            return [] # No access

        allowed_plants = my_perms['PlantId'].unique().tolist()
        allowed_plants = [str(p).strip().upper() for p in allowed_plants]

        if my_perms.empty:
            data = data.iloc[0:0]
        else:
            if 'ALL' in allowed_plants:
                pass 
            else:
                if "PlantId" in data.columns:
                    data = data[data["PlantId"].isin(allowed_plants)]
                else:
                    data = data.iloc[0:0]
        
        if "Feedback" not in data.columns:
            data["Feedback"] = "Unactioned"
        
        data["Feedback"] = data["Feedback"].fillna("Unactioned")
        data["Feedback"] = data["Feedback"].replace("", "Unactioned")

        ts_col = "CreatedTimestamp" 
        if ts_col in data.columns:
            data[ts_col] = pd.to_datetime(data[ts_col]).dt.strftime("%Y-%m-%d %H:%M:%S")
        
        st.session_state.df_to_edit = data.copy()
        st.session_state.original_df = data.copy()
    except Exception as e:
        st.error(f"Error loading data for {model_name}: {e}")

# --- 3. MAIN UI FUNCTION ---
def run_model_ui():
    # 🆕 SAFETY CHECK: Ensure selected model is one of the 3 allowed tables
    if "selected_model" not in st.session_state or st.session_state.selected_model not in MODEL_TABLES:
        st.session_state.selected_model = MODEL_TABLES[0]
    
    if "editor_key" not in st.session_state:
        st.session_state.editor_key = 0
    
    if "df_to_edit" not in st.session_state or st.session_state.df_to_edit is None:
        load_data(st.session_state.selected_model)

    # ==========================================
    # 🆕 UI NAVIGATION (Filtered to MODEL_TABLES)
    # ==========================================
    # Added a spacer [5.0] at the end so the 3 buttons don't stretch across the whole screen
    nav_cols = st.columns([0.5, 0.5] + [1.5] * len(MODEL_TABLES) + [5.0])

    with nav_cols[0]:
        if st.button("🏠", use_container_width=False):
            st.session_state.page = "home"
            st.rerun()

    # Loop ONLY through the 3 specific tables we want to show
    for i, model in enumerate(MODEL_TABLES):
        is_active = st.session_state.get("selected_model") == model
        
        # We only generate buttons for these specific models
        if nav_cols[i+2].button(model, use_container_width=True, type="primary" if is_active else "secondary"):
            st.session_state.selected_model = model
            load_data(model)
            st.session_state.editor_key += 1
            st.rerun()

    st.markdown("<hr style='margin: 0px 0px 10px 0px; border-top: 1px solid #ddd;'>", unsafe_allow_html=True)

    current_model = st.session_state.selected_model
    current_cfg = DATASET_CONFIG[current_model]
    
    # --- 4. DYNAMIC FILTER SECTION ---
    df_display = st.session_state.df_to_edit.copy()
    
    filter_cols = [col for col in current_cfg.get("filter_columns", []) if col != "RunID"]
    if filter_cols:
        col_filters, col_empty = st.columns([5, 6])
        
        with col_filters:
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
        
        with col_empty:
            st.empty()

    # --- 5. DATA EDITOR ---
    if st.session_state.df_to_edit is not None:
        column_configuration = {}
        for col in st.session_state.df_to_edit.columns:
            
            if col == "Feedback":
                column_configuration[col] = st.column_config.SelectboxColumn(
                    label="Feedback",
                    width="small",
                    options=["Accept", "Reject", "Under Review", "Unactioned"],
                    required=True,
                    help="Select the final status for this item"
                )
            
            elif col == "ActualSaving":
                column_configuration[col] = st.column_config.NumberColumn(
                    label="Actual Saving",
                    width="small",
                    disabled=False, 
                    help="Value can only be edited if Feedback is NOT 'Unactioned'"
                )
            
            elif col == "UserEmail":
                column_configuration[col] = st.column_config.TextColumn(
                    label="User Email",
                    width="medium", 
                    disabled=True
                )
            else:
                column_configuration[col] = st.column_config.Column(disabled=True)

        dynamic_widget_key = f"editor_{current_model}_{st.session_state.editor_key}"

        st.data_editor(
            df_display,
            key=dynamic_widget_key,  
            column_config=column_configuration,
            use_container_width=True,
            height=388,
            hide_index=True 
        )

        # --- 6. PROCESS EDITS ---
        state = st.session_state.get(dynamic_widget_key)
        
        if state and state.get("edited_rows"):
            user_email = st.context.headers.get("X-Forwarded-Email", "user@example.com")
            ts_col = "CreatedTimestamp" if "CreatedTimestamp" in df_display.columns else "Timestamp"
            
            valid_update_occurred = False
            validation_error = False
            
            for row_idx_in_filtered, changes in state["edited_rows"].items():
                actual_index = df_display.index[row_idx_in_filtered]
                
                current_feedback = changes.get("Feedback", st.session_state.df_to_edit.at[actual_index, "Feedback"])

                if "ActualSaving" in changes:
                    if current_feedback == "Unactioned":
                        validation_error = True 
                    else:
                        st.session_state.df_to_edit.at[actual_index, "ActualSaving"] = changes["ActualSaving"]
                        valid_update_occurred = True

                if "Feedback" in changes:
                    st.session_state.df_to_edit.at[actual_index, "Feedback"] = changes["Feedback"]
                    valid_update_occurred = True
                
                if valid_update_occurred:
                    st.session_state.df_to_edit.at[actual_index, ts_col] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    st.session_state.df_to_edit.at[actual_index, "UserEmail"] = user_email
            
            if validation_error:
                st.toast("⚠️ You must update 'Feedback' status (e.g., to 'Accept') before entering Actual Saving!", icon="🚫")
                time.sleep(2)
                st.session_state.editor_key += 1
                st.rerun()

            elif valid_update_occurred:
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
                        st.session_state.editor_key += 1
                        st.rerun() 
                except Exception as e:
                    st.error(f"Failed to save: {e}")
            else:
                st.info("No changes detected to save.")
    else:
        st.warning("No data found.")