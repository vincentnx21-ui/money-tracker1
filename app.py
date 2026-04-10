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

# --- CURRENT BALANCE ---
current_balance = float(log_df["Wallet Left"].iloc[-1]) if not log_df.empty else 0.0

st.title("💰 Smart Tracker & Reminders")

# --- REMINDER SECTION ---
if not log_df.empty:
    unpaid_loans = log_df[log_df["Type"] == "Lend"]
    if not unpaid_loans.empty:
        with st.expander("🔔 PENDING REMINDERS", expanded=True):
            for i, row in unpaid_loans.iterrows():
                c_t, c_b = st.columns([3, 1])
                c_t.warning(f"**{row['Item']}**: **${row['Total Cost']:.2f}**")
                if c_b.button(f"Paid ✅", key=f"rem_{i}"):
                    log_df.at[i, 'Type'] = 'Collected' 
                    new_bal = current_balance + row['Total Cost']
                    repaid_entry = pd.DataFrame([{"Date": datetime.now().strftime("%Y-%m-%d"), "Item": f"REPAYMENT: {row['Item']}", "Quantity": 1, "Total Cost": 0, "Wallet Left": new_bal, "Type": "TopUp"}])
                    pd.concat([log_df, repaid_entry], ignore_index=True).to_csv(log_file, index=False)
                    st.rerun()

st.metric("App Balance", f"${current_balance:,.2f}")

tab1, tab2, tab3, tab4 = st.tabs(["🛒 Purchase", "💵 Top Up", "🤝 Lend", "🪙 Cash Audit"])

# --- TAB 1: PURCHASE ---
with tab1:
    items_in_history = log_df[log_df["Type"]=="Spend"]["Item"].unique().tolist() if not log_df.empty else []
    selection = st.selectbox("Select Item:", ["-- New Item --"] + items_in_history, key="sel_item")
    if selection == "-- New Item --":
        i_name = st.text_input("Item Name", key="new_i")
        i_price = st.number_input("Price ($)", min_value=0.0, step=0.01, key="new_p")
    else:
        i_name = selection
        i_price = log_df[log_df["Item"]==selection]["Total Cost"].iloc[-1] / log_df[log_df["Item"]==selection]["Quantity"].iloc[-1]
        st.info(f"Price: ${i_price:.2f}")
    qty = st.number_input("Quantity", min_value=1, step=1, key="new_q")
    if st.button("Confirm Purchase", key="p_btn", use_container_width=True):
        if i_name:
            new_bal = current_balance - (i_price * qty)
            new_row = pd.DataFrame([{"Date": datetime.now().strftime("%Y-%m-%d"), "Item": i_name, "Quantity": qty, "Total Cost": i_price*qty, "Wallet Left": new_bal, "Type": "Spend"}])
            new_row.to_csv(log_file, mode='a', header=not os.path.isfile(log_file), index=False)
            st.rerun()

# --- TAB 2: TOP UP ---
with tab2:
    t_amt = st.number_input("Top Up Amount ($)", min_value=0.0, key="t_amt")
    if st.button("Add to Wallet", key="t_btn", use_container_width=True):
        new_row = pd.DataFrame([{"Date": datetime.now().strftime("%Y-%m-%d"), "Item": "TOP UP", "Quantity": 1, "Total Cost": 0, "Wallet Left": current_balance + t_amt, "Type": "TopUp"}])
        new_row.to_csv(log_file, mode='a', header=not os.path.isfile(log_file), index=False)
        st.rerun()

# --- TAB 3: LEND ---
with tab3:
    f_name = st.text_input("Who borrowed?", key="f_name")
    l_amt = st.number_input("Lend Amount ($)", min_value=0.0, key="l_amt_loan")
    if st.button("Confirm Loan", key="l_btn", use_container_width=True):
        if f_name:
            new_bal = current_balance - l_amt
            new_row = pd.DataFrame([{"Date": datetime.now().strftime("%Y-%m-%d"), "Item": f"LENT TO: {f_name}", "Quantity": 1, "Total Cost": l_amt, "Wallet Left": new_bal, "Type": "Lend"}])
            new_row.to_csv(log_file, mode='a', header=not os.path.isfile(log_file), index=False)
            st.rerun()

# --- TAB 4: CASH AUDIT (FULL VERSION) ---
with tab4:
    st.subheader("Physical Cash Count")
    col1, col2 = st.columns(2)
    with col1:
        st.write("**Bills**")
        n100 = st.number_input("$100", min_value=0, step=1, key="n100")
        n50 = st.number_input("$50", min_value=0, step=1, key="n50")
        n10 = st.number_input("$10", min_value=0, step=1, key="n10")
        n5 = st.number_input("$5", min_value=0, step=1, key="n5")
        n2 = st.number_input("$2", min_value=0, step=1, key="n2")
    with col2:
        st.write("**Coins**")
        c50 = st.number_input("50¢", min_value=0, step=1, key="c50")
        c20 = st.number_input("20¢", min_value=0, step=1, key="c20")
        c10 = st.number_input("10¢", min_value=0, step=1, key="c10")
        c05 = st.number_input("5¢", min_value=0, step=1, key="c05")
        c01 = st.number_input("1¢", min_value=0, step=1, key="c01")

    physical_total = (n100*100) + (n50*50) + (n10*10) + (n5*5) + (n2*2) + \
                     (c50*0.50) + (c20*0.20) + (c10*0.10) + (c05*0.05) + (c01*0.01)

    st.divider()
    st.write(f"### Physical Total: **${physical_total:.2f}**")
    
    diff = physical_total - current_balance
    if abs(diff) < 0.01:
        st.success("✅ Perfectly matched! Your wallet and app are in sync.")
    elif diff > 0:
        st.warning(f"🤔 You have **${diff:.2f} extra** in your wallet. Did you forget to log a Top Up?")
    else:
        st.error(f"❌ You are **${abs(diff):.2f} short**. Did you forget to log a purchase?")

# --- HISTORY & DELETION ---
st.divider()
st.header("📊 History & Settings")
if not log_df.empty:
    st.dataframe(log_df.iloc[::-1], use_container_width=True)
    c1, c2 = st.columns(2)
    with c1:
        rows = st.multiselect("Delete Rows:", options=log_df.index, format_func=lambda x: f"{log_df.iloc[x]['Item']}")
        if st.button("Delete Selected"):
            log_df.drop(rows).to_csv(log_file, index=False)
            st.rerun()
    with c2:
        if st.button("🧨 Wipe All Data"):
            if os.path.exists(log_file): os.remove(log_file)
            st.rerun()
