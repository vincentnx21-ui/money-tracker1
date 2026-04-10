import streamlit as st
import pandas as pd
from datetime import datetime
import os

# --- CONFIG ---
log_file = "money_tracker.csv"
user_file = "users.csv"
SUPER_USER = "Vincent21"
SUPER_PASS = "3123" 

st.set_page_config(page_title="Vincent's Tracker", layout="wide")

# --- DATABASE HELPERS ---
def load_data(file, columns):
    if os.path.exists(file):
        try:
            df = pd.read_csv(file, dtype=str) # Load as string to prevent leading zero issues
            for col in columns:
                if col not in df.columns: df[col] = "N/A"
            return df
        except:
            return pd.DataFrame(columns=columns)
    return pd.DataFrame(columns=columns)

# Load Data
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
            if u == SUPER_USER and p == SUPER_PASS:
                st.session_state.logged_in = True
                st.session_state.username = u
                st.rerun()
            else:
                # Direct match check (Decoded/Plain-text)
                user_match = user_df[(user_df["Username"] == u) & (user_df["Password"] == p)]
                if not user_match.empty:
                    st.session_state.logged_in = True
                    st.session_state.username = u
                    st.rerun()
                else:
                    st.error("Invalid Username or Password")
    with t2:
        nu = st.text_input("New Username")
        np = st.text_input("New Password", type="password")
        npc = st.text_input("Confirm Password", type="password")
        if st.button("Create Account"):
            if nu and np == npc:
                if nu in user_df["Username"].values:
                    st.error("Username already taken!")
                else:
                    new_u = pd.DataFrame([{"Username": nu, "Password": np}]) # Storing plain text
                    new_u.to_csv(user_file, mode='a', index=False, header=not os.path.exists(user_file))
                    st.success("Registered! You can now log in.")
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
    
    if user == SUPER_USER:
        with st.expander("🛠️ Superadmin Dashboard"):
            st.subheader("👥 User Accounts (Decoded)")
            # This table now shows the actual passwords
            st.dataframe(user_df, use_container_width=True)
            
            st.subheader("📜 All User Activity")
            global_act = log_df[log_df["Type"] != "MenuSetup"]
            st.dataframe(global_act.iloc[::-1], use_container_width=True)
            
            st.divider()
            st.subheader("🍱 Menu Setup")
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
                    setup_row.to_csv(log_file, mode='a', index=False); st.success("Menu Updated!"); st.rerun()

# --- MAIN APP ---
user_log = log_df[log_df["User"] == user]
# Calculate balance from history
balance = float(user_log["Wallet Left"].iloc[-1]) if not user_log.empty else 0.0

st.title(f"💰 Welcome, {user}")
st.metric("Wallet Balance", f"${balance:,.2f}")

tab1, tab2, tab3, tab4, tab5 = st.tabs(["🛒 Order", "💵 Top Up", "🤝 Lending", "🪙 Audit", "📊 History"])

# ... [Rest of the tab logic (Order, Top Up, Lending, Audit, History) remains the same as previous version] ...
# (Included for completeness in your file)

with tab1:
    locs = sorted([l for l in log_df["Location"].unique().tolist() if l != "N/A"])
    l_sel = st.selectbox("Where are you?", ["-- Select --"] + locs)
    if l_sel != "-- Select --":
        stalls = sorted(log_df[log_df["Location"] == l_sel]["Shop"].unique().tolist())
        s_sel = st.selectbox("Stall", ["-- Select --"] + stalls)
        if s_sel != "-- Select --":
            items_df = log_df[(log_df["Location"] == l_sel) & (log_df["Shop"] == s_sel)]
            p_sel = st.selectbox("Product", ["-- Select --"] + sorted(items_df["Item"].unique().tolist()))
            if p_sel != "-- Select --":
                price_match = items_df[(items_df["Item"] == p_sel) & (items_df["Type"] == "MenuSetup")]
                u_price = float(price_match.iloc[-1]["Total Cost"]) if not price_match.empty else 0.0
                st.info(f"Price: ${u_price:.2f}")
                qty = st.number_input("Quantity", min_value=1)
                if st.button("Confirm Purchase"):
                    cost = u_price * qty
                    new_r = pd.DataFrame([{"Date": datetime.now().strftime("%Y-%m-%d"), "User": user, "Location": l_sel, "Shop": s_sel, "Item": p_sel, "Quantity": qty, "Total Cost": cost, "Wallet Left": balance - cost, "Type": "Spend"}])
                    new_r.to_csv(log_file, mode='a', index=False); st.rerun()

with tab2:
    amt = st.number_input("Amount", min_value=0.0)
    if st.button("Deposit"):
        new_r = pd.DataFrame([{"Date": datetime.now().strftime("%Y-%m-%d"), "User": user, "Location": "N/A", "Shop": "N/A", "Item": "Deposit", "Quantity": 1, "Total Cost": 0, "Wallet Left": balance + amt, "Type": "TopUp"}])
        new_r.to_csv(log_file, mode='a', index=False); st.rerun()

with tab3:
    st.subheader("Lend Money")
    friend = st.text_input("Friend Name")
    l_amt = st.number_input("Lend Amt", min_value=0.0)
    if st.button("Lend"):
        new_r = pd.DataFrame([{"Date": datetime.now().strftime("%Y-%m-%d"), "User": user, "Location": "N/A", "Shop": "N/A", "Item": f"LENT: {friend}", "Quantity": 1, "Total Cost": l_amt, "Wallet Left": balance - l_amt, "Type": "Lend"}])
        new_r.to_csv(log_file, mode='a', index=False); st.rerun()

with tab4:
    st.subheader("Audit")
    c1, c2 = st.columns(2)
    with c1:
        n100 = st.number_input("$100", 0); n50 = st.number_input("$50", 0); n10 = st.number_input("$10", 0)
    with c2:
        c1 = st.number_input("$1", 0); c50 = st.number_input("50¢", 0); c01 = st.number_input("1¢", 0)
    total_phys = (n100*100)+(n50*50)+(n10*10)+(c1*1)+(c50*0.5)+(c01*0.01)
    st.write(f"### Total: ${total_phys:.2f}")

with tab5:
    if not user_log.empty:
        h_view = user_log[user_log["Type"].isin(["Spend", "TopUp", "Lend"])]
        st.dataframe(h_view.iloc[::-1], use_container_width=True)
