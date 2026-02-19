import streamlit as st
import os
import pandas as pd
from databricks import sql
from databricks.sdk.core import Config
import time
from database_query import getData # Ensure this is imported correctly from your local file

# --- DATABRICKS CHECK ---
assert os.getenv('DATABRICKS_WAREHOUSE_ID'), "DATABRICKS_WAREHOUSE_ID must be set in app.yaml."

# --- PAGE CONFIG ---
st.set_page_config(page_title="NFG Wastage Reduction", layout="wide")

# ==========================================
# 🔐 AUTHENTICATION & ACCESS CONTROL LOGIC
# ==========================================
def get_current_user_email():
    # In Databricks apps, the email is passed in headers
    # Default to a test user for local development
    return st.context.headers.get("X-Forwarded-Email", "user@example.com")

def load_user_permissions():
    """
    Fetches UserSettings and determines what the current user can see.
    Returns a list of allowed PlantIds (e.g., ['P01', 'P02'] or ['ALL']).
    """
    try:
        user_email = get_current_user_email()
        
        # 1. Fetch the permissions table
        # We fetch the whole table to check permissions. 
        # In a very large system, you might query specific user rows, but for settings tables this is fine.
        df_perms = getData("bytemaster.appdata.UserSettings")
        
        if df_perms.empty:
            return []

        # 2. Filter for current user
        # Clean emails to ensure case-insensitive matching
        df_perms['UserEmail'] = df_perms['UserEmail'].astype(str).str.strip().str.lower()
        my_perms = df_perms[df_perms['UserEmail'] == user_email.lower()]
        
        if my_perms.empty:
            return [] # No access
        
        # 3. Get list of plants
        allowed_plants = my_perms['PlantId'].unique().tolist()
        
        # Handle 'ALL' case (normalize to uppercase)
        allowed_plants = [p.upper() for p in allowed_plants]
        
        return allowed_plants

    except Exception as e:
        st.error(f"Auth Error: {e}")
        return []

# --- INITIALIZE AUTH STATE ---
# We load permissions once per session start to avoid hitting DB on every rerun
if "user_permissions" not in st.session_state:
    st.session_state.user_permissions = load_user_permissions()
    st.session_state.user_email = get_current_user_email()

# ==========================================
# 🎨 UI STYLING & COMPONENTS
# ==========================================

import base64

def get_base64_of_bin_file(bin_file):
    with open(bin_file, 'rb') as f:
        data = f.read()
    return base64.b64encode(data).decode()

st.markdown("""
    <style>
        /* 1. HIDE SIDEBAR & LEFT CONTROLS COMPLETELY */
        [data-testid="stSidebar"], section[data-testid="stSidebar"] {
            display: none !important;
        }
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
            overflow: hidden; 
        }

        /* 3. TEXT & FONT CONTROL */
        h1 { font-size: 1.6rem !important; margin-bottom: 0.2rem !important; text-align: center; }
        h2 { font-size: 1.2rem !important; margin-top: 0px !important; }
        p, div, span { font-size: 0.85rem !important; }

        /* 4. TIGHTER SPACING */
        .stVerticalBlock { gap: 0.5rem !important; }
        .stElementContainer { margin-bottom: 0px !important; }
        
        /* 5. BACK BUTTON & INPUT ALIGNMENT */
        div.stButton > button {
            padding: 2px 5px !important;
            height: 2.2rem !important;
            min-height: 0px !important;
        }
        div[data-baseweb="select"] > div {
            height: 2.2rem !important;
            min-height: 0px !important;
        }
    </style>
    """, unsafe_allow_html=True)

# --- ROUTER STATE ---
if "page" not in st.session_state:
    st.session_state.page = "home"

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

breadcrumb = page_labels.get(st.session_state.page, "")
sub_label = ""

if st.session_state.page == "model":
    sub_label = st.session_state.get("selected_model", "Substitution")
elif st.session_state.page == "master":
    sub_label = st.session_state.get("selected_master", "ComponentExclusion")
elif st.session_state.page == "settings":
    sub_label = st.session_state.get("selected_settings", "Settings")

if sub_label:
    breadcrumb += f" <span style='color: #999; font-size: 1.5rem;'>&rarr;</span> {sub_label}"

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

def render_card(page_data, is_wide=False):
    """
    Ultra-compact card renderer for single-screen layouts.
    """
    with st.container(border=True):
        container_height = "40px"
        # "100px" if not is_wide else "80px"
        
        st.markdown(f"""
            <div style="
                border: 1px solid #e6e9ef; 
                padding: 8px;
                border-radius: 10px; 
                height: {container_height};
                margin-bottom: 5px;
                display: flex;
                align-items: center;
                justify-content: center;
                background-color: #f9f9f9;">
                <div style="
                    color: #31333F; 
                    font-size: 1.1rem;
                    font-weight: 400; 
                    line-height: 1.1;
                    text-align: center;">
                    {page_data['title']}
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        label = "Open Dashboard" if is_wide else "Open"
        
        st.button(
            label,
            key=f"btn_{page_data['page']}",
            use_container_width=True,
            on_click=go,
            args=(page_data["page"],),
            type="primary" if is_wide else "secondary"
        )

# ==========================================
# 🚦 PAGE ROUTING WITH SECURITY CHECKS
# ==========================================

def home():
    # Only show buttons if user has ANY access
    if not st.session_state.user_permissions:
        st.error(f"⛔ Access Denied: User '{st.session_state.user_email}' is not found in UserSettings.")
        return

    # Dynamic Page List based on Permissions
    pages = [
        {"title": "📊 Model Output", "page": "model"},
        {"title": "📁 Master Data", "page": "master"} if 'ALL' in st.session_state.user_permissions else None,
        {"title": "⚙️ User Detail", "page": "settings"} if 'ALL' in st.session_state.user_permissions else None,
        {"title": "🔗 Dashboard", "page": "dashboard"},
    ]
    # Filter out hidden pages
    pages = [p for p in pages if p is not None]
    
    col_left, col_right = st.columns([3, 2], gap="large")

    with col_left:
        # Dynamic Grid Layout based on number of visible pages
        # If settings is hidden, we might have 3 items total (2 in top row, 1 in bottom, or 3 in top)
        # We'll stick to your grid logic but adapt indices
        
        # Determine items for top row (first 3 max)
        top_row_items = pages[:3]
        
        row1_cols = st.columns(3, gap="medium")
        for i, item in enumerate(top_row_items):
            with row1_cols[i]:
                render_card(item, is_wide=False)

        st.write("") 

        # If we have a 4th item (Dashboard usually), show it wide
        if len(pages) > 3:
            render_card(pages[3], is_wide=True)

    with col_right:
        st.markdown("""
            <style>
            div[data-testid="stImage"] img {
                border: 2px solid #e6e9ef;
                border-radius: 15px;
                box-shadow: 2px 2px 15px rgba(0,0,0,0.05);
                transition: transform 0.3s ease;
                margin-top: -16px;
            }
            div[data-testid="stImage"] img:hover {
                transform: scale(1.01);
                border-color: #ff4b4b;
            }
            </style>
        """, unsafe_allow_html=True)
        
        # Ensure the image exists, or handle gracefully
        if os.path.exists("images/logo.png"):
            st.image("images/logo.png", use_column_width=True)
        else:
            st.warning("Logo image not found at images/logo.png")

# --- PAGES ---

def model_page():
    # Access Check
    if not st.session_state.user_permissions:
        st.error("Access Denied")
        return
        
    with st.spinner(' '):
        from pages.A_Model_Recommendation import run_model_ui
        run_model_ui()

def master_page():
    # STRICT Access Check: Only 'ALL' allowed
    if 'ALL' not in st.session_state.user_permissions:
        st.error("⛔ Unauthorized. Only Administrators (PlantId='ALL') can access User Settings.")
        st.button("Back", on_click=go, args=("home",))
        return

    with st.spinner(' '):
        from pages.B_Master_Data import run_master_ui
        run_master_ui()


def settings_page():
    # STRICT Access Check: Only 'ALL' allowed
    if 'ALL' not in st.session_state.user_permissions:
        st.error("⛔ Unauthorized. Only Administrators (PlantId='ALL') can access User Settings.")
        st.button("Back", on_click=go, args=("home",))
        return

    with st.spinner(' '):
        st.button("🏠", on_click=go, args=("home",))
        from pages.C_User_Settings import run_user_setting_ui
        run_user_setting_ui()


# def dashboard_page():
#     # General Access Check
#     if not st.session_state.user_permissions:
#         st.error("Access Denied")
#         return

#     with st.spinner(' '):
#         st.button("🏠", on_click=go, args=("home",))
#         st.write("Dashboard Placeholder")

def dashboard_page():
    # General Access Check
    if not st.session_state.user_permissions:
        st.error("Access Denied")
        return

    with st.spinner('Loading Dashboard...'):
        # st.button("🏠 Home", on_click=go, args=("home",))
        
        # Import and run the dashboard UI
        from pages.D_Dashboard import run_dashboard_ui
        run_dashboard_ui()

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