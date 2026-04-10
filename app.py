import streamlit as st
import pandas as pd
from datetime import datetime
import os

# File names
log_file = "money_tracker.csv"

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

# --- REMINDERS ---
if not log_df.empty:
    unpaid = log_df[log_df["Type"] == "Lend"]
    if not unpaid.empty:
        with st.expander("🔔 PENDING REMINDERS", expanded=True):
            for i, row in unpaid.iterrows():
                c1, c2 = st.columns([3, 1])
                c1.warning(f"**{row['Item']}**: ${row['Total Cost']:.2f}")
                if c2.button("Paid ✅", key=f"re_{i}"):
                    log_df.at[i, 'Type'] = 'Collected'
                    new_bal = current_balance + row['Total Cost']
                    repaid = pd.DataFrame([{"Date": datetime.now().strftime("%Y-%m-%d"), "Item": f"REPAYMENT: {row['Item']}", "Shop": "N/A", "Quantity": 1, "Total Cost": 0, "Wallet Left": new_bal, "Type": "TopUp"}])
                    pd.concat([log_df, repaid], ignore_index=True).to_csv(log_file, index=False)
                    st.rerun()

st.metric("App Balance", f"${current_balance:,.2f}")

tab1, tab2, tab3, tab4 = st.tabs(["🛒 Purchase", "💵 Top Up", "🤝 Lend", "🪙 Audit"])

# --- TAB 1: PURCHASE ---
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
    
    suggested_price = 0.0
    if selection != "-- New Item --":
        exact_match = log_df[(log_df["Shop"] == shop_name) & (log_df["Item"] == selection)]
        if not exact_match.empty:
            suggested_price = float(exact_match.iloc[-1]["Total Cost"] / exact_match.iloc[-1]["Quantity"])
        else:
            fuzzy_match = log_df[(log_df["Shop"] == shop_name) & (log_df["Item"].str.startswith(selection))]
            if not fuzzy_match.empty:
                suggested_price = float(fuzzy_match.iloc[-1]["Total Cost"] / fuzzy_match.iloc[-1]["Quantity"])

    i_name = st.text_input("Item Name", value="" if selection == "-- New Item --" else selection)
    base_price = st.number_input("Base Price ($)", min_value=0.0, step=0.05, value=suggested_price)

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
            full_save_name = i_name + (" +" + " +".join(ex_names) if ex_names else "")
            new_row = pd.DataFrame([{"Date": datetime.now().strftime("%Y-%m-%d"), "Item": full_save_name, "Shop": shop_name, "Quantity": qty, "Total Cost": final_total, "Wallet Left": current_balance - final_total, "Type": "Spend"}])
            new_row.to_csv(log_file, mode='a', header=not os.path.isfile(log_file), index=False)
            st.session_state.addons_list = []
            st.rerun()

# --- TAB 2, 3, 4 ---
with tab2:
    top = st.number_input("Amount", min_value=0.0, key="top_up")
    if st.button("Top Up"):
        nr = pd.DataFrame([{"Date": datetime.now().strftime("%Y-%m-%d"), "Item": "TOP UP", "Shop": "N/A", "Quantity": 1, "Total Cost": 0, "Wallet Left": current_balance + top, "Type": "TopUp"}])
        nr.to_csv(log_file, mode='a', index=False); st.rerun()

with tab3:
    fr = st.text_input("Friend", key="lend_fr")
    am = st.number_input("Amt", min_value=0.0, key="lend_am")
    if st.button("Lend"):
        nr = pd.DataFrame([{"Date": datetime.now().strftime("%Y-%m-%d"), "Item": f"LENT TO: {fr}", "Shop": "N/A", "Quantity": 1, "Total Cost": am, "Wallet Left": current_balance - am, "Type": "Lend"}])
        nr.to_csv(log_file, mode='a', index=False); st.rerun()

with tab4:
    st.subheader("Cash Audit")
    # Audit math...

# --- HISTORY & MENU MANAGEMENT ---
st.divider()
st.header("⚙️ Settings & Data")

if not log_df.empty:
    # 1. DELETE FROM MENU (New Feature)
    with st.expander("📝 Manage Shop & Item Menus", expanded=False):
        st.write("Deleting from here removes the item/shop from your dropdown menus by deleting its history.")
        
        m_col1, m_col2 = st.columns(2)
        with m_col1:
            shop_to_wipe = st.selectbox("Wipe Shop from Menu", ["-- Select --"] + all_shops)
            if st.button("Delete Shop Menu"):
                log_df = log_df[log_df["Shop"] != shop_to_wipe]
                log_df.to_csv(log_file, index=False)
                st.rerun()
        
        with m_col2:
            item_to_wipe = st.selectbox("Wipe Item from Menu", ["-- Select --"] + clean_items)
            if st.button("Delete Item Menu"):
                # Remove any item that starts with this name (to include variations with extras)
                log_df = log_df[~log_df["Item"].str.startswith(item_to_wipe)]
                log_df.to_csv(log_file, index=False)
                st.rerun()

    # 2. DELETE FROM HISTORY (Existing Feature)
    with st.expander("📊 Transaction History", expanded=True):
        st.dataframe(log_df.iloc[::-1], use_container_width=True)
        rows_to_del = st.multiselect("Select rows to delete:", options=log_df.index, format_func=lambda x: f"{log_df.loc[x, 'Item']} (${log_df.loc[x, 'Total Cost']:.2f})")
        
        c1, c2 = st.columns(2)
        if c1.button("Delete Selected Transactions"):
            log_df.drop(rows_to_del).to_csv(log_file, index=False)
            st.rerun()
        if c2.button("🧨 Wipe All Data", type="primary"):
            if os.path.exists(log_file): os.remove(log_file)
            st.rerun()
