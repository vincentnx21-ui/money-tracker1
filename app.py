import streamlit as st
import pandas as pd
from datetime import datetime
import os
import hashlib

# --- CONFIG ---
log_file = "money_tracker.csv"
user_file = "users.csv"
SUPER_USER = "Vincent21"
SUPER_PASS = "3123" 

st.set_page_config(page_title="Vincent's Tracker", layout="centered")

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
            # 1. Check for Super User
            if u == SUPER_USER and p == SUPER_PASS:
                st.session_state.logged_in = True
                st.session_state.username = u
                st.rerun()
            # 2. Check standard users
            else:
                row = user_df[user_df["Username"] == u]
                if not row.empty and check_password(p, row.iloc[0]["Password"]):
                    st.session_state.logged_in = True
                    st.session_state.username = u
                    st.rerun()
                else:
                    st.error("Invalid Credentials")
    with t2:
        nu = st.text_input("New Username")
        np = st.text_input("New Password", type="password")
        npc = st.text_input("Confirm Password", type="password")
        if st.button("Create Account"):
            if nu and np == npc:
                new_u = pd.DataFrame([{"Username": nu, "Password": hash_password(np)}])
                new_u.to_csv(user_file, mode='a', index=False, header=not os.path.exists(user_file))
                st.success("Registered!")
    st.stop()

# --- SIDEBAR ---
user = st.session_state.username

with st.sidebar:
    st.title(f"👤 {user}")
    if st.button("🚪 Logout", use_container_width=True):
        st.session_state.logged_in = False
        st.session_state.username = None
        st.rerun()
    
    st.divider()
    
    # --- RESTRICTED ADMIN SECTION ---
    # This block is ONLY rendered if the user is Vincent21
    if user == SUPER_USER:
        with st.expander("🛠️ Administration Entry"):
            st.subheader("Master Menu Setup")
            a_loc = st.text_input("Location")
            a_stall = st.text_input("Stall")
            a_item = st.text_input("Product")
            a_price = st.number_input("Price", min_value=0.0, step=0.05)
            
            if st.button("Save to Global Menu"):
                if a_loc and a_stall and a_item:
                    setup_row = pd.DataFrame([{
                        "Date": "MASTER", "User": "ADMIN", "Location": a_loc, 
                        "Shop": a_stall, "Item": a_item, "Quantity": 1, 
                        "Total Cost": a_price, "Wallet Left": 0, "Type": "MenuSetup"
                    }])
                    setup_row.to_csv(log_file, mode='a', index=False); st.success("Saved!"); st.rerun()
            
            st.divider()
            if st.button("🧨 Wipe All Transactions", type="primary"):
                # Deletes spending but keeps the menu setup
                keep_menu = log_df[log_df["Type"] == "MenuSetup"]
                keep_menu.to_csv(log_file, index=False); st.rerun()

# --- MAIN APP ---
user_log = log_df[log_df["User"] == user]
balance = float(user_log["Wallet Left"].iloc[-1]) if not user_log.empty else 0.0

st.title("💰 Budget Tracker")
st.metric("My Balance", f"${balance:,.2f}")

tab1, tab2, tab3, tab4, tab5 = st.tabs(["🛒 Order", "💵 Top Up", "🤝 Lending", "🪙 Audit", "📊 History"])

# Order Tab
with tab1:
    locs = sorted([l for l in log_df["Location"].unique().tolist() if l != "N/A"])
    l_sel = st.selectbox("Location", ["-- Select --"] + locs)
    if l_sel != "-- Select --":
        stalls = sorted(log_df[log_df["Location"] == l_sel]["Shop"].unique().tolist())
        s_sel = st.selectbox("Stall", ["-- Select --"] + stalls)
        if s_sel != "-- Select --":
            items_df = log_df[(log_df["Location"] == l_sel) & (log_df["Shop"] == s_sel)]
            p_sel = st.selectbox("Product", ["-- Select --"] + sorted(items_df["Item"].unique().tolist()))
            if p_sel != "-- Select --":
                price_match = items_df[(items_df["Item"] == p_sel) & (items_df["Type"] == "MenuSetup")]
                u_price = float(price_match.iloc[-1]["Total Cost"]) if not price_match.empty else 0.0
                st.info(f"Fixed Price: ${u_price:.2f}")
                qty = st.number_input("Quantity", min_value=1)
                if st.button("Confirm Purchase", type="primary"):
                    cost = u_price * qty
                    new_r = pd.DataFrame([{"Date": datetime.now().strftime("%Y-%m-%d"), "User": user, "Location": l_sel, "Shop": s_sel, "Item": p_sel, "Quantity": qty, "Total Cost": cost, "Wallet Left": balance - cost, "Type": "Spend"}])
                    new_r.to_csv(log_file, mode='a', index=False); st.rerun()

# Top Up Tab
with tab2:
    amt = st.number_input("Top up amt", min_value=0.0)
    if st.button("Deposit"):
        new_r = pd.DataFrame([{"Date": datetime.now().strftime("%Y-%m-%d"), "User": user, "Location": "N/A", "Shop": "N/A", "Item": "Deposit", "Quantity": 1, "Total Cost": 0, "Wallet Left": balance + amt, "Type": "TopUp"}])
        new_r.to_csv(log_file, mode='a', index=False); st.rerun()

# Lending Tab
with tab3:
    st.subheader("Money Lending")
    friend = st.text_input("Who borrowed?")
    l_amt = st.number_input("Lend Amount", min_value=0.0)
    if st.button("Record Lending"):
        new_r = pd.DataFrame([{"Date": datetime.now().strftime("%Y-%m-%d"), "User": user, "Location": "N/A", "Shop": "N/A", "Item": f"LENT: {friend}", "Quantity": 1, "Total Cost": l_amt, "Wallet Left": balance - l_amt, "Type": "Lend"}])
        new_r.to_csv(log_file, mode='a', index=False); st.rerun()

# Audit Tab
with tab4:
    st.subheader("Denomination Calculator")
    c1, c2 = st.columns(2)
    with c1:
        n100 = st.number_input("$100", 0); n50 = st.number_input("$50", 0); n10 = st.number_input("$10", 0)
        n5 = st.number_input("$5", 0); n2 = st.number_input("$2", 0)
    with c2:
        c1 = st.number_input("$1", 0); c50 = st.number_input("50¢", 0); c20 = st.number_input("20¢", 0)
        c10 = st.number_input("10¢", 0); c5 = st.number_input("5¢", 0); c01 = st.number_input("1¢", 0)
    total_phys = (n100*100)+(n50*50)+(n10*10)+(n5*5)+(n2*2)+(c1*1)+(c50*0.5)+(c20*0.2)+(c10*0.1)+(c5*0.05)+(c01*0.01)
    st.write(f"### Cash on Hand: ${total_phys:.2f}")
    st.write(f"Difference: ${total_phys - balance:.2f}")

# History Tab
with tab5:
    if not user_log.empty:
        h_view = user_log[user_log["Type"].isin(["Spend", "TopUp", "Lend"])]
        st.dataframe(h_view.iloc[::-1], use_container_width=True)
        to_del = st.multiselect("Select to remove", options=h_view.index)
        if st.button("Clear Selected"):
            log_df.drop(to_del).to_csv(log_file, index=False); st.rerun()
