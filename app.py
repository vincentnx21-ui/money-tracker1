import streamlit as st
import pandas as pd
from datetime import datetime
import os
import re

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

# --- APP METRIC ---
st.metric("App Balance", f"${current_balance:,.2f}")

tab1, tab2, tab3, tab4 = st.tabs(["🛒 Purchase", "💵 Top Up", "🤝 Lend", "🪙 Audit"])

# --- TAB 1: PURCHASE (THE REAL PRICE FIX) ---
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
    
    # --- SMART BASE PRICE CALCULATION ---
    suggested_base_price = 0.0
    if selection != "-- New Item --":
        # Look for the last time you bought this (including variations)
        last_match = log_df[(log_df["Shop"] == shop_name) & (log_df["Item"].str.startswith(selection))].iloc[-1]
        
        full_price = last_match["Total Cost"] / last_match["Quantity"]
        full_name = last_match["Item"]
        
        # If the name has extras (e.g., "Chicken Rice +Egg +Meat"), we need to subtract them
        # This regex looks for patterns like '+Name' or '+Price'
        if " +" in full_name:
            st.info(f"Last total was ${full_price:.2f}, but I detected extras. Calculating base...")
            # For now, let's allow the user to manually set it once to "reset" the memory
            suggested_base_price = full_price 
        else:
            suggested_base_price = full_price

    i_name = st.text_input("Item Name", value="" if selection == "-- New Item --" else selection)
    
    # We use a unique key here to prevent the session from "holding" onto old numbers
    base_price = st.number_input("Base Price ($)", min_value=0.0, step=0.05, value=float(suggested_base_price), key=f"price_{selection}")

    st.divider()
    st.write("**Add Extras (One at a time):**")
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

    st.divider()
    qty = st.number_input("Quantity", min_value=1, step=1)
    final_total = (base_price + total_ex) * qty
    st.write(f"### Grand Total: **${final_total:.2f}**")

    if st.button("Confirm Final Order", use_container_width=True, type="primary"):
        if i_name and shop_name:
            full_save_name = i_name + (" +" + " +".join(ex_names) if ex_names else "")
            new_row = pd.DataFrame([{"Date": datetime.now().strftime("%Y-%m-%d"), "Item": full_save_name, "Shop": shop_name, "Quantity": qty, "Total Cost": final_total, "Wallet Left": current_balance - final_total, "Type": "Spend"}])
            new_row.to_csv(log_file, mode='a', header=not os.path.isfile(log_file), index=False)
            st.session_state.addons_list = []
            st.rerun()

# --- THE ALWAYS VISIBLE MANAGE SECTION ---
st.divider()
st.header("⚙️ Manage Data & Menus")

if not log_df.empty:
    st.subheader("🧹 Clean Up Menus")
    m_col1, m_col2 = st.columns(2)
    with m_col1:
        shop_to_wipe = st.selectbox("Forget Shop", ["-- Select --"] + all_shops)
        if st.button("Delete Shop from Menu"):
            log_df = log_df[log_df["Shop"] != shop_to_wipe].to_csv(log_file, index=False)
            st.rerun()
    with m_col2:
        item_to_wipe = st.selectbox("Forget Item", ["-- Select --"] + clean_items)
        if st.button("Delete Item from Menu"):
            # This deletes ALL history of that item so the app "forgets" the wrong price
            log_df = log_df[~log_df["Item"].str.startswith(item_to_wipe)]
            log_df.to_csv(log_file, index=False)
            st.rerun()

    st.subheader("📊 Transaction History")
    st.dataframe(log_df.iloc[::-1], use_container_width=True)
    
    rows_to_del = st.multiselect("Select transactions to remove:", options=log_df.index, format_func=lambda x: f"{log_df.loc[x, 'Item']} (${log_df.loc[x, 'Total Cost']:.2f})")
    if st.button("Delete Selected Transactions"):
        log_df.drop(rows_to_del).to_csv(log_file, index=False)
        st.rerun()
