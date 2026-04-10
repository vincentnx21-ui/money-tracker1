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

# --- UTILS: Password Hashing ---
def hash_password(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

def check_password(password, hashed_password):
    return hash_password(password) == hashed_password

# --- DATABASE HELPERS ---
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

# Load Users and Transaction Data
user_df = load_data(user_file, ["Username", "Password"])
log_cols = ["Date", "User", "Location", "Shop", "Item", "Quantity", "Total Cost", "Wallet Left", "Type"]
log_df = load_data(log_file, log_cols)

# --- SESSION STATE FOR LOGIN ---
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = None

# --- AUTHENTICATION UI ---
if not st.session_state.logged_in:
    auth_tab1, auth_tab2 = st.tabs(["Login", "Register"])
    
    with auth_tab1:
        st.subheader("Welcome Back")
        l_user = st.text_input("Username", key="l_user")
        l_pwd = st.text_input("Password", type="password", key="l_pwd")
        if st.button("Login"):
            user_row = user_df[user_df["Username"] == l_user]
            if not user_row.empty and check_password(l_pwd, user_row.iloc[0]["Password"]):
                st.session_state.logged_in = True
                st.session_state.username = l_user
                st.rerun()
            else:
                st.error("Invalid username or password")

    with auth_tab2:
        st.subheader("Create Account")
        r_user = st.text_input("New Username", key="r_user")
        r_pwd = st.text_input("New Password", type="password", key="r_pwd")
        r_pwd_confirm = st.text_input("Confirm Password", type="password", key="r_pwd_confirm")
        
        if st.button("Register"):
            if not r_user or not r_pwd:
                st.warning("Please fill all fields")
            elif r_pwd != r_pwd_confirm:
                st.error("Passwords do not match")
            elif r_user in user_df["Username"].values:
                st.error("Username already exists")
            else:
                new_user = pd.DataFrame([{"Username": r_user, "Password": hash_password(r_pwd)}])
                new_user.to_csv(user_file, mode='a', index=False, header=not os.path.exists(user_file))
                st.success("Account created! Please go to Login tab.")

    st.stop() # Prevents the rest of the app from running if not logged in

# --- MAIN APP (ONLY VISIBLE IF LOGGED IN) ---
user = st.session_state.username
# Filter log to only show the logged-in user's data
user_log = log_df[log_df["User"] == user]
current_balance = float(user_log["Wallet Left"].iloc[-1]) if not user_log.empty else 0.0

st.title(f"💰 {user}'s Tracker")
st.sidebar.button("Logout", on_click=lambda: st.session_state.update({"logged_in": False, "username": None}))
st.metric("Current Balance", f"${current_balance:,.2f}")

tab1, tab2, tab3 = st.tabs(["🛒 Order Food", "💵 Top Up", "📊 History"])

# --- TAB 1: ORDER FOOD ---
with tab1:
    # 1. Select Location
    all_locs = sorted(log_df["Location"].unique().tolist()) if not log_df.empty else []
    loc_choice = st.selectbox("Select Location", ["-- Choose --"] + [l for l in all_locs if l != "N/A"])
    
    if loc_choice != "-- Choose --":
        # 2. Select Stall
        stalls = sorted(log_df[log_df["Location"] == loc_choice]["Shop"].unique().tolist())
        stall_choice = st.selectbox("Select Stall", ["-- Choose --"] + stalls)
        
        if stall_choice != "-- Choose --":
            # 3. Select Product (Filters by Stall and Location)
            items = log_df[(log_df["Location"] == loc_choice) & (log_df["Shop"] == stall_choice)]["Item"].unique().tolist()
            clean_items = sorted(list(set([name.split(' +')[0].strip() for name in items])))
            prod_choice = st.selectbox("What are you buying?", ["-- Select --"] + clean_items)
            
            if prod_choice != "-- Select --":
                # Find Price from MenuSetup rows
                price_match = log_df[(log_df["Shop"] == stall_choice) & (log_df["Item"] == prod_choice) & (log_df["Type"] == "MenuSetup")]
                base_price = float(price_match.iloc[-1]["Total Cost"]) if not price_match.empty else 0.0

                st.info(f"Price: ${base_price:.2f}")
                qty = st.number_input("Quantity", min_value=1, step=1)
                
                if st.button("Confirm Purchase", use_container_width=True, type="primary"):
                    new_row = pd.DataFrame([{
                        "Date": datetime.now().strftime("%Y-%m-%d"),
                        "User": user,
                        "Location": loc_choice,
                        "Shop": stall_choice,
                        "Item": prod_choice,
                        "Quantity": qty,
                        "Total Cost": base_price * qty,
                        "Wallet Left": current_balance - (base_price * qty),
                        "Type": "Spend"
                    }])
                    new_row.to_csv(log_file, mode='a', index=False, header=not os.path.exists(log_file))
                    st.rerun()

# --- TAB 2: TOP UP ---
with tab2:
    top_amt = st.number_input("Top up amount", min_value=0.0)
    if st.button("Add Cash"):
        nr = pd.DataFrame([{"Date": datetime.now().strftime("%Y-%m-%d"), "User": user, "Location": "N/A", "Shop": "N/A", "Item": "Top-up", "Quantity": 1, "Total Cost": 0, "Wallet Left": current_balance + top_amt, "Type": "TopUp"}])
        nr.to_csv(log_file, mode='a', index=False); st.rerun()

# --- TAB 3: HISTORY & DELETE ---
with tab3:
    if not user_log.empty:
        display_df = user_log[user_log["Type"] == "Spend"]
        st.dataframe(display_df.iloc[::-1], use_container_width=True)
        rows_to_del = st.multiselect("Select transactions to delete:", options=display_df.index)
        if st.button("Delete Selected"):
            log_df.drop(rows_to_del).to_csv(log_file, index=False); st.rerun()

# --- ADMIN SECTION (FOR ADDING MENUS) ---
st.divider()
with st.expander("🔐 Admin (Manage School Menu)"):
    adm_pwd = st.text_input("Admin Password", type="password")
    if adm_pwd == ADMIN_PASSWORD:
        st.subheader("Add Stall/Item to Master Menu")
        c1, c2, c3, c4 = st.columns([1,1,1,1])
        a_loc = c1.text_input("Location")
        a_stall = c2.text_input("Stall")
        a_item = c3.text_input("Item")
        a_price = c4.number_input("Price", step=0.05)
        
        if st.button("Save to Global Menu"):
            if a_loc and a_stall and a_item:
                setup_row = pd.DataFrame([{"Date": "N/A", "User": "ADMIN", "Location": a_loc, "Shop": a_stall, "Item": a_item, "Quantity": 1, "Total Cost": a_price, "Wallet Left": 0, "Type": "MenuSetup"}])
                setup_row.to_csv(log_file, mode='a', index=False); st.success("Added!"); st.rerun()
