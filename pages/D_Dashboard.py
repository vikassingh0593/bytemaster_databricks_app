import streamlit as st
import pandas as pd
import plotly.express as px
from database_query import getData
from config.configuration import DATASET_CONFIG

# --- 1. DYNAMIC CATEGORY ASSIGNMENT ---
MODEL_TABLES = ["Substitution", "BatchReplacement", "ProdIncrease"]
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

# --- 3.5 KPI METRICS RENDERER ---
def render_kpi_cards(df):
    """Renders 7 specific KPIs in boxed cards, all on a single line."""
    if df.empty:
        return

    # NOTE: The CSS that was here has been moved to the unified block at the top!

    # 1. Calculate Metrics
    qty_at_risk = df["QtyAtRisk"].sum() if "QtyAtRisk" in df.columns else 0
    potential_saving = df["PotentialSaving"].sum() if "PotentialSaving" in df.columns else 0
    actual_saving = df["ActualSaving"].sum() if "ActualSaving" in df.columns else 0
    reduction_pct = (potential_saving / qty_at_risk * 100) if qty_at_risk > 0 else 0
    
    total_plants = df["PlantId"].nunique() if "PlantId" in df.columns else 0
    total_components = df["ComponentId"].nunique() if "ComponentId" in df.columns else 0
    no_recommendations = len(df)

    # 2. Render UI (7 Columns for 1 Line)
    cols = st.columns(7)
    
    # 3. Fill the boxed columns
    with cols[0]:
        with st.container(border=True):
            st.metric("Wastage Risk", f"{qty_at_risk:,.0f}")
            
    with cols[1]:
        with st.container(border=True):
            st.metric("Plants", f"{total_plants:,}")
            
    with cols[2]:
        with st.container(border=True):
            st.metric("Components", f"{total_components:,}")
            
    with cols[3]:
        with st.container(border=True):
            st.metric("Total Recs", f"{no_recommendations:,}")
            
    with cols[4]:
        with st.container(border=True):
            st.metric("Potential Save", f"${potential_saving:,.0f}")
            
    with cols[5]:
        with st.container(border=True):
            st.metric("Reduction", f"{reduction_pct:.1f}%")
            
    with cols[6]:
        with st.container(border=True):
            st.metric("Actual Save", f"${actual_saving:,.0f}")

# --- 3. DYNAMIC TOP BAR & FILTERS ---
def render_data(tables_list, nav_key, is_model=True):
    """
    Line 1: Radio Buttons (Aligns with Home button on the left)
    Line 2: Filters on a single horizontal row (Aligns with Model Output button)
    """
    
    # NOTE: The CSS that was here has been moved to the unified block at the top!

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
        return selected_table, df
        
    # ==========================================
    # LINE 2 (RIGHT SIDE): FILTERS (All on same height)
    # ==========================================
    config_filters = DATASET_CONFIG.get(selected_table, {}).get("filter_columns", [])
    valid_filters = [col for col in config_filters if col in df.columns]
    
    if not valid_filters:
        return selected_table, df
        
    layout_columns = st.columns([1.5] * len(valid_filters) + [5.0], gap="small")
    
    filter_selections = {}

    for idx, col_name in enumerate(valid_filters):
        with layout_columns[idx]: 
            unique_vals = sorted(df[col_name].dropna().unique().tolist())

            # DEFAULT LOGIC: Pre-select the latest RunID
            default_selection = None
            if col_name == "RunID" and unique_vals:
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

    return selected_table, filtered_df

# --- 4. MAIN DASHBOARD UI ---
def run_dashboard_ui():
    
    # ---------------------------------------------------------
    # 🆕 MASTER CSS BLOCK (All CSS goes here to prevent hidden gaps!)
    # ---------------------------------------------------------
    # st.markdown("""
    #     <style>
    #         /* 1. Gap between Radio Buttons and Filters */
    #         div[data-testid="stRadio"] {
    #             margin-top: 0em !important;    
    #             margin-bottom: -0.9rem !important; 
    #         }
            
    #         /* 2. Gap between Filters and KPI Boxes */
    #         div[data-testid="stMultiSelect"] {
    #             margin-bottom: -0.5rem !important; 
    #         }
            
    #         /* 3. Gap between KPI Boxes and Dataframe */
    #         div[data-testid="stDataFrame"] {
    #             margin-top: -0.5rem !important; 
    #         }
            
    #         /* 4. Left Sidebar Menu Gap AND Alignment */
    #         div[data-testid="column"]:nth-of-type(1) div[data-testid="stVerticalBlock"] {
    #             gap: 0.1rem !important;
    #             # margin-top: -1.2rem !important; /* 👈 Pulls the left column up to match the right column! */
    #         }
            
    #         /* 5. KPI Box Internal Styling */
    #         div[data-testid="stVerticalBlockBorderWrapper"]:has(div[data-testid="stMetricValue"]) {
    #             padding: 0.2rem 0.4rem !important;
    #         }
    #         div[data-testid="stVerticalBlockBorderWrapper"]:has(div[data-testid="stMetricValue"]) div[data-testid="stMetricLabel"] {
    #             margin-bottom: -0.6rem !important;
    #             font-weight: bold !important;
    #         }
    #         div[data-testid="stVerticalBlockBorderWrapper"]:has(div[data-testid="stMetricValue"]) div[data-testid="stMetricValue"] > div {
    #             font-size: 1.2rem !important; 
    #             line-height: 1.2 !important;
    #             font-weight: bold !important;
    #         }

    #         /* --- NEW: Reduce gap between KPI row and Chart rows --- */
    #         div[data-testid="stVerticalBlock"] > div:has(div[data-testid="stMetricValue"]) + div {
    #             margin-top: 0rem !important; 
    #         }
    #         /* --- 6. TARGETED CHART ROW SPACING --- */
    #         /* This specifically targets the row container immediately following the KPI row */
    #         div[data-testid="stVerticalBlock"] > div:has(div[data-testid="stMetricValue"]) + div[data-testid="stHorizontalBlock"] {
    #             margin-top: -0.5rem !important; /* Increase this negative value to pull the first chart row up */
    #         }
            
    #         /* This pulls the second row of charts up closer to the first row of charts */
    #         div[data-testid="stVerticalBlock"] > div:has(div[data-testid="stMetricValue"]) + div[data-testid="stHorizontalBlock"] + div + div[data-testid="stHorizontalBlock"] {
    #              margin-top: -2.5rem !important; 
    #         }
    #     </style>
    # """, unsafe_allow_html=True)

    # ---------------------------------------------------------
    # 🆕 MASTER CSS BLOCK (All CSS goes here to prevent hidden gaps!)
    # ---------------------------------------------------------
    st.markdown("""
        <style>
            /* ========================================================
               1. SYNC & PULL UP LEFT MENU AND RIGHT CONTENT
               ======================================================== */
            
            /* Pull the Home Button (Left Column) UP toward the line */
            div[data-testid="column"]:nth-of-type(1) div[data-testid="stVerticalBlock"] > div:first-child {
                margin-top: -15px !important; 
            }
            
            /* Pull the Radio Buttons OR Filters (Right Column) UP exactly the same amount */
            div[data-testid="column"]:nth-of-type(2) div[data-testid="stVerticalBlock"] > div:first-child {
                margin-top: -15px !important; 
            }

            /* Adjust the Radio Button specifically so the text aligns with the Home button icon */
            div[data-testid="stRadio"] {
                margin-bottom: -15px !important; 
            }


            /* ========================================================
               2. TIGHTEN REMAINING DASHBOARD SPACING
               ======================================================== */
            
            /* Gap between Filters and KPI Boxes */
            div[data-testid="stMultiSelect"] {
                margin-bottom: 2px !important; 
            }
            
            /* Gap between KPI Boxes and Dataframe */
            div[data-testid="stDataFrame"] {
                margin-top: -8px !important; 
            }
            
            /* Left Sidebar Menu button spacing */
            div[data-testid="column"]:nth-of-type(1) div[data-testid="stVerticalBlock"] {
                gap: 0.1rem !important;
            }
            
            /* 5. KPI Box Internal Styling */
            div[data-testid="stVerticalBlockBorderWrapper"]:has(div[data-testid="stMetricValue"]) {
                padding: 10px 5px !important; /* 👈 Even padding keeps the text inside the walls */
                height: 70% !important; /* 👈 Ensures all boxes stretch to match each other */
            }
            
            div[data-testid="stVerticalBlockBorderWrapper"]:has(div[data-testid="stMetricValue"]) div[data-testid="stMetricLabel"] {
                margin-top: 3px !important;    /* 👈 STOPS text from escaping out the top */
                margin-bottom: -1px !important; /* 👈 Adds a tiny normal gap between the name and the number */
                font-weight: bold !important;
                font-size: 0.85rem !important; 
                white-space: normal !important; /* Keeps wrapping on */
                # line-height: 1 !important;
                justify-content: center !important;
                text-align: center !important;
            }
            
            div[data-testid="stVerticalBlockBorderWrapper"]:has(div[data-testid="stMetricValue"]) div[data-testid="stMetricValue"] > div {
                font-size: 1.2rem !important; 
                # line-height: 1.2 !important;
                font-weight: bold !important;
                margin-top: 3px !important;
            }

            /* TARGETED CHART ROW SPACING */
            /* Pulls the first row of charts up closer to KPIs */
            div[data-testid="stVerticalBlock"] > div:has(div[data-testid="stMetricValue"]) + div[data-testid="stHorizontalBlock"] {
                margin-top: -0.5rem !important; 
            }
            
            /* Pulls the second row of charts up closer to the first row */
            div[data-testid="stVerticalBlock"] > div:has(div[data-testid="stMetricValue"]) + div[data-testid="stHorizontalBlock"] + div + div[data-testid="stHorizontalBlock"] {
                 margin-top: -2.5rem !important; 
            }

            /* Adjust the Radio Button specifically */
            div[data-testid="stRadio"] {
                # margin-top: -25px !important; /* Keep your current top margin */
                
                /* 👇 CHANGE THIS LINE to increase the gap below it */
                margin-bottom: 2px !important; /* Try 0px, 5px, or 10px to push filters down */
            }
        </style>
    """, unsafe_allow_html=True)
    
    if "nav_main" not in st.session_state:
        st.session_state.nav_main = "Current Waste Risk Summary"
    
    nav_col, main_col = st.columns([1, 6], gap="small")

    # ==========================================
    # 👈 LEFT NAVIGATION MENU
    # ==========================================
    with nav_col:

        if st.button("🏠", use_container_width=False, type="secondary"):
            st.session_state.page = "home"
            st.rerun()
            
        nav_options = ["Current Waste Risk Summary", "Model Recommendation", "Master Data"]
        
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
        if st.session_state.nav_main == "Model Recommendation":
            
            selected_table, filtered_df = render_data(MODEL_TABLES, "sub_nav_model", is_model=True)
            
            if not filtered_df.empty:

                render_kpi_cards(filtered_df)

                sort_col = "RunID" if "RunID" in filtered_df.columns else ("CreatedTimestamp" if "CreatedTimestamp" in filtered_df.columns else None)
                if sort_col:
                    filtered_df = filtered_df.sort_values(by=sort_col, ascending=False)
                    
                st.dataframe(filtered_df, use_container_width=True, hide_index=True, height=458)
            else:
                st.warning("No data found.")

        # ---------------------------------------------------------
        # VIEW 2: MASTER DATA (Tabular)
        # ---------------------------------------------------------
        elif st.session_state.nav_main == "Master Data":
            
            selected_table, filtered_df = render_data(MASTER_TABLES, "sub_nav_master", is_model=False)
            
            if not filtered_df.empty:
                st.markdown("<hr style='margin: 0px 0px 0px 0px;'>", unsafe_allow_html=True)
                st.dataframe(filtered_df, use_container_width=True, hide_index=True, height=493)
            else:
                st.warning("No data found.")

        # ---------------------------------------------------------
        # VIEW 3: GRAPHS (KPIs & Charts)
        # ---------------------------------------------------------
        elif st.session_state.nav_main == "Current Waste Risk Summary":
            # 1. LOAD AND COMBINE ALL MODEL DATA
            combined_data = []
            for table in MODEL_TABLES:
                table_path = DATASET_CONFIG[table]["table"]
                temp_df = load_dashboard_data(table_path, is_model=True)
                if not temp_df.empty:
                    temp_df["RecommendationType"] = table
                    if "MaterialType" not in temp_df.columns:
                        temp_df["MaterialType"] = 'Tmp'
                    combined_data.append(temp_df)
            
            if not combined_data:
                st.warning("No data available to visualize.")
            else:
                df_summary = pd.concat(combined_data, ignore_index=True)

                # 2. CUSTOM FILTERS
                summary_filter_cols = ["RunID", "PlantId", "Feedback", "MaterialType"] 
                valid_summary_filters = [c for c in summary_filter_cols if c in df_summary.columns]
                
                filter_selections = {}
                if valid_summary_filters:
                    layout_columns = st.columns([1.5] * len(valid_summary_filters) + [5.0], gap="small")
                    for idx, col_name in enumerate(valid_summary_filters):
                        with layout_columns[idx]:
                            unique_vals = sorted(df_summary[col_name].dropna().astype(str).unique().tolist())

                            default_selection = None
                            if col_name == "RunID" and unique_vals:
                                latest_run = df_summary[col_name].dropna().max()
                                default_selection = [latest_run]

                            selected = st.multiselect(
                                col_name, 
                                options=unique_vals,
                                default=default_selection,
                                key=f"sum_filt_{col_name}",
                                label_visibility="collapsed", 
                                placeholder=f"{col_name}"
                            )
                            if selected:
                                filter_selections[col_name] = selected
                
                filtered_df = df_summary.copy()
                for col_name, selected_vals in filter_selections.items():
                    filtered_df = filtered_df[filtered_df[col_name].isin(selected_vals)]

                # 3. RENDER KPIs
                render_kpi_cards(filtered_df)

                # 4. CHARTS SECTION
                # Standardized kwargs for single-screen fitting
                chart_layout_kwargs = dict(
                    margin=dict(l=10, r=10, t=35, b=10), 
                    height=235,
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, font=dict(size=10))
                )

                # row1_col1, row1_col2 = st.columns(2)
                row1_col1, row1_col2 = st.columns(2)

                with row1_col1:
                    with st.container(border=True):
                        # Chart 1: Doughnut Chart for SAVINGS by Recommendation Type
                        if "RecommendationType" in filtered_df.columns and not filtered_df.empty:
                            # Grouping by PotentialSaving for the doughnut segments
                            type_savings = filtered_df.groupby("RecommendationType")["ActualSaving"].sum().reset_index()
                            fig1 = px.pie(
                                type_savings, 
                                values="ActualSaving", 
                                names="RecommendationType", 
                                title="Savings by Rec Type",
                                hole=0.5, # Doughnut hole
                                color_discrete_sequence=px.colors.qualitative.T10
                            )
                            fig1.update_layout(**chart_layout_kwargs)
                            st.plotly_chart(fig1, use_container_width=True, config={'displayModeBar': False})
                        else:
                            st.warning("Missing 'RecommendationType' or Savings data")

                # with row1_col2:
                with row1_col2:
                    with st.container(border=True):
                        # Chart 2: Horizontal Bar segmented by Feedback
                        if all(col in filtered_df.columns for col in ["RecommendationType", "Feedback"]) and not filtered_df.empty:
                            
                            # 1. Group by BOTH columns (requires a list []) and get the size/count
                            recom_counts = filtered_df.groupby(["RecommendationType", "Feedback"]).size().reset_index(name="Count")
                            
                            # 2. Plot the chart
                            fig2 = px.bar(
                                recom_counts, 
                                x="Count", 
                                y="RecommendationType",  # The main bars are the Recommendation Type
                                color="Feedback",        # 👈 Segments and colors the bars by Feedback
                                orientation='h', 
                                title="Rec Type Distribution by Feedback",
                                barmode="stack",         # Stacks the feedback counts horizontally
                                color_discrete_sequence=px.colors.qualitative.Pastel
                            )
                            
                            # Sort Y-axis to show largest total bar on top
                            fig2.update_layout(yaxis={'categoryorder':'total ascending'}, **chart_layout_kwargs)
                            st.plotly_chart(fig2, use_container_width=True, config={'displayModeBar': False})
                        else:
                            st.warning("Missing 'RecommendationType' or 'Feedback' data")

                row2_col1, row2_col2 = st.columns(2)

                with row2_col1:
                    with st.container(border=True):
                        if all(c in filtered_df.columns for c in ["MaterialType", "QtyAtRisk", "ActualSaving"]):
                            mat_savings = filtered_df.groupby("MaterialType")[["QtyAtRisk", "ActualSaving"]].sum().reset_index()
                            fig3 = px.bar(
                                mat_savings, x="MaterialType", y=["QtyAtRisk", "ActualSaving"],
                                title="Risk & Savings by Material", barmode="group",
                                color_discrete_sequence=["#d62728", "#1f77b4"]
                            )
                            fig3.update_layout(**chart_layout_kwargs)
                            st.plotly_chart(fig3, use_container_width=True, config={'displayModeBar': False})
                        else:
                            st.warning("Missing Material Data")

                with row2_col2:
                    with st.container(border=True):
                        # Ensure all required columns exist
                        req_cols = ["ComponentId", "QtyAtRisk", "ActualSaving"]
                        if all(c in filtered_df.columns for c in req_cols) and not filtered_df.empty:
                            
                            # Group and sort by QtyAtRisk to find the top 10
                            # top_components = filtered_df.groupby("ComponentId")[["QtyAtRisk", "ActualSaving"]].sum().reset_index()
                            # top_components = top_components.sort_values(by="QtyAtRisk", ascending=False).tail(10)
                            # 1. Group by ComponentId and sum the metrics
                            top_components = filtered_df.groupby("ComponentId")[["QtyAtRisk", "ActualSaving"]].sum().reset_index()
                            
                            # 2. Sort to get the TOP 10 highest risks (ascending=False) and use .head(10)
                            top_components = top_components.sort_values(by="QtyAtRisk", ascending=False).head(10)
                            
                            # 3. CRITICAL FIX: Reverse the dataframe so Plotly draws the biggest bar at the TOP
                            top_components = top_components.iloc[::-1]
                            
                            # Horizontal bar chart with multiple X values
                            fig4 = px.bar(
                                top_components, 
                                x=["QtyAtRisk", "ActualSaving"], # 👈 Pass both columns as a list
                                y="ComponentId", 
                                title="Top 10 Components by Risk & Saving", 
                                orientation='h',
                                barmode='group', # 👈 Groups the bars side-by-side
                                color_discrete_sequence=["#d62728", "#2ca02c"] # Red for Risk, Green for Saving
                            )
                            
                            # Plotly defaults the x-axis name to "value" when using multiple columns, 
                            # so we rename it to "Amount" for better readability
                            fig4.update_layout(xaxis_title="Amount", legend_title_text="Metric", **chart_layout_kwargs)
                            
                            st.plotly_chart(fig4, use_container_width=True, config={'displayModeBar': False})
                        else:
                            st.warning("Missing Component, Risk, or Saving Data")