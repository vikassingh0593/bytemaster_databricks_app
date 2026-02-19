import streamlit as st
import pandas as pd
import plotly.express as px
from database_query import getData

# --- 1. CONFIGURATIONS ---
MODEL_CONFIG = {
    "Substitution": "bytemaster.appdata.Substitution",
    "BatchReplacement": "bytemaster.appdata.BatchReplacement",
    "ProdIncrease": "bytemaster.appdata.ProdIncrease"
}

MASTER_CONFIG = {
    "ComponentExclusion": "bytemaster.appdata.DimComponentExclusion",
    "Substitution": "bytemaster.appdata.DimSubstitution"
}

# --- 2. DATA LOADERS & HELPERS ---
# @st.cache_data(ttl=300) 
def load_dashboard_data(table_path, is_model=False):
    """Loads data and applies basic pre-processing."""
    try:
        df = getData(tb_nm=table_path)
        
        if is_model:
            if "Feedback" not in df.columns:
                df["Feedback"] = "Unactioned"
            df["Feedback"] = df["Feedback"].fillna("Unactioned").replace("", "Unactioned")
            
            num_cols = ["QtyAtRisk", "PotentialSaving", "ActualSaving"]
            for col in num_cols:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
                    
        return df
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return pd.DataFrame()

# @st.cache_data
def convert_df_to_csv(df):
    """Converts a pandas DataFrame to CSV format for downloading."""
    return df.to_csv(index=False).encode('utf-8')

# --- 3. DYNAMIC FILTERS ---
def render_filters(df, context="model"):
    """Renders filters dynamically and returns the filtered dataframe."""
    
    # We use the context string to ensure our keys are unique per tab
    if context == "model" or context == "graph":
        f_col1, f_col2, f_col3 = st.columns(3)
        with f_col1:
            plants = sorted(df["PlantId"].dropna().unique()) if "PlantId" in df.columns else []
            selected_plants = st.multiselect(
                "Plant ID", 
                options=plants,
                key=f"f_{context}_plant",
                label_visibility="collapsed",
                placeholder="Plant ID"
            )
        with f_col2:
            materials = sorted(df["MaterialId"].dropna().unique()) if "MaterialId" in df.columns else []
            selected_materials = st.multiselect(
                "Material ID", 
                options=materials,
                key=f"f_{context}_material",
                label_visibility="collapsed",
                placeholder="Material ID"
            )
        with f_col3:
            statuses = sorted(df["Feedback"].dropna().unique()) if "Feedback" in df.columns else []
            selected_status = st.multiselect(
                "Feedback Status", 
                options=statuses,
                key=f"f_{context}_status",
                label_visibility="collapsed",
                placeholder="Feedback Status"
            )
    else:
        f_col1, f_col2 = st.columns(2)
        with f_col1:
            plants = sorted(df["PlantId"].dropna().unique()) if "PlantId" in df.columns else []
            selected_plants = st.multiselect(
                "Plant ID", 
                options=plants,
                key=f"f_{context}_plant",
                label_visibility="collapsed",
                placeholder="Plant ID"
            )
        with f_col2:
            materials = sorted(df["MaterialId"].dropna().unique()) if "MaterialId" in df.columns else []
            selected_materials = st.multiselect(
                "Material ID", 
                options=materials,
                key=f"f_{context}_material",
                label_visibility="collapsed",
                placeholder="Material ID"
            )
        selected_status = [] 

    filtered_df = df.copy()
    
    # Apply Filters
    if selected_plants:
        filtered_df = filtered_df[filtered_df["PlantId"].isin(selected_plants)]
    if selected_materials:
        filtered_df = filtered_df[filtered_df["MaterialId"].isin(selected_materials)]
    if selected_status and "Feedback" in filtered_df.columns:
        filtered_df = filtered_df[filtered_df["Feedback"].isin(selected_status)]

    st.markdown("<hr style='margin: 10px 0px 20px 0px;'>", unsafe_allow_html=True)
    return filtered_df

# --- 4. MAIN DASHBOARD UI ---
def run_dashboard_ui():
    
    # --- FIX: RE-ENABLE SCROLLING FOR DASHBOARD ---
    # st.markdown("""
    #     <style>
    #         /* Override the global no-scroll rule just for this page */
    #         .main .block-container {
    #             overflow-y: auto !important;
    #             height: auto !important;
    #             padding-bottom: 5rem !important; /* Add some space at the bottom */
    #         }
    #     </style>
    # """, unsafe_allow_html=True)

    # Initialize Navigation States
    if "nav_main" not in st.session_state:
        st.session_state.nav_main = "Model Output"
    
    # Define Layout
    nav_col, main_col = st.columns([1, 6], gap="small")

    # ==========================================
    # 👈 LEFT NAVIGATION MENU
    # ==========================================
    # with nav_col:
    #     # st.markdown("### 🗂️ Menu")
    #     # st.markdown("<hr style='margin: 0px 0px 15px 0px;'>", unsafe_allow_html=True)
        
    #     nav_options = ["Model Output", "Master Data", "Graphs"]
        
    #     for option in nav_options:
    #         btn_type = "primary" if st.session_state.nav_main == option else "secondary"
    #         if st.button(option, use_container_width=False, type=btn_type):
    #             st.session_state.nav_main = option
    #             st.rerun()
    with nav_col:
            # --- NEW: Back to App Button ---
            if st.button("🏠", use_container_width=False, type="secondary"):
                st.session_state.page = "home"
                st.rerun()
                
            # st.markdown("<hr style='margin: 10px 0px 15px 0px;'>", unsafe_allow_html=True)
            
            nav_options = ["Model Output", "Master Data", "Graphs"]
            
            for option in nav_options:
                btn_type = "primary" if st.session_state.nav_main == option else "secondary"
                if st.button(option, use_container_width=True, type=btn_type):
                    st.session_state.nav_main = option
                    st.rerun()

    # ==========================================
    # 📈 MAIN CONTENT AREA
    # ==========================================
    with main_col:
        
        # ---------------------------------------------------------
        # VIEW 1: MODEL OUTPUT (Tabular)
        # ---------------------------------------------------------
        if st.session_state.nav_main == "Model Output":
            # st.subheader("Model Output Data")
            
            # selected_table = st.radio("", options=list(MODEL_CONFIG.keys()), horizontal=True, key="sub_nav_model")
            selected_table = st.radio("a", options=list(MODEL_CONFIG.keys()), horizontal=True, key="sub_nav_model", label_visibility="collapsed")
            
            df = load_dashboard_data(MODEL_CONFIG[selected_table], is_model=True)
            if not df.empty:
                filtered_df = render_filters(df, context="model")
                
                # # Setup Download & Record Count
                # info_col, dl_col = st.columns([3, 1])
                # with info_col:
                #     st.markdown(f"**Showing {len(filtered_df)} records**")
                # with dl_col:
                #     csv_data = convert_df_to_csv(filtered_df)
                #     st.download_button(
                #         label="📥 Download CSV",
                #         data=csv_data,
                #         file_name=f"{selected_table}_Data.csv",
                #         mime="text/csv",
                #         use_container_width=False
                #     )
                
                st.dataframe(filtered_df, use_container_width=True, hide_index=True, height=388)
            else:
                st.warning("No data found.")

        # ---------------------------------------------------------
        # VIEW 2: MASTER DATA (Tabular)
        # ---------------------------------------------------------
        elif st.session_state.nav_main == "Master Data":
            # st.subheader("Master Data Management")
            
            selected_table = st.radio("a", options=list(MASTER_CONFIG.keys()), horizontal=True, key="sub_nav_master", label_visibility="collapsed")
            
            df = load_dashboard_data(MASTER_CONFIG[selected_table], is_model=False)
            if not df.empty:
                filtered_df = render_filters(df, context="master")
                
                # # Setup Download & Record Count
                # info_col, dl_col = st.columns([3, 1])
                # with info_col:
                #     st.markdown(f"**Showing {len(filtered_df)} records**")
                # with dl_col:
                #     csv_data = convert_df_to_csv(filtered_df)
                #     st.download_button(
                #         label="📥 Download CSV",
                #         data=csv_data,
                #         file_name=f"{selected_table}_MasterData.csv",
                #         mime="text/csv",
                #         use_container_width=True
                #     )

                st.dataframe(filtered_df, use_container_width=True, hide_index=True, height=388)
            else:
                st.warning("No data found.")

        # ---------------------------------------------------------
        # VIEW 3: GRAPHS (KPIs & Charts)
        # ---------------------------------------------------------
        elif st.session_state.nav_main == "Graphs":
            st.subheader("Visual Analytics")
            
            selected_table = st.radio("a", options=list(MODEL_CONFIG.keys()), horizontal=True, key="sub_nav_graph", label_visibility="collapsed")
            
            df = load_dashboard_data(MODEL_CONFIG[selected_table], is_model=True)
            if df.empty:
                st.warning("No data available to visualize.")
            else:
                filtered_df = render_filters(df, context="graph")
                
                # KPI CARDS
                kpi1, kpi2, kpi3, kpi4 = st.columns(4)
                
                total_potential = filtered_df["PotentialSaving"].sum() if "PotentialSaving" in filtered_df else 0
                total_actual = filtered_df["ActualSaving"].sum() if "ActualSaving" in filtered_df else 0
                total_qty = filtered_df["QtyAtRisk"].sum() if "QtyAtRisk" in filtered_df else 0
                accepted_count = len(filtered_df[filtered_df["Feedback"] == "Accept"]) if "Feedback" in filtered_df else 0

                with kpi1:
                    st.metric("Potential Saving", f"${total_potential:,.0f}")
                with kpi2:
                    st.metric("Actual Saving", f"${total_actual:,.0f}")
                with kpi3:
                    st.metric("Qty at Risk", f"{total_qty:,.0f}")
                with kpi4:
                    st.metric("Accepted Proposals", f"{accepted_count}")

                st.markdown("<br>", unsafe_allow_html=True)

                # CHARTS
                chart_col1, chart_col2 = st.columns(2)
                
                with chart_col1:
                    if "PlantId" in filtered_df and not filtered_df.empty:
                        plant_savings = filtered_df.groupby("PlantId")[["PotentialSaving", "ActualSaving"]].sum().reset_index()
                        fig_bar = px.bar(
                            plant_savings, x="PlantId", y=["PotentialSaving", "ActualSaving"], 
                            title=f"Savings by Plant ({selected_table})",
                            barmode="group",
                            color_discrete_sequence=["#1f77b4", "#2ca02c"]
                        )
                        fig_bar.update_layout(margin=dict(l=20, r=20, t=40, b=20), height=350)
                        st.plotly_chart(fig_bar, use_container_width=True)

                with chart_col2:
                    if "Feedback" in filtered_df and not filtered_df.empty:
                        status_counts = filtered_df["Feedback"].value_counts().reset_index()
                        status_counts.columns = ["Feedback", "Count"]
                        fig_pie = px.pie(
                            status_counts, values="Count", names="Feedback",
                            title=f"Feedback Distribution ({selected_table})",
                            hole=0.4 
                        )
                        fig_pie.update_layout(margin=dict(l=20, r=20, t=40, b=20), height=350)
                        st.plotly_chart(fig_pie, use_container_width=True)