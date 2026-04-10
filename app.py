import streamlit as st
import pandas as pd
from datetime import datetime
import os

# --- 1. SETTINGS & STYLING ---
USER_FILE = "users.csv"
LOG_FILE = "money_tracker.csv"
SUPER_USER = "Vincent21"
SUPER_PASS = "3123"

st.set_page_config(page_title="Personal Finance System", layout="wide")

# Custom CSS for "Pro" look
st.markdown("""
    <style>
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    div.stButton > button:first-child { background-color: #007bff; color: white; width: 100%; border-radius: 5px; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. DATA CORE ---
def load_data(file, cols):
    if os.path.exists(file):
        return pd.read_csv(file, dtype=str)
    return pd.DataFrame(columns=cols)

user_df = load_data(USER_FILE, ["Username", "Password"])
log_df = load_data(LOG_FILE, ["Date", "User", "Location", "Shop", "Item", "Quantity", "Total Cost", "Wallet Left", "Type"])

# --- 3. AUTHENTICATION ---
if "auth" not in st.session_state:
    st.session_state.auth = False
    st.session_state.user = None

if not st.session_state.auth:
    t1, t2 = st.tabs(["🔒 Login", "📝 Register"])
    with t1:
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")
        if st.button("Access Account"):
            if u == SUPER_USER and p == SUPER_PASS:
                st.session_state.auth, st.session_state.user = True, u
                st.rerun()
            else:
                match = user_df[(user_df["Username"] == u) & (user_df["Password"] == p)]
                if not match.empty:
                    st.session_state.auth, st.session_state.user = True, u
                    st.rerun()
                else: st.error("Access Denied.")
    with t2:
        nu = st.text_input("New Username")
        np = st.text_input("New Password", type="password")
        if st.button("Create Account"):
            if nu and np:
                pd.DataFrame([{"Username": nu, "Password": np}]).to_csv(USER_FILE, mode='a', index=False, header=not os.path.exists(USER_FILE))
                st.success("Registered! Please login.")
    st.stop()

# --- 4. NAVIGATION & SIDEBAR ---
current_user = st.session_state.user
# Common User Menu
menu = ["🏠 Home Dashboard", "🛒 Order Food", "💵 Top Up", "🤝 Lending", "🪙 Audit", "📊 My History"]

# Admin Addition
if current_user == SUPER_USER:
    menu.append("🛠️ SUPERADMIN SPACE")

with st.sidebar:
    st.title(f"👤 {current_user}")
    choice = st.radio("Navigation", menu)
    st.divider()
    if st.button("Logout"):
        st.session_state.auth = False
        st.rerun()

# Global Data Calculation
user_log = log_df[log_df["User"] == current_user]
balance = float(user_log["Wallet Left"].iloc[-1]) if not user_log.empty else 0.0

# --- 5. APP SPACES ---

# --- A: USER FEATURES ---
if choice == "🏠 Home Dashboard":
    st.header(f"Welcome, {current_user}")
    c1, c2 = st.columns(2)
    c1.metric("Wallet Balance", f"${balance:,.2f}")
    c2.info(f"**Last Login:** {datetime.now().strftime('%Y-%m-%d')}")

elif choice == "🛒 Order Food":
    st.header("Place Order")
    # Menu Filter Logic
    locs = sorted([l for l in log_df["Location"].unique().tolist() if l != "N/A"])
    l_sel = st.selectbox("Location", ["-- Select --"] + locs)
    if l_sel != "-- Select --":
        items = log_df[(log_df["Location"] == l_sel) & (log_df["Type"] == "MenuSetup")]
        p_sel = st.selectbox("Product", items["Item"].tolist())
        price = float(items[items["Item"] == p_sel].iloc[-1]["Total Cost"])
        st.write(f"Price: **${price:.2f}**")
        qty = st.number_input("Qty", 1)
        if st.button("Confirm Order"):
            cost = price * qty
            nr = pd.DataFrame([{"Date": datetime.now().strftime("%Y-%m-%d"), "User": current_user, "Location": l_sel, "Shop": "Shop", "Item": p_sel, "Quantity": str(qty), "Total Cost": str(cost), "Wallet Left": str(balance - cost), "Type": "Spend"}])
            nr.to_csv(LOG_FILE, mode='a', index=False); st.balloons(); st.rerun()

elif choice == "🪙 Audit":
    st.header("Cash Audit")
    v100 = st.number_input("$100 Bills", 0); v50 = st.number_input("$50 Bills", 0)
    total = (v100 * 100) + (v50 * 50) # ... add more denominations as needed
    st.subheader(f"Calculated: ${total:.2f}")
    st.write(f"Diff: ${total - balance:.2f}")

elif choice == "📊 My History":
    st.header("My Transactions")
    st.dataframe(user_log[user_log["Type"] != "MenuSetup"].iloc[::-1], use_container_width=True)

# --- B: ADMIN FEATURES (ONLY FOR VINCENT) ---
elif choice == "🛠️ SUPERADMIN SPACE":
    st.title("🛡️ Superadmin Control")
    t_acc, t_logs, t_setup = st.tabs(["👤 Accounts", "🌍 Global Logs", "🍱 Menu Setup"])
    
    with t_acc:
        st.subheader("User List (Passwords Visible)")
        st.dataframe(user_df, use_container_width=True)
        
    with t_logs:
        st.subheader("Every Activity in System")
        st.dataframe(log_df[log_df["Type"] != "MenuSetup"].iloc[::-1], use_container_width=True)
        
    with t_setup:
        st.subheader("Add New Item to Global Menu")
        al = st.text_input("New Location Name")
        ai = st.text_input("New Item Name")
        ap = st.number_input("Set Price", 0.0)
        if st.button("Add to System Menu"):
            nr = pd.DataFrame([{"Date": "MASTER", "User": "ADMIN", "Location": al, "Shop": "N/A", "Item": ai, "Quantity": "1", "Total Cost": str(ap), "Wallet Left": "0", "Type": "MenuSetup"}])
            nr.to_csv(LOG_FILE, mode='a', index=False); st.success("Added!"); st.rerun()
