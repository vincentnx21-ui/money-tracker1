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
            # Ensure 'Shop' column exists in old files
            if "Shop" not in df.columns:
                df["Shop"] = "Unknown"
            return df
        except:
            return pd.DataFrame(columns=columns)
    return pd.DataFrame(columns=columns)

log_cols = ["Date", "Item", "Shop", "Quantity", "Total Cost", "Wallet Left", "Type"]
log_df = load_data(log_file, log_cols)
current_balance = float(log_df["Wallet Left"].iloc[-1]) if not log_df.empty else 0.0

if "addons_list" not in st.session_state:
    st.session_state.addons_list = []

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
                    repaid = pd.DataFrame([{"Date": datetime.now().strftime("%Y-%m-%d"), "Item": f"REPAYMENT: {row['Item']}", "Shop": "N/A", "Quantity": 1, "Total Cost": 0, "Wallet Left": new_bal, "Type": "TopUp"}])
                    pd.concat([log_df, repaid], ignore_index=True).to_csv(log_file, index=False)
                    st.rerun()

st.metric("App Balance", f"${current_balance:,.2f}")

tab1, tab2, tab3, tab4 = st.tabs(["🛒 Purchase", "💵 Top Up", "🤝 Lend", "🪙 Audit"])

# --- TAB 1: PURCHASE WITH LOCATION & ADD-ONS ---
with tab1:
    st.subheader("Order Builder")
    
    # 1. Select Shop First
    all_shops = log_df["Shop"].unique().tolist() if not log_df.empty else []
    shop_selection = st.selectbox("Where are you buying from?", ["-- New Shop --"] + [s for s in all_shops if s != "N/A"])
    
    if shop_selection == "-- New Shop --":
        shop_name = st.text_input("Enter Shop Name (e.g., Maxwell Hawker)")
    else:
        shop_name = shop_selection

    # 2. Select Item (Filtered by Shop)
    shop_items = []
    if not log_df.empty and shop_name != "-- New Shop --":
        shop_items = log_df[(log_df["Shop"] == shop_name) & (log_df["Type"] == "Spend")]["Item"].unique().tolist()
    
    selection = st.selectbox("What are you buying?", ["-- New Item --"] + shop_items)
    
    if selection == "-- New Item --":
        i_name = st.text_input("Item Name")
        base_price = st.number_input("Base Price ($)", min_value=0.0, step=0.10)
    else:
        i_name = selection
        # Get last price for THIS specific item at THIS specific shop
        last_price_row = log_df[(log_df["Shop"] == shop_name) & (log_df["Item"] == selection)].iloc[-1]
        base_price = last_price_row["Total Cost"] / last_price_row["Quantity"]
        st.info(f"Price at {shop_name}: ${base_price:.2f}")

    st.divider()
    st.write("**Add Extras:**")
    col_a, col_b, col_c = st.columns([2, 1, 1])
    e_name = col_a.text_input("Extra", key="ex_n")
    e_price = col_b.number_input("$", min_value=0.0, step=0.10, key="ex_p")
    if col_c.button("➕ Add"):
        if e_name:
            st.session_state.addons_list.append({"name": e_name, "price": e_price})
            st.rerun()

    total_extras = 0.0
    display_extras = []
    for add in st.session_state.addons_list:
        st.write(f"✅ {add['name']} (+${add['price']:.2f})")
        total_extras += add['price']
        display_extras.append(add['name'])
    
    if st.session_state.addons_list and st.button("Clear Extras"):
        st.session_state.addons_list = []
        st.rerun()

    st.divider()
    qty = st.number_input("Quantity", min_value=1, step=1)
    final_total = (base_price + total_extras) * qty
    st.write(f"### Grand Total: **${final_total:.2f}**")

    if st.button("Confirm Final Order", use_container_width=True, type="primary"):
        if i_name and shop_name:
            full_name = i_name + (" +" + " +".join(display_extras) if display_extras else "")
            new_bal = current_balance - final_total
            new_row = pd.DataFrame([{"Date": datetime.now().strftime("%Y-%m-%d"), "Item": full_name, "Shop": shop_name, "Quantity": qty, "Total Cost": final_total, "Wallet Left": new_bal, "Type": "Spend"}])
            new_row.to_csv(log_file, mode='a', header=not os.path.isfile(log_file), index=False)
            st.session_state.addons_list = []
            st.rerun()

# --- OTHER TABS (Simplified for Code Length) ---
with tab2:
    top = st.number_input("Amount", min_value=0.0)
    if st.button("Add Cash"):
        nr = pd.DataFrame([{"Date": datetime.now().strftime("%Y-%m-%d"), "Item": "TOP UP", "Shop": "N/A", "Quantity": 1, "Total Cost": 0, "Wallet Left": current_balance + top, "Type": "TopUp"}])
        nr.to_csv(log_file, mode='a', index=False); st.rerun()

with tab3:
    fr = st.text_input("Friend")
    am = st.number_input("Amt", min_value=0.0)
    if st.button("Lend"):
        nr = pd.DataFrame([{"Date": datetime.now().strftime("%Y-%m-%d"), "Item": f"LENT TO: {fr}", "Shop": "N/A", "Quantity": 1, "Total Cost": am, "Wallet Left": current_balance - am, "Type": "Lend"}])
        nr.to_csv(log_file, mode='a', index=False); st.rerun()

with tab4:
    st.subheader("Audit") # Add your counting logic here

# --- HISTORY ---
st.divider()
st.header("📊 History")
st.dataframe(log_df.iloc[::-1], use_container_width=True)
if st.button("🧨 Wipe All Data"):
    if os.path.exists(log_file): os.remove(log_file)
    st.rerun()
