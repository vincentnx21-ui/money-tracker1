import streamlit as st
import pandas as pd
from datetime import datetime
import os
import hashlib

# --- CONFIG ---
log_file = "money_tracker.csv"
user_file = "users.csv"
ADMIN_PASSWORD = "123"
SUPER_USER = "Vincent21" # No password needed for admin settings
# Note: Vincent21 still needs his login password "3123" to enter the app initially.

st.set_page_config(page_title="Personal Finance Tracker", layout="centered")

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
            # Special bypass for the specific request if account doesn't exist yet
            # or standard check against users.csv
            row = user_df[user_df["Username"] == u]
            if u == SUPER_USER and p == "3123":
                st.session_state.logged_in = True
                st.session_state.username = u
                st.rerun()
            elif not row.empty and check_password(p, row.iloc[0]["Password"]):
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
                st.success("Account created!")
    st.stop()

# --- SIDEBAR (LOGOUT & ADMIN) ---
user = st.session_state.username

with st.sidebar:
    st.title(f"👤 {user}")
    if st.button("🚪 Logout", use_container_width=True):
        st.session_state.logged_in = False
        st.session_state.username = None
        st.rerun()
    
    st.divider()
    
    with st.expander("🛠️ Administration Entry"):
        # LOGIC CHANGE: Check if user is Vincent21
        is_admin = False
        if user == SUPER_USER:
            st.success("Admin Access Granted (Vincent21)")
            is_admin = True
        else:
            adm_pwd = st.text_input("Admin Password Required", type="password")
            if adm_pwd == ADMIN_PASSWORD:
                is_admin = True
            elif adm_pwd != "":
                st.error("Incorrect Admin Password")

        if is_admin:
            st.subheader("Master Menu Setup")
            a_loc = st.text_input("Location Name")
            a_stall = st.text_input("Stall Name")
            a_item = st.text_input("Product Name")
            a_price = st.number_input("Unit Price", min_value=0.0, step=0.05)
            
            if st.button("Add to Master Menu"):
                if a_loc and a_stall and a_item:
                    setup_row = pd.DataFrame([{
                        "Date": "MASTER", "User": "ADMIN", "Location": a_loc, 
                        "Shop": a_stall, "Item": a_item, "Quantity": 1, 
                        "Total Cost": a_price, "Wallet Left": 0, "Type": "MenuSetup"
                    }])
                    setup_row.to_csv(log_file, mode='a', index=False); st.success("Saved!"); st.rerun()

# --- MAIN APP ---
user_log = log_df[log_df["User"] == user]
balance = float(user_log["Wallet Left"].iloc[-1]) if not user_log.empty else 0.0

st.title("💰 Smart Budget Tracker")
st.metric("App Balance", f"${balance:,.2f}")

tab1, tab2, tab3, tab4, tab5 = st.tabs(["🛒 Order", "💵 Top Up", "🤝 Lending", "🪙 Audit", "📊 History"])

# --- TAB 1: ORDER ---
with tab1:
    locs = sorted([l for l in log_df["Location"].unique().tolist() if l != "N/A"])
    l_sel = st.selectbox("Where are you?", ["-- Choose Location --"] + locs)
    if l_sel != "-- Choose Location --":
        stalls = sorted(log_df[log_df["Location"] == l_sel]["Shop"].unique().tolist())
        s_sel = st.selectbox("Select Stall", ["-- Choose Stall --"] + stalls)
        if s_sel != "-- Choose Stall --":
            items_df = log_df[(log_df["Location"] == l_sel) & (log_df["Shop"] == s_sel)]
            p_sel = st.selectbox("Select Product", ["-- Select Product --"] + sorted(items_df["Item"].unique().tolist()))
            if p_sel != "-- Select Product --":
                price_match = items_df[(items_df["Item"] == p_sel) & (items_df["Type"] == "MenuSetup")]
                u_price = float(price_match.iloc[-1]["Total Cost"]) if not price_match.empty else 0.0
                st.info(f"Price: ${u_price:.2f}")
                qty = st.number_input("Quantity", min_value=1)
                if st.button("Confirm Purchase", use_container_width=True, type="primary"):
                    cost = u_price * qty
                    new_r = pd.DataFrame([{"Date": datetime.now().strftime("%Y-%m-%d"), "User": user, "Location": l_sel, "Shop": s_sel, "Item": p_sel, "Quantity": qty, "Total Cost": cost, "Wallet Left": balance - cost, "Type": "Spend"}])
                    new_r.to_csv(log_file, mode='a', index=False); st.rerun()

# --- TAB 2: TOP UP ---
with tab2:
    t_amt = st.number_input("Amount to add", min_value=0.0)
    if st.button("Add Funds"):
        new_r = pd.DataFrame([{"Date": datetime.now().strftime("%Y-%m-%d"), "User": user, "Location": "N/A", "Shop": "N/A", "Item": "Deposit", "Quantity": 1, "Total Cost": 0, "Wallet Left": balance + t_amt, "Type": "TopUp"}])
        new_r.to_csv(log_file, mode='a', index=False); st.rerun()

# --- TAB 3: MONEY LENDING ---
with tab3:
    st.subheader("Lend Money")
    l_friend = st.text_input("Friend's Name")
    l_amt = st.number_input("Amount", min_value=0.0)
    if st.button("Record Loan"):
        if l_friend and l_amt > 0:
            new_r = pd.DataFrame([{"Date": datetime.now().strftime("%Y-%m-%d"), "User": user, "Location": "N/A", "Shop": "N/A", "Item": f"LENT: {l_friend}", "Quantity": 1, "Total Cost": l_amt, "Wallet Left": balance - l_amt, "Type": "Lend"}])
            new_r.to_csv(log_file, mode='a', index=False); st.rerun()

# --- TAB 4: MONEY AUDIT ---
with tab4:
    st.subheader("Physical Cash Audit")
    col1, col2 = st.columns(2)
    with col1:
        n100 = st.number_input("$100 Bills", 0, step=1)
        n50 = st.number_input("$50 Bills", 0, step=1)
        n10 = st.number_input("$10 Bills", 0, step=1)
        n5 = st.number_input("$5 Bills", 0, step=1)
        n2 = st.number_input("$2 Bills", 0, step=1)
    with col2:
        c1 = st.number_input("$1 Coins", 0, step=1)
        c50 = st.number_input("50¢ Coins", 0, step=1)
        c20 = st.number_input("20¢ Coins", 0, step=1)
        c10 = st.number_input("10¢ Coins", 0, step=1)
        c5 = st.number_input("5¢ Coins", 0, step=1)
        c01 = st.number_input("1¢ Coins", 0, step=1)
    
    total_phys = (n100*100) + (n50*50) + (n10*10) + (n5*5) + (n2*2) + \
                 (c1*1) + (c50*0.5) + (c20*0.2) + (c10*0.1) + (c5*0.05) + (c01*0.01)
    
    st.divider()
    st.write(f"### Total Physical Cash: ${total_phys:.2f}")
    diff = total_phys - balance
    if abs(diff) < 0.01:
        st.success("Perfect Match!")
    else:
        st.info(f"Difference: ${diff:.2f}")

# --- TAB 5: HISTORY ---
with tab5:
    if not user_log.empty:
        h_data = user_log[user_log["Type"].isin(["Spend", "TopUp", "Lend"])]
        st.dataframe(h_data.iloc[::-1], use_container_width=True)
        to_del = st.multiselect("Select transactions to remove:", options=h_data.index)
        if st.button("Delete Selected"):
            log_df.drop(to_del).to_csv(log_file, index=False); st.rerun()
