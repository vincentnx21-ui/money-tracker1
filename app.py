import streamlit as st
import pandas as pd
from datetime import datetime
import os

# File names
log_file = "money_tracker.csv"

st.set_page_config(page_title="Auto-Budget Tracker", layout="centered")

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
if not log_df.empty:
    history_spend = log_df[log_df["Type"] == "Spend"]
    if not history_spend.empty:
        auto_menu = history_spend.sort_values("Date").groupby("Item").tail(1)[["Item", "Total Cost", "Quantity"]]
        auto_menu["Unit Price"] = auto_menu["Total Cost"] / auto_menu["Quantity"]
    else:
        auto_menu = pd.DataFrame(columns=["Item", "Unit Price"])
else:
    auto_menu = pd.DataFrame(columns=["Item", "Unit Price"])

# --- MAIN APP ---
current_balance = float(log_df["Wallet Left"].iloc[-1]) if not log_df.empty else 0.0

st.title("💰 Smart Money Tracker")
st.metric("App Balance", f"${current_balance:,.2f}")

# Added "🤝 Lend Money" tab
tab1, tab2, tab3, tab4 = st.tabs(["🛒 Log Purchase", "💵 Top Up", "🤝 Lend Money", "🪙 Cash Audit"])

with tab1:
    st.subheader("Purchase")
    if not auto_menu.empty:
        existing_items = ["-- New Item --"] + auto_menu["Item"].tolist()
        selection = st.selectbox("Select an item:", existing_items)
    else:
        selection = "-- New Item --"

    if selection == "-- New Item --":
        item_name = st.text_input("What are you buying?")
        unit_price = st.number_input("Price for 1 ($)", min_value=0.0, step=0.01)
    else:
        item_name = selection
        unit_price = float(auto_menu.loc[auto_menu["Item"] == selection, "Unit Price"].values[0])
        st.info(f"Last paid: ${unit_price:.2f}")

    qty = st.number_input("Quantity", min_value=1, step=1)
    total_cost = qty * unit_price
    new_balance_spend = current_balance - total_cost

    if st.button("Confirm Purchase", use_container_width=True):
        if item_name:
            new_entry = pd.DataFrame([{
                "Date": datetime.now().strftime("%Y-%m-%d"),
                "Item": item_name, "Quantity": qty,
                "Total Cost": total_cost, "Wallet Left": new_balance_spend, "Type": "Spend"
            }])
            new_entry.to_csv(log_file, mode='a', header=not os.path.isfile(log_file), index=False)
            st.rerun()

with tab2:
    st.subheader("Add Money")
    top_up_amount = st.number_input("Amount to add ($)", min_value=0.0, step=1.0)
    if st.button("Confirm Top Up", use_container_width=True):
        topup_entry = pd.DataFrame([{
            "Date": datetime.now().strftime("%Y-%m-%d"),
            "Item": "CASH TOP UP", "Quantity": 1,
            "Total Cost": 0, "Wallet Left": current_balance + top_up_amount, "Type": "TopUp"
        }])
        topup_entry.to_csv(log_file, mode='a', header=not os.path.isfile(log_file), index=False)
        st.balloons()
        st.rerun()

with tab3:
