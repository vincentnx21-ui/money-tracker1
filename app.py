import streamlit as st
import pandas as pd
from datetime import datetime
import os

# File names
log_file = "money_tracker.csv"
menu_file = "item_menu.csv"

st.set_page_config(page_title="Auto-Budget Tracker", layout="centered")

# --- DATABASE HELPERS ---
def load_data(file, columns):
    if os.path.isfile(file):
        return pd.read_csv(file)
    return pd.DataFrame(columns=columns)

# Load existing data (This is what keeps your history alive)
menu_df = load_data(menu_file, ["Item", "Price"])
log_df = load_data(log_file, ["Date", "Item", "Quantity", "Total Cost", "Wallet Left"])

# --- SIDEBAR: MASTER MENU (Price List) ---
st.sidebar.header("📋 Master Menu")
st.sidebar.write("Items here stay at 1 quantity.")

with st.sidebar.expander("➕ Add/Update Menu Item"):
    m_item = st.text_input("Item Name")
    m_price = st.number_input("Unit Price ($)", min_value=0.0, step=0.01, format="%.2f")
    if st.sidebar.button("Save to Menu"):
        if m_item:
            new_row = pd.DataFrame([{"Item": m_item, "Price": m_price}])
            menu_df = pd.concat([menu_df, new_row]).drop_duplicates(subset=['Item'], keep='last')
            menu_df.to_csv(menu_file, index=False)
            st.rerun()

if not menu_df.empty:
    st.sidebar.write("Your Prices:")
    st.sidebar.dataframe(menu_df, hide_index=True)

# --- MAIN APP: THE LOGGER ---
st.title("💰 Smart Money Tracker")

# Automatically get the last wallet balance from your history
last_balance = float(log_df["Wallet Left"].iloc[-1]) if not log_df.empty else 0.0

if not menu_df.empty:
    with st.container(border=True):
        st.subheader("Log a Purchase")
        selected_item = st.selectbox("Pick Item:", menu_df["Item"].tolist())
        
        # Auto-fetch price
        unit_price = menu_df.loc[menu_df["Item"] == selected_item, "Price"].values[0]
        
        col1, col2 = st.columns(2)
        with col1:
            qty = st.number_input("Quantity", min_value=1, step=1)
        with col2:
            current_wallet = st.number_input("Wallet Balance", value=last_balance)
