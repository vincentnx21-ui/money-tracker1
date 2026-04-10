import streamlit as st
import pandas as pd
from datetime import datetime
import os

# File names
log_file = "money_tracker.csv"
menu_file = "item_menu.csv"

st.set_page_config(page_title="Auto-Budget Tracker", layout="centered")

# --- DATABASE HELPERS (RELIABLE LOAD) ---
def load_data(file, columns):
    if os.path.exists(file):
        try:
            df = pd.read_csv(file)
            # Check if columns match; if not, return empty with correct columns
            if list(df.columns) != columns:
                return pd.DataFrame(columns=columns)
            return df
        except:
            return pd.DataFrame(columns=columns)
    return pd.DataFrame(columns=columns)

# Define column structures
log_cols = ["Date", "Item", "Quantity", "Total Cost", "Wallet Left", "Type"]
menu_cols = ["Item", "Price"]

# Load existing data
menu_df = load_data(menu_file, menu_cols)
log_df = load_data(log_file, log_cols)

# --- SIDEBAR: MASTER MENU ---
st.sidebar.header("📋 Master Menu")
with st.sidebar.expander("➕ Add Item to Price List"):
    m_item = st.sidebar.text_input("Item Name")
    m_price = st.sidebar.number_input("Price ($)", min_value=0.0, step=0.01)
    if st.sidebar.button("Save to Menu"):
        if m_item:
            new_row = pd.DataFrame([{"Item": m_item, "Price": m_price}])
            menu_df = pd.concat([menu_df, new_row]).drop_duplicates(subset=['Item'], keep='last')
            menu_df.to_csv(menu_file, index=False)
            st.rerun()

if not menu_df.empty:
    st.sidebar.dataframe(menu_df, hide_index=True)

# --- CALCULATING CURRENT BALANCE ---
# Logic: If log is empty, balance is 0. Otherwise, take the last 'Wallet Left' value.
if not log_df.empty:
    current_balance = float(log_df["Wallet Left"].iloc[-1])
else:
    current_balance = 0.0

st.title("💰 Smart Money Tracker")
st.metric("Current Wallet Balance", f"${current_balance:,.2f}")

# --- TWO TABS: SPEND VS TOP UP ---
tab1, tab2 = st.tabs(["🛒 Log Purchase", "💵 Top Up Wallet"])

with tab1:
    if not menu_df.empty:
        selected_item = st.selectbox("What did you buy?", menu_df["Item"].tolist())
        unit_price = menu_df.loc[menu_df["Item"] == selected_item, "Price"].values[0]
        
        qty = st.number_input("Quantity", min_value=1, step=1)
        total_cost = qty * unit_price
        
        # Calculation
        new_balance_after_spend = current_balance - total_cost
        
        st.write(f"Total Cost: **${total_cost:.2f}**")
        
        if st.button("Confirm Purchase", use_container_width=True):
            new_entry = pd.DataFrame([{
                "Date": datetime.now().strftime("%Y-%m-%d"),
                "Item": selected_item,
                "Quantity": qty,
                "Total Cost": total_cost,
                "Wallet Left": new_balance_after_spend,
                "Type": "Spend"
            }])
            new_entry.to_csv(log_file, mode='a', header=not os.path.isfile(log_file), index=False)
            st.rerun()
    else:
        st.info("👈 Add items to your menu in the sidebar first.")

with tab2:
    st.subheader("Add Money to Wallet")
    top_up_amount = st.number_input("Amount to add ($)", min_value=0.0, step=1.0)
    
    # Define the calculation here so it's always ready
    calculated_topup = current_balance + top_up_amount
    
    if st.button("Confirm Top Up", use_container_width=True):
        topup_entry = pd.DataFrame([{
            "Date": datetime.now().strftime("%Y-%m-%d"),
            "Item": "CASH TOP UP",
            "Quantity": 1,
            "Total Cost": 0,
            "Wallet Left": calculated_topup,
            "Type": "TopUp"
        }])
        topup_entry.to_csv(log_file, mode='a', header=not os.path.isfile(log_file), index=False)
        st.balloons()
        st.rerun()

# --- HISTORY SECTION ---
st.divider()
st.header("📊 History")
if not log_df.empty:
    st.dataframe(log_df.iloc[::-1], use_container_width=True)
    
    # Download Button for the Spreadsheet
    csv_data = log_df.to_csv(index=False).encode('utf-8')
    st.download_button("📥 Download Spreadsheet", data=csv_data, file_name="spending_log.csv", mime="text/csv")
    
    if st.button("🗑️ Reset Everything"):
        if os.path.exists(log_file): os.remove(log_file)
        if os.path.exists(menu_file): os.remove(menu_file)
        st.rerun()
