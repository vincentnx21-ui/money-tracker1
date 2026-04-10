import streamlit as st
import pandas as pd
from datetime import datetime
import os

# File names
log_file = "money_tracker.csv"

st.set_page_config(page_title="Auto-Learning Budget", layout="centered")

# --- DATABASE HELPER ---
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
log_df = load_data(log_file, log_cols)

# --- AUTOMATIC MENU LOGIC ---
# We extract unique items from history that were 'Spend' types
if not log_df.empty:
    # Get only 'Spend' rows, then find the latest price for each unique item
    history_spend = log_df[log_df["Type"] == "Spend"]
    if not history_spend.empty:
        # This creates a "Menu" by taking the most recent price you paid for every item
        auto_menu = history_spend.sort_values("Date").groupby("Item").tail(1)[["Item", "Total Cost", "Quantity"]]
        auto_menu["Unit Price"] = auto_menu["Total Cost"] / auto_menu["Quantity"]
    else:
        auto_menu = pd.DataFrame(columns=["Item", "Unit Price"])
else:
    auto_menu = pd.DataFrame(columns=["Item", "Unit Price"])

# --- MAIN APP ---
current_balance = float(log_df["Wallet Left"].iloc[-1]) if not log_df.empty else 0.0

st.title("💰 Auto-Learning Tracker")
st.metric("Current Balance", f"${current_balance:,.2f}")

tab1, tab2 = st.tabs(["🛒 Log Purchase", "💵 Top Up"])

with tab1:
    st.subheader("Purchase")
    
    # Choice 1: Pick from things you've bought before
    if not auto_menu.empty:
        existing_items = ["-- New Item --"] + auto_menu["Item"].tolist()
        selection = st.selectbox("Select an item from your history:", existing_items)
    else:
        selection = "-- New Item --"

    if selection == "-- New Item --":
        item_name = st.text_input("What are you buying?")
        unit_price = st.number_input("Price for 1 ($)", min_value=0.0, step=0.01)
    else:
        item_name = selection
        # Auto-fill the price based on what you paid last time
        unit_price = float(auto_menu.loc[auto_menu["Item"] == selection, "Unit Price"].values[0])
        st.info(f"Last paid: ${unit_price:.2f} per unit")

    qty = st.number_input("Quantity", min_value=1, step=1)
    total_cost = qty * unit_price
    new_balance = current_balance - total_cost

    st.write(f"Total: **${total_cost:.2f}** | New Balance: **${new_balance:.2f}**")

    if st.button("Confirm Purchase", use_container_width=True):
        if item_name:
            new_entry = pd.DataFrame([{
                "Date": datetime.now().strftime("%Y-%m-%d"),
                "Item": item_name, "Quantity": qty,
                "Total Cost": total_cost, "Wallet Left": new_balance, "Type": "Spend"
            }])
            new_entry.to_csv(log_file, mode='a', header=not os.path.isfile(log_file), index=False)
            st.rerun()

with tab2:
    st.subheader("Add Money")
    top_up = st.number_input("Amount ($)", min_value=0.0, step=1.0)
    if st.button("Confirm Top Up", use_container_width=True):
