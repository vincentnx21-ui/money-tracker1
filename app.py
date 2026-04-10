import streamlit as st
import pandas as pd
from datetime import datetime
import os

# --- 1. CONFIG & SECURITY ---
USER_FILE = "users.csv"
LOG_FILE = "money_tracker.csv"
SUPER_USER = "Vincent21"
SUPER_PASS = "3123"

st.set_page_config(page_title="Multi-User System", layout="wide")

# --- 2. DATA LOADING ---
def load_data(file):
    if os.path.exists(file):
        return pd.read_csv(file, dtype=str)
    return pd.DataFrame()

user_df = load_data(USER_FILE)
log_df = load_data(LOG_FILE)

# --- 3. THE LOGIN BARRIER ---
if "auth" not in st.session_state:
    st.session_state.auth = False
    st.session_state.user = None

if not st.session_state.auth:
    tab_login, tab_reg = st.tabs(["🔒 Login", "📝 Register"])
    with tab_login:
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")
        if st.button("Enter System"):
            # Check for Vincent or regular users
            if u == SUPER_USER and p == SUPER_PASS:
                st.session_state.auth = True
                st.session_state.user = SUPER_USER
                st.rerun()
            elif not user_df.empty:
                match = user_df[(user_df["Username"] == u) & (user_df["Password"] == p)]
                if not match.empty:
                    st.session_state.auth = True
                    st.session_state.user = u
                    st.rerun()
            st.error("Access Denied.")
    # (Register logic stays same here)
    st.stop()

# --- 4. THE DIFFERENTIATED SPACES ---
current_user = st.session_state.user

# --- SPACE A: THE SIDEBAR (Navigation) ---
with st.sidebar:
    st.title(f"Logged in as: {current_user}")
    
    # NAVIGATION MENU
    menu_options = ["🏠 Home Dashboard", "🛒 Order Food", "💵 Top Up"]
    
    # ONLY INJECT ADMIN OPTION FOR VINCENT
    if current_user == SUPER_USER:
        st.divider()
        st.warning("ADMIN ACCESS")
        menu_options.append("🛠️ SUPERADMIN SPACE") # This won't exist for others
        
    choice = st.radio("Navigation", menu_options)
    
    if st.button("Logout"):
        st.session_state.auth = False
        st.rerun()

# --- SPACE B: THE ADMIN SPACE (Strictly Hidden) ---
if choice == "🛠️ SUPERADMIN SPACE":
    # Double-check identity again for security
    if current_user != SUPER_USER:
        st.error("Unauthorized!")
    else:
        st.header("🔑 Master Control Center")
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("User Database (Decoded)")
            st.dataframe(user_df, use_container_width=True)
        with col2:
            st.subheader("Global System Logs")
            st.dataframe(log_df, use_container_width=True)

# --- SPACE C: THE USER SYSTEM ---
elif choice == "🏠 Home Dashboard":
    st.header(f"Welcome to your System, {current_user}")
    # Show user balance and specific history here...

elif choice == "🛒 Order Food":
    st.header("Place an Order")
    # Show menu logic here...
