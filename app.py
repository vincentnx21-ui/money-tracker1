import streamlit as st
import pandas as pd
from datetime import datetime
import os

# File names
log_file = "money_tracker.csv"

st.set_page_config(page_title="Smart Tracker", layout="centered")

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
current_balance = float(log_df["Wallet Left"].iloc[-1]) if not log_df.empty else 0.0

st.title("💰 Smart Money Tracker")

# --- REMINDERS ---
if not log_df.empty:
    unpaid = log_df[log_df["Type"] == "Lend"]
    if not unpaid.empty:
        with st.expander("🔔 PENDING REMINDERS", expanded=True):
            for i, row in unpaid.iterrows():
                c1, c2 = st.columns([3, 1])
                c1.warning(f"**{row['Item']}**: ${row['Total Cost']:.2f}")
                if c2.button("Paid ✅", key=f"re_{i}"):
                    log_df.at[i, 'Type'] = 'Collected'
                    new_bal = current_balance + row['Total Cost']
                    repaid = pd.DataFrame([{"Date": datetime.now().strftime("%Y-%m-%d"), "Item": f"REPAYMENT: {row['Item']}", "Quantity": 1, "Total Cost": 0, "Wallet Left": new_bal, "Type": "TopUp"}])
                    pd.concat([log_df, repaid], ignore_index=True).to_csv(log_file, index=False)
                    st.rerun()

st.metric("App Balance", f"${current_balance:,.2f}")

tab1, tab2, tab3, tab4 = st.tabs(["🛒 Purchase", "💵 Top Up", "🤝 Lend", "🪙 Audit"])

# --- TAB 1: SMART PURCHASE ---
with tab1:
    st.subheader("Order Food / Items")
    items_hist = log_df[log_df["Type"]=="Spend"]["Item"].unique().tolist() if not log_df.empty else []
    selection = st.selectbox("What are you buying?", ["-- New Item --"] + items_hist)
    
    if selection == "-- New Item --":
        i_name = st.text_input("Item Name (e.g. Chicken Rice)")
        base_price = st.number_input("Base Price ($)", min_value=0.0, step=0.10)
    else:
        i_name = selection
        # Get last known price
        last_row = log_df[log_df["Item"]==selection].iloc[-1]
        base_price = last_row["Total Cost"] / last_row["Quantity"]
        st.info(f"Standard Price: ${base_price:.2f}")

    # NEW: Add-on Logic
    with st.expander("➕ Add Extras (Egg, Extra Meat, etc.)"):
        extra_note = st.text_input("What extras? (e.g. +Egg +Tofu)")
        extra_cost = st.number_input("Extra Cost ($)", min_value=0.0, step=0.10)

    qty = st.number_input("Quantity", min_value=1, step=1)
    
    # Calculation
    final_unit_price = base_price + extra_cost
    total_bill = final_unit_price * qty
    
    st.write(f"### Total: **${total_bill:.2f}**")
    
    if st.button("Confirm Order", use_container_width=True):
        if i_name:
            display_name = f"{i_name} ({extra_note})" if extra_note else i_name
            new_bal = current_balance - total_bill
            new_row = pd.DataFrame([{"Date": datetime.now().strftime("%Y-%m-%d"), "Item": display_name, "Quantity": qty, "Total Cost": total_bill, "Wallet Left": new_bal, "Type": "Spend"}])
            new_row.to_csv(log_file, mode='a', header=not os.path.isfile(log_file), index=False)
            st.rerun()

# --- OTHER TABS (Same logic as before) ---
with tab2:
    top = st.number_input("Add cash ($)", min_value=0.0)
    if st.button("Top Up Wallet"):
        new_row = pd.DataFrame([{"Date": datetime.now().strftime("%Y-%m-%d"), "Item": "TOP UP", "Quantity": 1, "Total Cost": 0, "Wallet Left": current_balance + top, "Type": "TopUp"}])
        new_row.to_csv(log_file, mode='a', header=not os.path.isfile(log_file), index=False)
        st.rerun()

with tab3:
    fr = st.text_input("Friend's name")
    amt = st.number_input("Amount to lend", min_value=0.0)
    if st.button("Confirm Loan"):
        new_row = pd.DataFrame([{"Date": datetime.now().strftime("%Y-%m-%d"), "Item": f"LENT TO: {fr}", "Quantity": 1, "Total Cost": amt, "Wallet Left": current_balance - amt, "Type": "Lend"}])
        new_row.to_csv(log_file, mode='a', header=not os.path.isfile(log_file), index=False)
        st.rerun()

with tab4:
    st.write("Count your physical cash here.")
    # (Simplified Audit placeholder)

# --- HISTORY ---
st.divider()
st.header("📊 History")
if not log_df.empty:
    st.dataframe(log_df.iloc[::-1], use_container_width=True)
    if st.button("🧨 Wipe All Data"):
        if os.path.exists(log_file): os.remove(log_file)
        st.rerun()
