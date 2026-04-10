import streamlit as st
import pandas as pd
from datetime import datetime
import os

# File names
log_file = "money_tracker.csv"
menu_file = "item_menu.csv"

st.set_page_config(page_title="Auto-Money Tracker", layout="centered")

# --- DATABASE LOAD ---
def load_data(file, columns):
    if os.path.isfile(file):
        return pd.read_csv(file)
    return pd.DataFrame(columns=columns)

menu_df = load_data(menu_file, ["Item", "Price"])
log_df = load_data(log_file, ["Date", "Item", "Quantity", "Total Cost", "Wallet Left"])

# --- SIDEBAR: MENU MANAGEMENT ---
st.sidebar.header("📋 Master Menu")
with st.sidebar.expander("Add/Update Item"):
    m_item = st.text_input("Item Name")
    m_price = st.number_input("Unit Price", min_value=0.0, step=0.50)
    if st.sidebar.button("Save to Menu"):
        new_row = pd.DataFrame([{"Item": m_item, "Price": m_price}])
        menu_df = pd.concat([menu_df, new_row]).drop_duplicates(subset=['Item'], keep='last')
        menu_df.to_csv(menu_file, index=False)
        st.rerun()

# --- MAIN APP ---
st.title("💰 Smart Expense Tracker")

# 1. Automatic Wallet Balance Check
# Finds the last recorded 'Wallet Left' value so you don't have to type it
last_balance = log_df["Wallet Left"].iloc[-1] if not log_df.empty else 0.0

with st.container(border=True):
    st.subheader("Log Purchase")
    
    # Selection from Menu
    if not menu_df.empty:
        # The 'selectbox' is the trigger for the automatic update
        selected_item = st.selectbox("What did you buy?", menu_df["Item"].tolist())
        
        # AUTOMATIC PRICE FETCH
        unit_price = menu_df.loc[menu_df["Item"] == selected_item, "Price"].values[0]
        
        col1, col2
