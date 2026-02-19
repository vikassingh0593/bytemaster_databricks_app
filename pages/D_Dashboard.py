import streamlit as st
import pandas as pd
import plotly.express as px
from database_query import getData

# --- 1. CONFIGURATION ---
DATASET_CONFIG = {
    "Substitution": "bytemaster.appdata.Substitution",
    "BatchReplacement": "bytemaster.appdata.BatchReplacement",
    "ProdIncrease": "bytemaster.appdata.ProdIncrease"
}

# --- 2. DATA LOADER ---
@st.cache_data(ttl=300) # Cache for 5 mins for performance
def load_dashboard_data(model_name):
    """Loads and pre-processes data for the dashboard."""
    try:
        table_name = DATASET_CONFIG[model_name]
        df = getData(tb_nm=table_name)
        
        # Ensure Feedback column exists
        if "Feedback" not in df.columns:
            df["Feedback"] = "Unactioned"
        df["Feedback"] = df["Feedback"].fillna("Unactioned").replace("", "Unactioned")
        
        # Ensure numeric columns are actually numeric
        num_cols = ["QtyAtRisk", "PotentialSaving", "ActualSaving"]
        for col in num_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
                
        return df
    except Exception as e:
        st.error(f"Error loading {model_name}: {e}")
        return pd.DataFrame()

# --- 3. MAIN DASHBOARD UI ---
def run_dashboard_ui():
    
    # Initialize state for local dashboard navigation
    if "dash_page" not in st.session_state:
        st.session_state.dash_page = "Substitution"

    # --- LAYOUT: Left Nav (1 part) + Main Content (4 parts) ---
    nav_col, main_col = st.columns([1, 4], gap="large")

    # ==========================================
    # 👈 LEFT NAVIGATION MENU
    # ==========================================
    with nav_col:
        st.markdown("### 📊 Reports")
        st.markdown("<hr style='margin: 0px 0px 15px 0px;'>", unsafe_allow_html=True)
        
        # Create a button for each dashboard page
        for page_name in DATASET_CONFIG.keys():
            # Highlight the active button using 'primary' type
            btn_type = "primary" if st.session_state.dash_page == page_name else "secondary"
            if st.button(page_name, use_container_width=True, type=btn_type):
                st.session_state.dash_page = page_name
                st.rerun()

    # ==========================================
    # 📈 MAIN CONTENT AREA
    # ==========================================
    with main_col:
        current_report = st.session_state.dash_page
        st.subheader(f"{current_report} Overview")
        
        # Load data for the selected report
        df = load_dashboard_data(current_report)
        
        if df.empty:
            st.warning("No data available for this report.")
            return

        # --- TOP LEVEL: FILTERS ---
        st.markdown("##### Filters")
        f_col1, f_col2, f_col3 = st.columns(3)
        
        with f_col1:
            plants = sorted(df["PlantId"].dropna().unique())
            selected_plants = st.multiselect("Plant ID", options=plants, default=plants)
            
        with f_col2:
            materials = sorted(df["MaterialId"].dropna().unique()) if "MaterialId" in df.columns else []
            selected_materials = st.multiselect("Material ID", options=materials)
            
        with f_col3:
            statuses = sorted(df["Feedback"].dropna().unique())
            selected_status = st.multiselect("Feedback Status", options=statuses)

        # Apply Filters
        filtered_df = df.copy()
        if selected_plants:
            filtered_df = filtered_df[filtered_df["PlantId"].isin(selected_plants)]
        if selected_materials:
            filtered_df = filtered_df[filtered_df["MaterialId"].isin(selected_materials)]
        if selected_status:
            filtered_df = filtered_df[filtered_df["Feedback"].isin(selected_status)]

        st.markdown("<hr style='margin: 10px 0px 20px 0px;'>", unsafe_allow_html=True)

        # --- MIDDLE LEVEL: KPI CARDS ---
        kpi1, kpi2, kpi3, kpi4 = st.columns(4)
        
        # Calculate Metrics
        total_potential = filtered_df["PotentialSaving"].sum() if "PotentialSaving" in filtered_df else 0
        total_actual = filtered_df["ActualSaving"].sum() if "ActualSaving" in filtered_df else 0
        total_qty = filtered_df["QtyAtRisk"].sum() if "QtyAtRisk" in filtered_df else 0
        accepted_count = len(filtered_df[filtered_df["Feedback"] == "Accept"])

        with kpi1:
            st.metric("Total Potential Saving", f"${total_potential:,.0f}")
        with kpi2:
            st.metric("Total Actual Saving", f"${total_actual:,.0f}")
        with kpi3:
            st.metric("Total Qty at Risk", f"{total_qty:,.0f} units")
        with kpi4:
            st.metric("Accepted Proposals", f"{accepted_count}")

        st.markdown("<br>", unsafe_allow_html=True)

        # --- BOTTOM LEVEL: CHARTS ---
        chart_col1, chart_col2 = st.columns(2)
        
        with chart_col1:
            # Chart 1: Savings by Plant (Bar Chart)
            if "PlantId" in filtered_df and not filtered_df.empty:
                plant_savings = filtered_df.groupby("PlantId")[["PotentialSaving", "ActualSaving"]].sum().reset_index()
                fig_bar = px.bar(
                    plant_savings, x="PlantId", y=["PotentialSaving", "ActualSaving"], 
                    title="Savings Comparison by Plant",
                    barmode="group",
                    color_discrete_sequence=["#1f77b4", "#2ca02c"]
                )
                fig_bar.update_layout(margin=dict(l=20, r=20, t=40, b=20), height=350)
                st.plotly_chart(fig_bar, use_container_width=True)

        with chart_col2:
            # Chart 2: Feedback Distribution (Pie Chart)
            if "Feedback" in filtered_df and not filtered_df.empty:
                status_counts = filtered_df["Feedback"].value_counts().reset_index()
                status_counts.columns = ["Feedback", "Count"]
                fig_pie = px.pie(
                    status_counts, values="Count", names="Feedback",
                    title="Feedback Status Distribution",
                    hole=0.4 # Makes it a donut chart
                )
                fig_pie.update_layout(margin=dict(l=20, r=20, t=40, b=20), height=350)
                st.plotly_chart(fig_pie, use_container_width=True)