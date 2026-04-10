import streamlit as st
import pandas as pd
from datetime import datetime
import os

# --- 1. CONFIG & SYSTEM SETUP ---
USER_FILE = "users.csv"
LOG_FILE = "money_tracker.csv"
SUPER_USER = "Vincent21"
SUPER_PASS = "3123"

st.set_page_config(page_title="Command Center", layout="wide")

# Helper to load data
def load_data(file):
    if os.path.exists(file):
        return pd.read_csv(file, dtype=str)
    return pd.DataFrame()

user_df = load_data(USER_FILE)
log_df = load_data(LOG_FILE)

# --- 2. AUTHENTICATION BARRIER ---
if "auth" not in st.session_state:
    st.session_state.auth = False
    st.session_state.user = None

if not st.session_state.auth:
    # Login / Register UI (Same as before)
    t1, t2 = st.tabs(["🔒 Login", "📝 Register"])
    with t1:
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")
        if st.button("Login"):
            if u == SUPER_USER and p == SUPER_PASS:
                st.session_state.auth, st.session_state.user = True, u
                st.rerun()
            elif not user_df.empty:
                match = user_df[(user_df["Username"] == u) & (user_df["Password"] == p)]
                if not match.empty:
                    st.session_state.auth, st.session_state.user = True, u
                    st.rerun()
            st.error("Invalid credentials")
    # ... (Register logic here)
    st.stop()

# --- 3. SIDEBAR NAVIGATION (Define 'choice' here!) ---
current_user = st.session_state.user

with st.sidebar:
    st.title(f"👤 {current_user}")
    
    # Start with basic options
    menu = ["🏠 Home", "🛒 Order", "💵 Top Up", "📊 History"]
    
    # Inject Admin Space ONLY for Vincent
    if current_user == SUPER_USER:
        st.divider()
        st.warning("ADMIN MODE")
        menu.append("🛠️ SUPERADMIN SPACE")
    
    # THIS DEFINES THE VARIABLE 'choice'
    choice = st.radio("Navigation", menu)
    
    if st.button("Logout"):
        st.session_state.auth = False
        st.rerun()

# --- 4. CONDITIONAL SPACES (Use 'choice' here!) ---

if choice == "🛠️ SUPERADMIN SPACE":
    st.title("🛡️ Advanced Command Center")
    
    # User Management Tab
    tab_users, tab_logs, tab_settings = st.tabs(["Accounts", "Global Logs", "Control"])
    
    with tab_users:
        st.subheader("Decoded Credentials")
        st.dataframe(user_df, use_container_width=True) # Now readable!
        
        delete_user = st.selectbox("Delete Account", ["-- Select --"] + user_df["Username"].tolist())
        if st.button("Delete User") and delete_user != "-- Select --":
            new_df = user_df[user_df["Username"] != delete_user]
            new_df.to_csv(USER_FILE, index=False)
            st.rerun()

    with tab_logs:
        st.subheader("Every Transaction in System")
        st.dataframe(log_df.iloc[::-1], use_container_width=True)

elif choice == "🏠 Home":
    st.header(f"Welcome back, {current_user}")
    # User-specific balance and stats logic goes here

# ... add 'elif choice == "🛒 Order":' etc. below
