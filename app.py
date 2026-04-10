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

# --- CURRENT BALANCE CALCULATION ---
current_balance = float(log_df["Wallet Left"].iloc[-1]) if not log_df.empty else 0.0

st.title("💰 Smart Tracker & Reminders")

# --- AUTOMATIC REMINDER SECTION ---
if not log_df.empty:
    # We only show things where Type is 'Lend'
    unpaid_loans = log_df[log_df["Type"] == "Lend"]
    if not unpaid_loans.empty:
        with st.expander("🔔 PENDING REMINDERS (Money Owed to You)", expanded=True):
            for i, row in unpaid_loans.iterrows():
                col_text, col_btn = st.columns([3, 1])
                col_text.warning(f"👉 **{row['Item']}**: **${row['Total Cost']:.2f}**")
                
                # The Fix is here: Adding money back to the wallet
                if col_btn.button(f"Paid ✅", key=f"pay_{i}"):
                    # 1. Update the old row so it's not a 'Lend' anymore
                    log_df.at[i, 'Type'] = 'Collected' 
                    
                    # 2. Create a new entry to ADD the money back to the wallet
                    new_balance = current_balance + row['Total Cost']
                    repaid_entry = pd.DataFrame([{
                        "Date": datetime.now().strftime("%Y-%m-%d"),
                        "Item": f"REPAYMENT: {row['Item']}",
                        "Quantity": 1,
                        "Total Cost": 0, # It's not a cost, it's an intake
                        "Wallet Left": new_balance,
                        "Type": "TopUp"
                    }])
                    
                    # Save everything
                    final_df = pd.concat([log_df, repaid_entry], ignore_index=True)
                    final_df.to_csv(log_file, index=False)
                    st.rerun()

st.metric("App Balance", f"${current_balance:,.2f}")

tab1, tab2, tab3, tab4 = st.tabs(["🛒 Log Purchase", "💵 Top Up", "🤝 Lend Money", "🪙 Cash Audit"])

# --- TAB 1: PURCHASE ---
with tab1:
    st.subheader("Purchase")
    item_name = st.text_input("What are you buying?")
    unit_price = st.number_input("Price ($)", min_value=0.0, step=0.01)
    qty = st.number_input("Quantity", min_value=1, step=1)
    if st.button("Confirm Purchase", use_container_width=True):
        if item_name:
            new_bal = current_balance - (unit_price * qty)
            new_entry = pd.DataFrame([{"Date": datetime.now().strftime("%Y-%m-%d"), "Item": item_name, "Quantity": qty, "Total Cost": unit_price * qty, "Wallet Left": new_bal, "Type": "Spend"}])
            new_entry.to_csv(log_file, mode='a', header=not os.path.isfile(log_file), index=False)
            st.rerun()

# --- TAB 2: TOP UP ---
with tab2:
    st.subheader("Add Money")
    top_up = st.number_input("Amount ($)", min_value=0.0)
    if st.button("Confirm Top Up", use_container_width=True):
        top_up_entry = pd.DataFrame([{"Date": datetime.now().strftime("%Y-%m-%d"), "Item": "CASH TOP UP", "Quantity": 1, "Total Cost": 0, "Wallet Left": current_balance + top_up, "Type": "TopUp"}])
        top_up_entry.to_csv(log_file, mode='a', header=not os.path.isfile(log_file), index=False)
        st.balloons()
        st.rerun()

# --- TAB 3: LEND ---
with tab3:
    st.subheader("Lend Money")
    friend = st.text_input("Friend's Name")
    l_amount = st.number_input("Amount ($)", min_value=0.0)
    if st.button("Confirm Loan", use_container_width=True):
        if friend:
            new_bal = current_balance - l_amount
            lend_entry = pd.DataFrame([{"Date": datetime.now().strftime("%Y-%m-%d"), "Item": f"LENT TO: {friend}", "Quantity": 1, "Total Cost": l_amount, "Wallet Left": new_bal, "Type": "Lend"}])
            lend_entry.to_csv(log_file, mode='a', header=not os.path.isfile(log_file), index=False)
            st.rerun()

# --- TAB 4: CASH AUDIT ---
with tab4:
    st.subheader("Cash Audit")
    st.info("Count your physical cash to see if it matches the 'App Balance' above.")
    # (Simplified Audit for code space)

# --- HISTORY ---
st.divider()
st.header("📊 History")
st.dataframe(log_df.iloc[::-1], use_container_width=True)
