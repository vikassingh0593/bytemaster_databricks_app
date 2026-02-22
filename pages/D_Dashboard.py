import streamlit as st
import pandas as pd
import plotly.express as px
from database_query import getData
from config.configuration import DATASET_CONFIG

# --- 1. DYNAMIC CATEGORY ASSIGNMENT ---
# Instead of hardcoding paths, we group your existing DATASET_CONFIG keys
MODEL_TABLES = ["Substitution", "BatchReplacement", "ProdIncrease"]
# Note: Ensure your config uses "DimSubstitution" to avoid key collisions with the model "Substitution"
MASTER_TABLES = ["ComponentExclusion", "DimSubstitution"] 

# --- 2. DATA LOADER & HELPERS ---
@st.cache_data(ttl=300) 
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

# --- 3. DYNAMIC TOP BAR & FILTERS ---
def render_data(tables_list, nav_key, is_model=True):
    """
    Line 1: Radio Buttons (Aligns with Home button on the left)
    Line 2: Filters on a single horizontal row (Aligns with Model Output button)
    """
    
    # ---------------------------------------------------------
    # 🆕 CSS HACK: Shrink the gap below the radio buttons
    # ---------------------------------------------------------
    st.markdown("""
        <style>
            /* Targets the container holding the radio buttons */
            div[data-testid="stRadio"] {
                margin-top: -1.2rem !important;    /* Pulls it UP towards the divider */
                margin-bottom: -0.8rem !important; /* Pulls filters UP towards the radio buttons */
            }
        </style>
    """, unsafe_allow_html=True)

    # ==========================================
    # LINE 1 (RIGHT SIDE): RADIO BUTTONS
    # ==========================================
    selected_table = st.radio(
        "Select Table", 
        options=tables_list, 
        horizontal=True, 
        key=nav_key, 
        label_visibility="collapsed"
    )
    
    # Load Data based on the radio button selection
    table_path = DATASET_CONFIG[selected_table]["table"]
    df = load_dashboard_data(table_path, is_model=is_model)
    
    if df.empty:
        st.markdown("<hr style='margin: 0px 0px 10px 0px;'>", unsafe_allow_html=True)
        return selected_table, df
        
    # ==========================================
    # LINE 2 (RIGHT SIDE): FILTERS (All on same height)
    # ==========================================
    config_filters = DATASET_CONFIG.get(selected_table, {}).get("filter_columns", [])
    valid_filters = [col for col in config_filters if col in df.columns]
    
    if not valid_filters:
        st.markdown("<hr style='margin: 0px 0px 0px 0px;'>", unsafe_allow_html=True)
        return selected_table, df
        
    layout_columns = st.columns([1.5] * len(valid_filters) + [5.0], gap="small")
    
    filter_selections = {}
    
    for idx, col_name in enumerate(valid_filters):
        with layout_columns[idx]: 
            unique_vals = sorted(df[col_name].dropna().unique().tolist())

            # ---------------------------------------------------------
            # 🆕 DEFAULT LOGIC: Pre-select the latest RunID
            # ---------------------------------------------------------
            default_selection = None
            if col_name == "RunID" and unique_vals:
                # Get the absolute maximum value for RunID to use as default
                latest_run = df[col_name].dropna().max()
                default_selection = [latest_run]

            selected = st.multiselect(
                f"{col_name}",
                options=unique_vals,
                default=default_selection,
                key=f"f_{nav_key}_{selected_table}_{col_name}",
                label_visibility="collapsed",
                placeholder=f"{col_name}"
            )
            if selected:
                filter_selections[col_name] = selected

    # Apply Filters
    filtered_df = df.copy()
    for col_name, selected_vals in filter_selections.items():
        filtered_df = filtered_df[filtered_df[col_name].isin(selected_vals)]

    st.markdown("<hr style='margin: 0px 0px 0px 0px;'>", unsafe_allow_html=True)
    return selected_table, filtered_df

# --- 4. MAIN DASHBOARD UI ---
def run_dashboard_ui():
    
    if "nav_main" not in st.session_state:
        st.session_state.nav_main = "Model Output"
    
    nav_col, main_col = st.columns([1, 6], gap="small")

    # ==========================================
    # 👈 LEFT NAVIGATION MENU
    # ==========================================
    with nav_col:
        st.markdown("""
            <style>
                div[data-testid="column"]:nth-of-type(1) div[data-testid="stVerticalBlock"] {
                    gap: 0.1rem !important;
                }
            </style>
        """, unsafe_allow_html=True)
        
        if st.button("🏠", use_container_width=False, type="secondary"):
            st.session_state.page = "home"
            st.rerun()
            
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
            
            # 🆕 One line handles radio buttons, data load, and filters!
            selected_table, filtered_df = render_data(MODEL_TABLES, "sub_nav_model", is_model=True)
            
            if not filtered_df.empty:
                sort_col = "RunID" if "RunID" in filtered_df.columns else ("CreatedTimestamp" if "CreatedTimestamp" in filtered_df.columns else None)
                if sort_col:
                    filtered_df = filtered_df.sort_values(by=sort_col, ascending=False)
                    
                st.dataframe(filtered_df, use_container_width=True, hide_index=True, height=493)
            else:
                st.warning("No data found.")

        # ---------------------------------------------------------
        # VIEW 2: MASTER DATA (Tabular)
        # ---------------------------------------------------------
        elif st.session_state.nav_main == "Master Data":
            
            # 🆕 Same clean line for Master Data
            selected_table, filtered_df = render_data(MASTER_TABLES, "sub_nav_master", is_model=False)
            
            if not filtered_df.empty:
                st.dataframe(filtered_df, use_container_width=True, hide_index=True, height=493)
            else:
                st.warning("No data found.")

        # ---------------------------------------------------------
        # VIEW 3: GRAPHS (KPIs & Charts)
        # ---------------------------------------------------------
        elif st.session_state.nav_main == "Graphs":
            
            # 🆕 Same clean line for Graphs
            selected_table, filtered_df = render_data(MODEL_TABLES, "sub_nav_graph", is_model=True)
            
            if filtered_df.empty:
                st.warning("No data available to visualize.")
            else:
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