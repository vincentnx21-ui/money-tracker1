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

# Load data
menu_df = load_data(menu_file, ["Item", "Price"])
log_df = load_data(log_file, ["Date", "Item", "Quantity", "Total Cost", "Wallet Left", "Type"])

# --- SIDEBAR: MASTER MENU ---
st.sidebar.header("📋 Master Menu")
with st.sidebar.expander("➕ Add/Update Menu Item"):
    m_item = st.text_input("Item Name")
    m_price = st.number_input("Unit Price ($)", min_value=0.0, step=0.01)
    if st.sidebar.button("Save to Menu"):
        if m_item:
            new_row = pd.DataFrame([{"Item": m_item, "Price": m_price}])
            menu_df = pd.concat([menu_df, new_row]).drop_duplicates(subset=['Item'], keep='last')
            menu_df.to_csv(menu_file, index=False)
            st.rerun()

if not menu_df.empty:
    st.sidebar.dataframe(menu_df, hide_index=True)

# --- CALCULATING CURRENT BALANCE ---
# It finds the very last 'Wallet Left' value recorded in your history
current_balance = float(log_df["Wallet Left"].iloc[-1]) if not log_df.empty else 0.0

st.title("💰 Smart Money Tracker")

# Display current money prominently at the top
st.metric("Current Wallet Balance", f"${current_balance:,.2f}")

# --- TWO TABS: SPEND VS TOP UP ---
tab1, tab2 = st.tabs(["🛒 Log Purchase", "💵 Top Up Wallet"])

with tab1:
    if not menu_df.empty:
        selected_item = st.selectbox("What did you buy?", menu_df["Item"].tolist())
        unit_price = menu_df.loc[menu_df["Item"] == selected_item, "Price"].values[0]
        
        qty = st.number_input("Quantity", min_value=1, step=1)
        total_cost = qty * unit_price
        new_balance_after_spend = current_balance - total_cost
        
        st.write(f"Total: **${total_cost:.2f}** | Remaining: **${new_balance_after_spend:.2f}**")
        
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
            st.success("Logged!")
            st.rerun()
    else:
        st.info("Add items to your menu in the sidebar to start spending.")

with tab2:
    st.subheader("Add Money to Wallet")
    top_up_amount = st.number_input("Amount to add ($)", min_value=0.0, step=1.0)
    new_balance_after_topup
