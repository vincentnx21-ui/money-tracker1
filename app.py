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
    wallet = st.number_input("Current Wallet Money", min_value=0.0)
    
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
    st.success(f"Logged {item}!")

# --- CHECKING & DELETING SECTION ---
st.divider()
st.header("🔍 Money Check")

if os.path.isfile(file_name):
    df = pd.read_csv(file_name)
    
    # Display the table with Index visible so you know which row to delete
    st.dataframe(df, use_container_width=True)
    
    total_spent = df['Total Cost'].sum()
    st.metric("Total Spent Overall", f"${total_spent:,.2f}")

    st.subheader("🗑️ Remove Data")
    col1, col2 = st.columns(2)

    with col1:
        # Option 1: Select specific rows to remove
        to_delete = st.multiselect("Select Item(s) to remove:", options=df.index, format_func=lambda x: f"Row {x}: {df.iloc[x]['Item']}")
        if st.button("Delete Selected"):
            df = df.drop(to_delete)
            df.to_csv(file_name, index=False)
            st.warning("Selected items removed.")
            st.rerun()

    with col2:
        # Option 2: Clear everything
        if st.button("Clear All History"):
            os.remove(file_name)
            st.error("All data deleted.")
            st.rerun()
