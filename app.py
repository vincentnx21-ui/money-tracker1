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
    if os.path.exists(file):
        try:
            df = pd.read_csv(file)
            if list(df.columns) != columns:
                return pd.DataFrame(columns=columns)
            return df
        except:
            return pd.DataFrame(columns=columns)
    return pd.DataFrame(columns=columns)

log_cols = ["Date", "Item", "Quantity", "Total Cost", "Wallet Left", "Type"]
menu_cols = ["Item", "Price"]

menu_df = load_data(menu_file, menu_cols)
log_df = load_data(log_file, log_cols)

# --- SIDEBAR: MASTER MENU MANAGEMENT ---
st.sidebar.header("📋 Master Menu")

# Add Section
with st.sidebar.expander("➕ Add Item to Price List"):
    m_item = st.text_input("Item Name")
    m_price = st.number_input("Price ($)", min_value=0.0, step=0.01)
    if st.button("Save to Menu"):
        if m_item:
            new_row = pd.DataFrame([{"Item": m_item, "Price": m_price}])
            menu_df = pd.concat([menu_df, new_row]).drop_duplicates(subset=['Item'], keep='last')
            menu_df.to_csv(menu_file, index=False)
            st.rerun()

# Delete Section (NEW FEATURE)
if not menu_df.empty:
    st.sidebar.divider()
    with st.sidebar.expander("🗑️ Delete from Menu"):
        items_to_del = st.multiselect("Select items to remove:", options=menu_df["Item"].tolist())
        if st.button("Delete Selected Items"):
            menu_df = menu_df[~menu_df["
