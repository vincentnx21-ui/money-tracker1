import streamlit as st
import pandas as pd
from datetime import datetime
import os

# File names
log_file = "money_tracker.csv"
menu_file = "item_menu.csv"

st.set_page_config(page_title="Auto-Budget", layout="centered")

# --- DATABASE HELPERS ---
def load_data(file, columns):
    if os.path.isfile(file):
        return pd.read_csv(file)
    return pd.DataFrame(columns=columns)

# Load existing data
menu_df = load_data(menu_file, ["Item", "Price"])
log_df = load_data(log_file, ["Date", "Item", "Quantity", "Total Cost", "Wallet Left"])

# --- SIDEBAR: YOUR PRICE LIST ---
st.sidebar.header("📋 Master Menu")
st.sidebar.info("Add items here once. They will always show 1 quantity in this list.")

with st.sidebar.expander("➕ Add New Item to Menu"):
    m_item = st.text_input("Item Name")
    m_price = st.number_input("Unit Price ($)", min_value=0.0, step=0.01, format="%.2f")
    if st.sidebar.button("Save to Menu"):
        if m_item:
            new_row = pd.DataFrame([{"Item": m_item, "Price": m_price}])
            menu_df = pd.concat([menu_df, new_row]).drop_duplicates(subset=['Item'], keep='last')
            menu_df.to_csv(menu_file, index=False)
            st.rerun()

if not menu_df.empty:
    st.sidebar.write("Current Menu (Prices for 1):")
    st.sidebar.dataframe(menu_df, hide_index=True, use_container_width=True)
    if st.sidebar.button("🗑️ Wipe Menu Clean"):
        os.remove(menu_file)
        st.rerun()

# --- MAIN APP: THE AUTOMATIC LOGGER ---
st.title("💰 Smart Money Tracker")

# 1. Automatic Balance Detection
# Looks
