import streamlit as st
import os
import pandas as pd
from databricks import sql
from databricks.sdk.core import Config
import time

# --- DATABRICKS CHECK ---
assert os.getenv('DATABRICKS_WAREHOUSE_ID'), "DATABRICKS_WAREHOUSE_ID must be set in app.yaml."

# --- PAGE CONFIG ---
st.set_page_config(page_title="NFG Wastage Reduction", layout="wide")

import base64

def get_base64_of_bin_file(bin_file):
    with open(bin_file, 'rb') as f:
        data = f.read()
    return base64.b64encode(data).decode()

st.markdown("""
    <style>
        /* 1. HIDE SIDEBAR & LEFT CONTROLS COMPLETELY */
        /* Hides the sidebar itself */
        [data-testid="stSidebar"], section[data-testid="stSidebar"] {
            display: none !important;
        }
        /* Hides the 'arrow' button on the top left */
        [data-testid="collapsedControl"] {
            display: none !important;
        }

        /* 2. FORCE NO-SCROLL (Single Screen) */
        .main .block-container {
            padding-top: 1rem !important;
            padding-bottom: 0rem !important;
            padding-left: 3rem !important;
            padding-right: 3rem !important;
            height: 100vh;
            overflow: hidden; /* No scrolling allowed */
        }

        /* 3. TEXT & FONT CONTROL */
        h1 { font-size: 1.6rem !important; margin-bottom: 0.2rem !important; text-align: center; }
        h2 { font-size: 1.2rem !important; margin-top: 0px !important; }
        p, div, span { font-size: 0.85rem !important; }

        /* 4. TIGHTER SPACING */
        .stVerticalBlock { gap: 0.5rem !important; }
        .stElementContainer { margin-bottom: 0px !important; }
        
        /* 5. BACK BUTTON & INPUT ALIGNMENT */
        /* Shrinks buttons to fit in narrow rows */
        div.stButton > button {
            padding: 2px 5px !important;
            height: 2.2rem !important;
            min-height: 0px !important;
        }
        /* Tightens the selectbox height to match button */
        div[data-baseweb="select"] > div {
            height: 2.2rem !important;
            min-height: 0px !important;
        }
    </style>
    """, unsafe_allow_html=True)

# --- ROUTER STATE ---
if "page" not in st.session_state:
    st.session_state.page = "home"

# --- ROUTER ---
    
def go(page_name):
    """Callback to switch pages (Automatically reruns)"""
    st.session_state.page = page_name

# --- DYNAMIC TITLE LOGIC ---
page_labels = {
    "home": "",
    "model": " <span style='color: #666; font-size: 2rem;'>&rarr;</span> Model Recommendation",
    "master": " <span style='color: #666; font-size: 2rem;'>&rarr;</span> Master Data",
    "settings": " <span style='color: #666; font-size: 2rem;'>&rarr;</span> User Settings",
    "dashboard": " <span style='color: #666; font-size: 2rem;'>&rarr;</span> Dashboard"
}

# Determine base breadcrumb
breadcrumb = page_labels.get(st.session_state.page, "")

# --- Dynamic Sub-Label Logic ---
sub_label = ""

if st.session_state.page == "model":
    sub_label = st.session_state.get("selected_model", "Substitution")
elif st.session_state.page == "master":
    sub_label = st.session_state.get("selected_master", "ComponentExclusion")
elif st.session_state.page == "settings":
    sub_label = st.session_state.get("selected_settings", "Settings")

# Append to breadcrumb if a sub_label exists
if sub_label:
    breadcrumb += f" <span style='color: #999; font-size: 1.5rem;'>&rarr;</span> {sub_label}"

# # Render the Title
st.markdown(
    f"""
    <div style="text-align: center; margin-top: 4px; margin-bottom: 0px;">
        <h1 style="margin-top: 4px; color: #31333F; font-size: 2.2rem; font-weight: 800; line-height: 1.2;">
            NFG Wastage Reduction{breadcrumb}
        </h1>
    </div>
    """,
    unsafe_allow_html=True
)
st.markdown("<hr style='margin: 0px 0px 10px 0px; border-top: 1px solid #ddd;'>", unsafe_allow_html=True)

# def render_card(page_data, is_wide=False):
#     """
#     Ultra-compact card renderer for single-screen layouts.
#     """
#     with st.container(border=True):
#         # 1. Use a smaller header (h3 or h4 equivalent)

#         container_height = "150px" if not is_wide else "100px"
#         st.markdown(f"""
#             <div style="
#                 border: 1px solid #e6e9ef; 
#                 padding: 10px; 
#                 border-radius: 10px; 
#                 height: {container_height};
#                 margin-bottom: 10px;">
#                 <div style="
#                     color: #31333F; 
#                     font-size: 1.5rem; 
#                     font-weight: 400; 
#                     line-height: 1.2;
#                     margin-bottom: 10px;">
#                     {page_data['title']}
#                 </div>
#             </div>
#         """, unsafe_allow_html=True)
        
#         st.write("") # Tiny spacer

#         # 3. Action Button
#         label = "Open Dashboard" if is_wide else "Open"
        
#         st.button(
#             label,
#             key=f"btn_{page_data['page']}",
#             use_container_width=True,
#             on_click=go,
#             args=(page_data["page"],),
#             type="primary" if is_wide else "secondary"
#         )

def render_card(page_data, is_wide=False):
    """
    Ultra-compact card renderer for single-screen layouts.
    """
    with st.container(border=True):
        # --- ADJUST HEIGHTS HERE ---
        # Changed from 150px/100px to 100px/80px
        container_height = "100px" if not is_wide else "80px"
        
        st.markdown(f"""
            <div style="
                border: 1px solid #e6e9ef; 
                padding: 8px;              /* Reduced from 10px */
                border-radius: 10px; 
                height: {container_height};
                margin-bottom: 5px;        /* Reduced margin */
                display: flex;             /* Added centering */
                align-items: center;       /* Centers text vertically */
                justify-content: center;   /* Centers text horizontally */
                background-color: #f9f9f9;">
                <div style="
                    color: #31333F; 
                    font-size: 1.1rem;      /* Reduced from 1.5rem */
                    font-weight: 400; 
                    line-height: 1.1;
                    text-align: center;">
                    {page_data['title']}
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        # 3. Action Button
        label = "Open Dashboard" if is_wide else "Open"
        
        st.button(
            label,
            key=f"btn_{page_data['page']}",
            use_container_width=True,
            on_click=go,
            args=(page_data["page"],),
            type="primary" if is_wide else "secondary"
        )

def home():
    pages = [
        {"title": "📊 Model Output", "page": "model"},
        {"title": "📁 Master Data", "page": "master"},
        {"title": "⚙️ User Detail", "page": "settings"},
        {"title": "🔗 Dashboard", "page": "dashboard"},
    ]
    
    # 1. Create two master columns for the whole page
    # The first (3 units) is for buttons, the second (2 units) is for the image
    col_left, col_right = st.columns([3, 2], gap="large")

    with col_left:
        # --- Row 1 inside the Left Master Column ---
        # We need 3 columns here for the first 3 buttons
        row1_cols = st.columns(3, gap="medium")
        for i in range(3):
            with row1_cols[i]:
                render_card(pages[i], is_wide=False)

        st.write("") # Vertical Spacer between rows

        # --- Row 2 inside the Left Master Column ---
        # The Dashboard button spans the full width of this left column
        render_card(pages[3], is_wide=True)

    with col_right:
        # Inject CSS to style the image
        st.markdown("""
            <style>
            /* This targets the image within the column and adds the border and shadow */
            div[data-testid="stImage"] img {
                border: 2px solid #e6e9ef;
                border-radius: 15px;
                box-shadow: 2px 2px 15px rgba(0,0,0,0.05);
                transition: transform 0.3s ease;
                margin-top: -16px;
            }
            /* Optional: Add a subtle hover effect like your buttons */
            div[data-testid="stImage"] img:hover {
                transform: scale(1.01);
                border-color: #ff4b4b;
                
            }
            </style>
        """, unsafe_allow_html=True)
        
        st.image("images/logo.png", use_column_width=True)

# --- PAGES ---

def model_page():
    with st.spinner(' '):
        from pages.A_Model_Recommendation import run_model_ui
        run_model_ui()

def master_page():
    with st.spinner(' '):
        from pages.B_Master_Data import run_master_ui
        run_master_ui()


def settings_page():
    with st.spinner(' '):
        st.button("🏠", on_click=go, args=("home",))
        from pages.C_User_Settings import run_user_setting_ui

        run_user_setting_ui()


def dashboard_page():
    with st.spinner(' '):
        st.button("🏠", on_click=go, args=("home",))

# --- ROUTER ---
if st.session_state.page == "home":
    home()
elif st.session_state.page == "model":
    model_page()
elif st.session_state.page == "master":
    master_page()
elif st.session_state.page == "settings":
    settings_page()
elif st.session_state.page == "dashboard":
    dashboard_page()