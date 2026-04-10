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

tab1, tab2, tab3 = st.tabs(["🛒 Log Purchase", "💵 Top Up", "🪙 Cash Audit"])

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
    st.subheader("Physical Cash Count")
    st.write("Enter how many of each you have in your wallet:")
    
    col1, col2 = st.columns(2)
    with col1:
        # Bills
        n100 = st.number_input("$100 Bills", min_value=0, step=1)
        n50 = st.number_input("$50 Bills", min_value=0, step=1)
        n10 = st.number_input("$10 Bills", min_value=0, step=1)
        n5 = st.number_input("$5 Bills", min_value=0, step=1)
        n2 = st.number_input("$2 Bills", min_value=0, step=1)
    
    with col2:
        # Coins (Simplified to Dollars for math)
        c50 = st.number_input("50¢ Coins", min_value=0, step=1)
        c20 = st.number_input("20¢ Coins", min_value=0, step=1)
        c10 = st.number_input("10¢ Coins", min_value=0, step=1)
        c05 = st.number_input("5¢ Coins", min_value=0, step=1)
        c01 = st.number_input("1¢ Coins", min_value=0, step=1)

    # Calculate Total
    physical_total = (n100*100) + (n50*50) + (n10*10) + (n5*5) + (n2*2) + \
                     (c50*0.50) + (c20*0.20) + (c10*0.10) + (c05*0.05) + (c01*0.01)

    st.divider()
    st.write(f"### Total Cash in Hand: **${physical_total:.2f}**")
    
    difference = physical_total - current_balance
    
    if abs(difference) < 0.01:
        st.success("✅ Perfect! Your physical cash matches the app.")
    elif difference > 0:
        st.warning(f"🤔 You have **${difference:.2f} more** than the app says. Did you find money?")
    else:
        st.error(f"❌ You are **${abs(difference):.2f} short**. Did you forget to log a purchase?")

# --- HISTORY ---
st.divider()
st.header("📊 History")
if not log_df.empty:
    st.dataframe(log_df.iloc[::-1], use_container_width=True)
    if st.button("🧨 Wipe All Data"):
        if os.path.exists(log_file): os.remove(log_file)
        st.rerun()
