import streamlit as st
import pandas as pd
from datetime import datetime
import os

# Configuration
file_name = "money_tracker.csv"

st.set_page_config(page_title="Money Tracker", layout="centered")
st.title("💰 Personal Expense Tracker")

# --- INPUT SECTION ---
with st.form("entry_form", clear_on_submit=True):
    date = st.date_input("Date", datetime.now())
    item = st.text_input("What did you buy?")
    qty = st.number_input("Quantity", min_value=1, step=1)
    price = st.number_input("Price per unit", min_value=0.0, format="%.2f")
    wallet = st.number_input("Starting Money (Wallet)", min_value=0.0)
    
    submit = st.form_submit_button("Log Expense")

if submit:
    total_cost = qty * price
    remaining = wallet - total_cost
    
    new_data = pd.DataFrame([{
        "Date": date.strftime("%Y-%m-%d"),
        "Item": item,
        "Quantity": qty,
        "Total Cost": total_cost,
        "Wallet Left": remaining
    }])

    if not os.path.isfile(file_name):
        new_data.to_csv(file_name, index=False)
    else:
        new_data.to_csv(file_name, mode='a', header=False, index=False)
    
    st.success(f"Logged! Total: {total_cost}. Left: {remaining}")

# --- CHECKING SECTION ---
st.divider()
st.header("🔍 Money Check")
if os.path.isfile(file_name):
    df = pd.read_csv(file_name)
    st.dataframe(df, use_container_width=True)
    
    total_spent = df['Total Cost'].sum()
    st.metric("Total Spent Overall", f"${total_spent:,.2f}")
else:
    st.info("No expenses logged yet. Start typing above!")
