import streamlit as st
import pandas as pd
from datetime import datetime
import os

# --- CONFIG ---
log_file = "money_tracker.csv"
ADMIN_PASSWORD = "C0D3AL13N@_@#_#" # <--- CHANGE YOUR PASSWORD HERE

st.set_page_config(page_title="Smart Tracker", layout="centered")

# --- DATABASE HELPER ---
def load_data(file, columns):
    if os.path.exists(file):
        try:
            df = pd.read_csv(file)
            if "Shop" not in df.columns: df["Shop"] = "Unknown"
            return df
        except:
            return pd.DataFrame(columns=columns)
    return pd.DataFrame(columns=columns)

log_cols = ["Date", "Item", "Shop", "Quantity", "Total Cost", "Wallet Left", "Type"]
log_df = load_data(log_file, log_cols)
current_balance = float(log_df["Wallet Left"].iloc[-1]) if not log_df.empty else 0.0

if "addons_list" not in st.session_state:
    st.session_state.addons_list = []

st.title("💰 Smart Money Tracker")
st.metric("App Balance", f"${current_balance:,.2f}")

tab1, tab2, tab3, tab4 = st.tabs(["🛒 Purchase", "💵 Top Up", "🤝 Lend", "🪙 Audit"])

# --- TAB 1: PURCHASE (CLEAN PRICE LOGIC) ---
with tab1:
    st.subheader("Order Builder")
    all_shops = sorted([s for s in log_df["Shop"].unique().tolist() if s != "N/A"]) if not log_df.empty else []
    shop_name = st.selectbox("Where are you?", ["-- New Shop --"] + all_shops)
    if shop_name == "-- New Shop --":
        shop_name = st.text_input("Enter Shop Name")

    clean_items = []
    if not log_df.empty and shop_name != "-- New Shop --":
        raw_items = log_df[(log_df["Shop"] == shop_name) & (log_df["Type"] == "Spend")]["Item"].unique().tolist()
        clean_items = sorted(list(set([name.split(' +')[0].strip() for name in raw_items])))
    
    selection = st.selectbox("What are you buying?", ["-- New Item --"] + clean_items)
    
    # --- RIGOROUS BASE PRICE SEARCH ---
    suggested_base = 0.0
    if selection != "-- New Item --":
        # 1. Search for the last entry that is EXACTLY the selection (no extras)
        exact_match = log_df[(log_df["Shop"] == shop_name) & (log_df["Item"] == selection)]
        if not exact_match.empty:
            suggested_base = float(exact_match.iloc[-1]["Total Cost"] / exact_match.iloc[-1]["Quantity"])
        else:
            # 2. Fallback: Search for any variation but warn user
            fuzzy_match = log_df[(log_df["Shop"] == shop_name) & (log_df["Item"].str.startswith(selection))]
            if not fuzzy_match.empty:
                suggested_base = float(fuzzy_match.iloc[-1]["Total Cost"] / fuzzy_match.iloc[-1]["Quantity"])
                st.caption("⚠️ Price might include extras from last time. Please check.")

    i_name = st.text_input("Item Name", value="" if selection == "-- New Item --" else selection)
    base_price = st.number_input("Base Price ($)", min_value=0.0, step=0.05, value=suggested_base, key=f"p_{selection}")

    st.divider()
    ca, cb, cc = st.columns([2, 1, 1])
    en = ca.text_input("Extra", key="en")
    ep = cb.number_input("$", min_value=0.0, step=0.05, key="ep")
    if cc.button("➕ Add"):
        if en:
            st.session_state.addons_list.append({"name": en, "price": ep})
            st.rerun()

    total_ex = 0.0
    ex_names = []
    for add in st.session_state.addons_list:
        st.write(f"✅ {add['name']} (+${add['price']:.2f})")
        total_ex += add['price']
        ex_names.append(add['name'])
    
    if st.session_state.addons_list and st.button("Clear Extras"):
        st.session_state.addons_list = []
        st.rerun()

    qty = st.number_input("Quantity", min_value=1, step=1)
    final_total = (base_price + total_ex) * qty
    if st.button("Confirm Final Order", use_container_width=True, type="primary"):
        if i_name and shop_name:
            full_name = i_name + (" +" + " +".join(ex_names) if ex_names else "")
            new_row = pd.DataFrame([{"Date": datetime.now().strftime("%Y-%m-%d"), "Item": full_name, "Shop": shop_name, "Quantity": qty, "Total Cost": final_total, "Wallet Left": current_balance - final_total, "Type": "Spend"}])
            new_row.to_csv(log_file, mode='a', header=not os.path.isfile(log_file), index=False)
            st.session_state.addons_list = []
            st.rerun()

# --- OTHER TABS (TOP UP, LEND, AUDIT) ---
with tab2:
    top = st.number_input("Amount", min_value=0.0)
    if st.button("Add Cash"):
        nr = pd.DataFrame([{"Date": datetime.now().strftime("%Y-%m-%d"), "Item": "TOP UP", "Shop": "N/A", "Quantity": 1, "Total Cost": 0, "Wallet Left": current_balance + top, "Type": "TopUp"}])
        nr.to_csv(log_file, mode='a', index=False); st.rerun()

with tab3:
    fr = st.text_input("Friend")
    am = st.number_input("Amt", min_value=0.0)
    if st.button("Lend"):
        nr = pd.DataFrame([{"Date": datetime.now().strftime("%Y-%m-%d"), "Item": f"LENT TO: {fr}", "Shop": "N/A", "Quantity": 1, "Total Cost": am, "Wallet Left": current_balance - am, "Type": "Lend"}])
        nr.to_csv(log_file, mode='a', index=False); st.rerun()

with tab4:
    st.subheader("Cash Audit")
    # (Audit counting logic remains same)

# --- ADMINISTRATION MENU (PASSWORD PROTECTED) ---
st.divider()
st.header("🔐 Administration")

pwd = st.text_input("Enter Admin Password", type="password")

if pwd == ADMIN_PASSWORD:
    st.success("Access Granted")
    
    # MENU MANAGEMENT
    st.subheader("🧹 Menu Management")
    m_col1, m_col2 = st.columns(2)
    with m_col1:
        s_wipe = st.selectbox("Forget Shop", ["-- Select --"] + all_shops)
        if st.button("Delete Shop"):
            log_df[log_df["Shop"] != s_wipe].to_csv(log_file, index=False)
            st.rerun()
    with m_col2:
        i_wipe = st.selectbox("Forget Item", ["-- Select --"] + clean_items)
        if st.button("Delete Item"):
            log_df[~log_df["Item"].str.startswith(i_wipe)].to_csv(log_file, index=False)
            st.rerun()

    # HISTORY MANAGEMENT
    st.subheader("📊 Transaction History")
    st.dataframe(log_df.iloc[::-1], use_container_width=True)
    rows_to_del = st.multiselect("Delete specific rows:", options=log_df.index, format_func=lambda x: f"{log_df.loc[x, 'Item']} (${log_df.loc[x, 'Total Cost']:.2f})")
    
    d_col1, d_col2 = st.columns(2)
    if d_col1.button("Delete Selected"):
        log_df.drop(rows_to_del).to_csv(log_file, index=False); st.rerun()
    if d_col2.button("🧨 Wipe All Data", type="primary"):
        if os.path.exists(log_file): os.remove(log_file); st.rerun()
        
elif pwd != "":
    st.error("Incorrect Password")import streamlit as st
import pandas as pd
from datetime import datetime
import os

# --- CONFIG ---
log_file = "money_tracker.csv"
ADMIN_PASSWORD = "123" # <--- CHANGE YOUR PASSWORD HERE

st.set_page_config(page_title="Smart Tracker", layout="centered")

# --- DATABASE HELPER ---
def load_data(file, columns):
    if os.path.exists(file):
        try:
            df = pd.read_csv(file)
            if "Shop" not in df.columns: df["Shop"] = "Unknown"
            return df
        except:
            return pd.DataFrame(columns=columns)
    return pd.DataFrame(columns=columns)

log_cols = ["Date", "Item", "Shop", "Quantity", "Total Cost", "Wallet Left", "Type"]
log_df = load_data(log_file, log_cols)
current_balance = float(log_df["Wallet Left"].iloc[-1]) if not log_df.empty else 0.0

if "addons_list" not in st.session_state:
    st.session_state.addons_list = []

st.title("💰 Smart Money Tracker")
st.metric("App Balance", f"${current_balance:,.2f}")

tab1, tab2, tab3, tab4 = st.tabs(["🛒 Purchase", "💵 Top Up", "🤝 Lend", "🪙 Audit"])

# --- TAB 1: PURCHASE (CLEAN PRICE LOGIC) ---
with tab1:
    st.subheader("Order Builder")
    all_shops = sorted([s for s in log_df["Shop"].unique().tolist() if s != "N/A"]) if not log_df.empty else []
    shop_name = st.selectbox("Where are you?", ["-- New Shop --"] + all_shops)
    if shop_name == "-- New Shop --":
        shop_name = st.text_input("Enter Shop Name")

    clean_items = []
    if not log_df.empty and shop_name != "-- New Shop --":
        raw_items = log_df[(log_df["Shop"] == shop_name) & (log_df["Type"] == "Spend")]["Item"].unique().tolist()
        clean_items = sorted(list(set([name.split(' +')[0].strip() for name in raw_items])))
    
    selection = st.selectbox("What are you buying?", ["-- New Item --"] + clean_items)
    
    # --- RIGOROUS BASE PRICE SEARCH ---
    suggested_base = 0.0
    if selection != "-- New Item --":
        # 1. Search for the last entry that is EXACTLY the selection (no extras)
        exact_match = log_df[(log_df["Shop"] == shop_name) & (log_df["Item"] == selection)]
        if not exact_match.empty:
            suggested_base = float(exact_match.iloc[-1]["Total Cost"] / exact_match.iloc[-1]["Quantity"])
        else:
            # 2. Fallback: Search for any variation but warn user
            fuzzy_match = log_df[(log_df["Shop"] == shop_name) & (log_df["Item"].str.startswith(selection))]
            if not fuzzy_match.empty:
                suggested_base = float(fuzzy_match.iloc[-1]["Total Cost"] / fuzzy_match.iloc[-1]["Quantity"])
                st.caption("⚠️ Price might include extras from last time. Please check.")

    i_name = st.text_input("Item Name", value="" if selection == "-- New Item --" else selection)
    base_price = st.number_input("Base Price ($)", min_value=0.0, step=0.05, value=suggested_base, key=f"p_{selection}")

    st.divider()
    ca, cb, cc = st.columns([2, 1, 1])
    en = ca.text_input("Extra", key="en")
    ep = cb.number_input("$", min_value=0.0, step=0.05, key="ep")
    if cc.button("➕ Add"):
        if en:
            st.session_state.addons_list.append({"name": en, "price": ep})
            st.rerun()

    total_ex = 0.0
    ex_names = []
    for add in st.session_state.addons_list:
        st.write(f"✅ {add['name']} (+${add['price']:.2f})")
        total_ex += add['price']
        ex_names.append(add['name'])
    
    if st.session_state.addons_list and st.button("Clear Extras"):
        st.session_state.addons_list = []
        st.rerun()

    qty = st.number_input("Quantity", min_value=1, step=1)
    final_total = (base_price + total_ex) * qty
    if st.button("Confirm Final Order", use_container_width=True, type="primary"):
        if i_name and shop_name:
            full_name = i_name + (" +" + " +".join(ex_names) if ex_names else "")
            new_row = pd.DataFrame([{"Date": datetime.now().strftime("%Y-%m-%d"), "Item": full_name, "Shop": shop_name, "Quantity": qty, "Total Cost": final_total, "Wallet Left": current_balance - final_total, "Type": "Spend"}])
            new_row.to_csv(log_file, mode='a', header=not os.path.isfile(log_file), index=False)
            st.session_state.addons_list = []
            st.rerun()

# --- OTHER TABS (TOP UP, LEND, AUDIT) ---
with tab2:
    top = st.number_input("Amount", min_value=0.0)
    if st.button("Add Cash"):
        nr = pd.DataFrame([{"Date": datetime.now().strftime("%Y-%m-%d"), "Item": "TOP UP", "Shop": "N/A", "Quantity": 1, "Total Cost": 0, "Wallet Left": current_balance + top, "Type": "TopUp"}])
        nr.to_csv(log_file, mode='a', index=False); st.rerun()

with tab3:
    fr = st.text_input("Friend")
    am = st.number_input("Amt", min_value=0.0)
    if st.button("Lend"):
        nr = pd.DataFrame([{"Date": datetime.now().strftime("%Y-%m-%d"), "Item": f"LENT TO: {fr}", "Shop": "N/A", "Quantity": 1, "Total Cost": am, "Wallet Left": current_balance - am, "Type": "Lend"}])
        nr.to_csv(log_file, mode='a', index=False); st.rerun()

with tab4:
    st.subheader("Cash Audit")
    # (Audit counting logic remains same)

# --- ADMINISTRATION MENU (PASSWORD PROTECTED) ---
st.divider()
st.header("🔐 Administration")

pwd = st.text_input("Enter Admin Password", type="password")

if pwd == ADMIN_PASSWORD:
    st.success("Access Granted")
    
    # MENU MANAGEMENT
    st.subheader("🧹 Menu Management")
    m_col1, m_col2 = st.columns(2)
    with m_col1:
        s_wipe = st.selectbox("Forget Shop", ["-- Select --"] + all_shops)
        if st.button("Delete Shop"):
            log_df[log_df["Shop"] != s_wipe].to_csv(log_file, index=False)
            st.rerun()
    with m_col2:
        i_wipe = st.selectbox("Forget Item", ["-- Select --"] + clean_items)
        if st.button("Delete Item"):
            log_df[~log_df["Item"].str.startswith(i_wipe)].to_csv(log_file, index=False)
            st.rerun()

    # HISTORY MANAGEMENT
    st.subheader("📊 Transaction History")
    st.dataframe(log_df.iloc[::-1], use_container_width=True)
    rows_to_del = st.multiselect("Delete specific rows:", options=log_df.index, format_func=lambda x: f"{log_df.loc[x, 'Item']} (${log_df.loc[x, 'Total Cost']:.2f})")
    
    d_col1, d_col2 = st.columns(2)
    if d_col1.button("Delete Selected"):
        log_df.drop(rows_to_del).to_csv(log_file, index=False); st.rerun()
    if d_col2.button("🧨 Wipe All Data", type="primary"):
        if os.path.exists(log_file): os.remove(log_file); st.rerun()
        
elif pwd != "":
    st.error("Incorrect Password")
