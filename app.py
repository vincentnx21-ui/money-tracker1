import streamlit as st
import pandas as pd
from datetime import datetime
import os

# File names
log_file = "money_tracker.csv"

st.set_page_config(page_title="Smart Tracker & Reminders", layout="centered")

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

# --- MAIN APP ---
current_balance = float(log_df["Wallet Left"].iloc[-1]) if not log_df.empty else 0.0

st.title("💰 Smart Tracker & Reminders")

# --- NEW: AUTOMATIC REMINDER SECTION ---
# This looks through your history for any "Lend" transactions
if not log_df.empty:
    unpaid_loans = log_df[log_df["Type"] == "Lend"]
    if not unpaid_loans.empty:
        with st.expander("🔔 PENDING REMINDERS (Money Owed to You)", expanded=True):
            for i, row in unpaid_loans.iterrows():
                st.warning(f"👉 **{row['Item']}**: Collect **${row['Total Cost']:.2f}** (Lent on {row['Date']})")
                if st.button(f"Mark as Paid (Row {i})"):
                    # Logic to convert 'Lend' to 'Repaid' so it disappears from reminders
                    log_df.at[i, 'Type'] = 'Repaid'
                    log_df.to_csv(log_file, index=False)
                    st.rerun()

st.metric("App Balance", f"${current_balance:,.2f}")

tab1, tab2, tab3, tab4 = st.tabs(["🛒 Log Purchase", "💵 Top Up", "🤝 Lend Money", "🪙 Cash Audit"])

with tab1:
    # ... (Purchase logic remains the same)
    st.subheader("Purchase")
    item_name = st.text_input("What are you buying?", key="buy_input")
    unit_price = st.number_input("Price ($)", min_value=0.0, step=0.01, key="buy_price")
    qty = st.number_input("Quantity", min_value=1, step=1, key="buy_qty")
    if st.button("Confirm Purchase"):
        new_balance = current_balance - (unit_price * qty)
        new_entry = pd.DataFrame([{"Date": datetime.now().strftime("%Y-%m-%d"), "Item": item_name, "Quantity": qty, "Total Cost": unit_price * qty, "Wallet Left": new_balance, "Type": "Spend"}])
        new_entry.to_csv(log_file, mode='a', header=not os.path.isfile(log_file), index=False)
        st.rerun()

with tab2:
    # ... (Top Up logic)
    st.subheader("Add Money")
    top_up = st.number_input("Amount ($)", min_value=0.0)
    if st.button("Confirm Top Up"):
        topup_entry = pd.DataFrame([{"Date": datetime.now().strftime("%Y-%m-%d"), "Item": "TOP UP", "Quantity": 1, "Total Cost": 0, "Wallet Left": current_balance + top_up, "Type": "TopUp"}])
        topup_entry.to_csv(log_file, mode='a', header=not os.path.isfile(log_file), index=False)
        st.rerun()

with tab3:
    st.subheader("Lend Money")
    friend = st.text_input("Who borrowed the money?")
    l_amount = st.number_input("Amount to lend ($)", min_value=0.0)
    if st.button("Confirm Loan & Create Reminder"):
        if friend:
            new_balance_lend = current_balance - l_amount
            lend_entry = pd.DataFrame([{
                "Date": datetime.now().strftime("%Y-%m-%d"),
                "Item": f"LENT
