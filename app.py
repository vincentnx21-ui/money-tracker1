import streamlit as st
import pandas as pd
from datetime import datetime
import os
import hashlib

# --- CONFIG ---
log_file = "money_tracker.csv"
user_file = "users.csv"
ADMIN_PASSWORD = "123"

st.set_page_config(page_title="Multi-User Tracker", layout="centered")

# --- UTILS ---
def hash_password(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

def check_password(password, hashed_password):
    return hash_password(password) == hashed_password

def load_data(file, columns):
    if os.path.exists(file):
        try:
            df = pd.read_csv(file)
            for col in columns:
                if col not in df.columns: df[col] = "N/A"
            return df
        except:
            return pd.DataFrame(columns=columns)
    return pd.DataFrame(columns=columns)

# Data Loading
user_df = load_data(user_file, ["Username", "Password"])
log_cols = ["Date", "User", "Location", "Shop", "Item", "Quantity", "Total Cost", "Wallet Left", "Type"]
log_df = load_data(log_file, log_cols)

# --- LOGIN LOGIC ---
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = None

if not st.session_state.logged_in:
    t1, t2 = st.tabs(["Login", "Register"])
    with t1:
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")
        if st.button("Log In"):
            row = user_df[user_df["Username"] == u]
            if not row.empty and check_password(p, row.iloc[0]["Password"]):
                st.session_state.logged_in = True
                st.session_state.username = u
                st.rerun()
            else:
                st.error("Wrong username/password")
    with t2:
        nu = st.text_input("New Username")
        np = st.text_input("New Password", type="password")
        npc = st.text_input("Confirm New Password", type="password")
        if st.button("Create Account"):
            if nu and np == npc:
                new_u = pd.DataFrame([{"Username": nu, "Password": hash_password(np)}])
                new_u.to_csv(user_file, mode='a', index=False, header=not os.path.exists(user_file))
                st.success("Account created! Go to Login.")
            else:
                st.error("Check details")
    st.stop()

# --- SIDEBAR (LOGOUT & ADMIN) ---
with st.sidebar:
    st.title(f"👋 Hi, {st.session_state.username}")
    if st.button("🚪 Logout", use_container_width=True):
        st.session_state.logged_in = False
        st.session_state.username = None
        st.rerun()
    
    st.divider()
    
    # ADMINISTRATION MOVED HERE
    with st.expander("🛠️ Administration"):
        adm_pwd = st.text_input("Admin Password", type="password")
        if adm_pwd == ADMIN_PASSWORD:
            st.subheader("Add Master Menu")
            a_loc = st.text_input("Location")
            a_stall = st.text_input("Stall")
            a_item = st.text_input("Product")
            a_price = st.number_input("Price", min_value=0.0, step=0.05)
            
            if st.button("Save to Global Menu"):
                if a_loc and a_stall and a_item:
                    setup_row = pd.DataFrame([{
                        "Date": "N/A", "User": "ADMIN", "Location": a_loc, 
                        "Shop": a_stall, "Item": a_item, "Quantity": 1, 
                        "Total Cost": a_price, "Wallet Left": 0, "Type": "MenuSetup"
                    }])
                    setup_row.to_csv(log_file, mode='a', index=False); st.success("Added!"); st.rerun()
            
            st.divider()
            if st.button("🧨 Wipe All Transactions", type="primary"):
                # Keeps the users and menu, but clears all user spending
                clean_df = log_df[log_df["Type"] == "MenuSetup"]
                clean_df.to_csv(log_file, index=False); st.rerun()

# --- MAIN APP ---
user = st.session_state.username
user_log = log_df[log_df["User"] == user]
balance = float(user_log["Wallet Left"].iloc[-1]) if not user_log.empty else 0.0

st.title("💰 Smart Money Tracker")
st.metric("Wallet Balance", f"${balance:,.2f}")

tab1, tab2, tab3 = st.tabs(["🛒 Order Food", "💵 Top Up", "📊 History"])

# --- ORDER TAB ---
with tab1:
    # 1. Location
    all_locs = sorted([l for l in log_df["Location"].unique().tolist() if l != "N/A"])
    loc_choice = st.selectbox("Location", ["-- Select --"] + all_locs)
    
    if loc_choice != "-- Select --":
        # 2. Stall
        stalls = sorted(log_df[log_df["Location"] == loc_choice]["Shop"].unique().tolist())
        stall_choice = st.selectbox("Stall", ["-- Select --"] + stalls)
        
        if stall_choice != "-- Select --":
            # 3. Product (Looking for MenuSetup price)
            items_df = log_df[(log_df["Location"] == loc_choice) & (log_df["Shop"] == stall_choice)]
            clean_items = sorted(items_df["Item"].unique().tolist())
            prod_choice = st.selectbox("Product", ["-- Select --"] + clean_items)
            
            if prod_choice != "-- Select --":
                price_match = items_df[(items_df["Item"] == prod_choice) & (items_df["Type"] == "MenuSetup")]
                u_price = float(price_match.iloc[-1]["Total Cost"]) if not price_match.empty else 0.0
                
                st.info(f"Fixed Price: ${u_price:.2f}")
                qty = st.number_input("How many?", min_value=1, step=1)
                
                if st.button("Confirm Purchase", use_container_width=True, type="primary"):
                    cost = u_price * qty
                    new_row = pd.DataFrame([{
                        "Date": datetime.now().strftime("%Y-%m-%d"),
                        "User": user, "Location": loc_choice, "Shop": stall_choice,
                        "Item": prod_choice, "Quantity": qty, "Total Cost": cost,
                        "Wallet Left": balance - cost, "Type": "Spend"
                    }])
                    new_row.to_csv(log_file, mode='a', index=False); st.rerun()

# --- TOP UP TAB ---
with tab2:
    amt = st.number_input("Amount to add", min_value=0.0)
    if st.button("Add to Wallet"):
        nr = pd.DataFrame([{"Date": datetime.now().strftime("%Y-%m-%d"), "User": user, "Location": "N/A", "Shop": "N/A", "Item": "Top-up", "Quantity": 1, "Total Cost": 0, "Wallet Left": balance + amt, "Type": "TopUp"}])
        nr.to_csv(log_file, mode='a', index=False); st.rerun()

# --- HISTORY TAB ---
with tab3:
    if not user_log.empty:
        history_view = user_log[user_log["Type"].isin(["Spend", "TopUp"])]
        st.dataframe(history_view.iloc[::-1], use_container_width=True)
        to_del = st.multiselect("Delete Mistakes", options=history_view.index)
        if st.button("Delete Selected"):
            log_df.drop(to_del).to_csv(log_file, index=False); st.rerun()
