import streamlit as st
import pandas as pd
from datetime import datetime
import os

# File names
log_file = "money_tracker.csv"
menu_file = "item_menu.csv"

st.set_page_config(page_title="Smart Money Tracker", layout="centered")

# --- 1. THE MENU (Price List) LOGIC ---
# This part ensures the menu only shows each item once with its base price
if not os.path.isfile(menu_file):
    menu_df = pd.DataFrame(columns=["Item", "Price"])
    menu_df.to_csv(menu_file, index=False)
else:
    menu_df = pd.read_csv(menu_file)

# --- SIDEBAR: Manage Your Master Price List ---
st.sidebar.header("📋 Master Price List")
st.sidebar.write("Add items here once. They will stay at 1 quantity for easy picking later.")

with st.sidebar.expander("Add/Update Menu Item"):
    new_menu_item = st.text_input("Item Name (e.g., Soda)")
    new_menu_price = st.number_input("Price for 1 unit ($)", min_value=0.0, format="%.2f")
    if st.button("Save to Menu"):
        if new_menu_item:
            # This logic replaces the item if it already exists, keeping the list clean
            new_row = pd.DataFrame([{"Item": new_menu_item, "Price": new_menu_price}])
            menu_df = pd.concat([menu_df, new_row]).drop_duplicates(subset=['Item'], keep='last')
            menu_df.to_csv(menu_file, index=False)
            st.success(f"Saved {new_menu_item} at ${new_menu_price}")
            st.rerun()

if not menu_df.empty:
    st.sidebar.write("Current Menu (Price for 1):")
    st.sidebar.dataframe(menu_df, hide_index=True)
    if st.sidebar.button("🗑️ Clear Entire Menu"):
        os.remove(menu_file)
        st.rerun()

# --- 2. MAIN APP: LOGGING DAILY PURCHASES ---
st.title("💰 Expense Tracker")

with st.form("entry_form", clear_on_submit=True):
    st.subheader("Log a Purchase")
    date = st.date_input("Date", datetime.now())
    
    # Selection from the Menu (which only shows 1 of each item)
    if not menu_df.empty:
        item_choice = st.selectbox("Select Item:", menu_df["Item"].tolist())
        # Lookup the saved price for 1 unit
        unit_price = menu_df.loc[menu_df["Item"] == item_choice, "Price"].values[0]
        st.write(f"Standard Price: **${unit_price:.2f} each**")
    else:
        st.warning("Your menu is empty! Add items in the sidebar first.")
        item_choice = "None"
        unit_price = 0.0

    # User inputs how many they bought today
    qty = st.number_input("How many did you buy today?", min_value=1, step=1)
    wallet = st.number_input("Total Money in Wallet currently", min_value=0.0)
    
    submit = st.form_submit_button("Log Expense")

if submit and item_choice != "None":
    total_cost = qty * unit_price
    remaining = wallet - total_cost
    
    new_log = pd.DataFrame([{
        "Date": date.strftime("%Y-%m-%d"),
        "Item": item_choice,
        "Quantity": qty,
        "Total Cost": total_cost,
        "Wallet Left": remaining
    }])

    # Save to the Daily Log spreadsheet
    if not os.path.isfile(log_file):
        new_log.to_csv(log_file, index=False)
    else:
        new_log.to_csv(log_file, mode='a', header=False, index=False)
    st.success(f"Logged {qty}x {item_choice} (Total: ${total_cost:.2f})")

# --- 3. THE SPREADSHEET (Checking) ---
st.divider()
st.header("🔍 Daily Spreadsheet & Checking")

if os.path.isfile(log_file):
    df_history = pd.read_csv(log_file)
    st.write("This shows everything you bought, the quantity, and your wallet balance:")
    st.dataframe(df_history, use_container_width=True)
    
    # The Math Check
    total_spent_today = df_history['Total Cost'].sum()
    st.metric("Total Money Spent", f"${total_spent_today:,.2f}")

    if st.button("🗑️ Clear Purchase History"):
        os.remove(log_file)
        st.rerun()
else:
    st.info("No purchases recorded yet.")
