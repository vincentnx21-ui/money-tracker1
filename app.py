import streamlit as st
import pandas as pd
from datetime import datetime
import os

# --- 1. CONFIGURATION ---
LOG_FILE = "money_tracker.csv"
USER_FILE = "users.csv"
SUPER_USER = "Vincent21"
SUPER_PASS = "3123" 

st.set_page_config(page_title="Vincent's Tracker", layout="wide")

# --- 2. DATA ENGINE ---
def load_data(file, columns):
    if os.path.exists(file):
        try:
            df = pd.read_csv(file, dtype=str)
            for col in columns:
                if col not in df.columns: df[col] = "N/A"
            return df
        except:
            return pd.DataFrame(columns=columns)
    return pd.DataFrame(columns=columns)

user_df = load_data(USER_FILE, ["Username", "Password"])
log_cols = ["Date", "User", "Location", "Shop", "Item", "Quantity", "Total Cost", "Wallet Left", "Type"]
log_df = load_data(LOG_FILE, log_cols)

# --- 3. LOGIN & REGISTRATION ---
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = None

if not st.session_state.logged_in:
    tab_login, tab_reg = st.tabs(["🔑 Login", "📝 Register"])
    
    with tab_login:
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")
        if st.button("Log In", use_container_width=True):
            if u == SUPER_USER and p == SUPER_PASS:
                st.session_state.logged_in = True
                st.session_state.username = u
                st.rerun()
            else:
                match = user_df[(user_df["Username"] == u) & (user_df["Password"] == p)]
                if not match.empty:
                    st.session_state.logged_in = True
                    st.session_state.username = u
                    st.rerun()
                else:
                    st.error("Invalid Username or Password")
                    
    with tab_reg:
        nu = st.text_input("New Username")
        np = st.text_input("New Password", type="password")
        if st.button("Create Account", use_container_width=True):
            if nu and np:
                new_u = pd.DataFrame([{"Username": nu, "Password": np}])
                new_u.to_csv(USER_FILE, mode='a', index=False, header=not os.path.exists(USER_FILE))
                st.success("Registration Successful!")
    st.stop()

# --- 4. SIDEBAR & SUPERADMIN DASHBOARD ---
current_user = st.session_state.username

with st.sidebar:
    st.title(f"👤 {current_user}")
    if st.button("🚪 Logout", use_container_width=True):
        st.session_state.logged_in = False
        st.session_state.username = None
        st.rerun()
    
    st.divider()
    
    # ONLY VISIBLE TO VINCENT21
    if current_user == SUPER_USER:
        st.subheader("🛠️ Superadmin Tools")
        with st.expander("📊 View All User Accounts"):
            st.write("Below are all registered users and their plain-text passwords:")
            st.dataframe(user_df, use_container_width=True)
            
        with st.expander("🍱 Manage Master Menu"):
            al = st.text_input("Location")
            as_ = st.text_input("Stall")
            ai = st.text_input("Product")
            ap = st.number_input("Price", min_value=0.0, step=0.05)
            if st.button("Add to Menu"):
                new_item = pd.DataFrame([{"Date": "MASTER", "User": "ADMIN", "Location": al, "Shop": as_, "Item": ai, "Quantity": "1", "Total Cost": str(ap), "Wallet Left": "0", "Type": "MenuSetup"}])
                new_item.to_csv(LOG_FILE, mode='a', index=False); st.success("Added!"); st.rerun()

# --- 5. MAIN INTERFACE ---
user_log = log_df[log_df["User"] == current_user]
balance = float(user_log["Wallet Left"].iloc[-1]) if not user_log.empty else 0.0

st.header("💰 Personal Money Manager")
st.metric("My Current Balance", f"${balance:,.2f}")

t1, t2, t3, t4, t5 = st.tabs(["🛒 Order", "💵 Top Up", "🤝 Lending", "🪙 Audit", "📊 History"])

# ORDERING SYSTEM
with t1:
    locs = sorted([l for l in log_df["Location"].unique().tolist() if l != "N/A"])
    l_sel = st.selectbox("Select Location", ["-- Select --"] + locs)
    if l_sel != "-- Select --":
        stalls = sorted(log_df[log_df["Location"] == l_sel]["Shop"].unique().tolist())
        s_sel = st.selectbox("Select Stall", ["-- Select --"] + stalls)
        if s_sel != "-- Select --":
            items_df = log_df[(log_df["Location"] == l_sel) & (log_df["Shop"] == s_sel) & (log_df["Type"] == "MenuSetup")]
            p_sel = st.selectbox("Select Product", ["-- Select --"] + sorted(items_df["Item"].unique().tolist()))
            if p_sel != "-- Select --":
                u_price = float(items_df[items_df["Item"] == p_sel].iloc[-1]["Total Cost"])
                st.info(f"Price: ${u_price:.2f}")
                qty = st.number_input("How many?", min_value=1)
                if st.button("Confirm Purchase", type="primary"):
                    cost = u_price * qty
                    new_r = pd.DataFrame([{"Date": datetime.now().strftime("%Y-%m-%d"), "User": current_user, "Location": l_sel, "Shop": s_sel, "Item": p_sel, "Quantity": str(qty), "Total Cost": str(cost), "Wallet Left": str(balance - cost), "Type": "Spend"}])
                    new_r.to_csv(LOG_FILE, mode='a', index=False); st.rerun()

# TOP UP SYSTEM
with t2:
    amt = st.number_input("Amount to deposit", min_value=0.0)
    if st.button("Add Cash"):
        new_r = pd.DataFrame([{"Date": datetime.now().strftime("%Y-%m-%d"), "User": current_user, "Location": "N/A", "Shop": "N/A", "Item": "Deposit", "Quantity": "1", "Total Cost": "0", "Wallet Left": str(balance + amt), "Type": "TopUp"}])
        new_r.to_csv(LOG_FILE, mode='a', index=False); st.rerun()

# LENDING SYSTEM
with t3:
    friend = st.text_input("Who borrowed money?")
    l_amt = st.number_input("Lend amount", min_value=0.0)
    if st.button("Record Loan"):
        new_r = pd.DataFrame([{"Date": datetime.now().strftime("%Y-%m-%d"), "User": current_user, "Location": "N/A", "Shop": "N/A", "Item": f"LENT: {friend}", "Quantity": "1", "Total Cost": str(l_amt), "Wallet Left": str(balance - l_amt), "Type": "Lend"}])
        new_r.to_csv(LOG_FILE, mode='a', index=False); st.rerun()

# AUDIT SYSTEM
with t4:
    st.subheader("Wallet Audit")
    c1, c2 = st.columns(2)
    with c1:
        v100 = st.number_input("$100", 0); v50 = st.number_input("$50", 0); v10 = st.number_input("$10", 0)
    with c2:
        v1 = st.number_input("$1", 0); v50c = st.number_input("50¢", 0); v1c = st.number_input("1¢", 0)
    total = (v100*100)+(v50*50)+(v10*10)+(v1*1)+(v50c*0.5)+(v1c*0.01)
    st.write(f"### Total Cash: ${total:.2f}")

# HISTORY SYSTEM
with t5:
    if not user_log.empty:
        # Show actual user history (Spends and Topups)
        history = user_log[user_log["Type"].isin(["Spend", "TopUp", "Lend"])]
        st.dataframe(history.iloc[::-1], use_container_width=True)
