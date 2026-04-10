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
            if "Shop" not in df.columns: df["Shop"] = "Unknown"
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

# --- TAB 1: PURCHASE (CLEAN MENU) ---
with tab1:
    st.subheader("Order Builder")
    
    # 1. Shop Selection
    all_shops = log_df["Shop"].unique().tolist() if not log_df.empty else []
    shop_name = st.selectbox("Where are you?", ["-- New Shop --"] + [s for s in all_shops if s != "N/A"])
    if shop_name == "-- New Shop --":
        shop_name = st.text_input("Enter Shop Name")

    # 2. CLEAN MENU LOGIC
    # We take items from history but REMOVE the extras (anything after a ' +')
    clean_items = []
    if not log_df.empty and shop_name != "-- New Shop --":
        raw_items = log_df[(log_df["Shop"] == shop_name) & (log_df["Type"] == "Spend")]["Item"].unique().tolist()
        # This line splits the name at the first '+' and takes only the left side (the main item)
        clean_items = sorted(list(set([name.split(' +')[0].strip() for name in raw_items])))
    
    selection = st.selectbox("What are you buying?", ["-- New Item --"] + clean_items)
    
    if selection == "-- New Item --":
        i_name = st.text_input("Item Name")
        base_price = st.number_input("Base Price ($)", min_value=0.0, step=0.10)
    else:
        i_name = selection
        # Find the last time you bought this EXACT base item to get the price
        # We look for rows that START with the selection name
        match = log_df[(log_df["Shop"] == shop_name) & (log_df["Item"].str.startswith(selection))]
        last_row = match.iloc[-1]
        # We subtract existing extras from that old total to guess the base price
        base_price = last_row["Total Cost"] / last_row["Quantity"]
        st.info(f"Last base price at {shop_name}: ${base_price:.2f}")

    st.divider()
    st.write("**Add Extras (One at a time):**")
    ca, cb, cc = st.columns([2, 1, 1])
    en = ca.text_input("Extra name", key="en")
    ep = cb.number_input("$", min_value=0.0, step=0.10, key="ep")
    if cc.button("➕ Add"):
        if en:
            st.session_state.addons_list.append({"name": en, "price": ep})
            st.rerun()

    total_ex = 0.0
    ex_names = []
    for add in st.session_state.addons_list:
        st.write(f"✅ {add['name']} (+${add['price']:.2f})")
        total_ex += add['price']
        ex_names.append(add['name'])
    
    if st.session_state.addons_list and st.button("Clear Extras"):
        st.session_state.addons_list = []
        st.rerun()

    st.divider()
    qty = st.number_input("Quantity", min_value=1, step=1)
    final_total = (base_price + total_ex) * qty
    st.write(f"### Total: **${final_total:.2f}**")

    if st.button("Confirm Order", use_container_width=True, type="primary"):
        if i_name and shop_name:
            # We save with the + symbol so the history is detailed
            full_save_name = i_name + (" +" + " +".join(ex_names) if ex_names else "")
            new_row = pd.DataFrame([{"Date": datetime.now().strftime("%Y-%m-%d"), "Item": full_save_name, "Shop": shop_name, "Quantity": qty, "Total Cost": final_total, "Wallet Left": current_balance - final_total, "Type": "Spend"}])
            new_row.to_csv(log_file, mode='a', header=not os.path.isfile(log_file), index=False)
            st.session_state.addons_list = []
            st.rerun()

# --- OTHER TABS ---
with tab2:
    top = st.number_input("Amount", min_value=0.0, key="top_up")
    if st.button("Top Up"):
        nr = pd.DataFrame([{"Date": datetime.now().strftime("%Y-%m-%d"), "Item": "TOP UP", "Shop": "N/A", "Quantity": 1, "Total Cost": 0, "Wallet Left": current_balance + top, "Type": "TopUp"}])
        nr.to_csv(log_file, mode='a', index=False); st.rerun()

with tab3:
    fr = st.text_input("Friend", key="lend_fr")
    am = st.number_input("Amt", min_value=0.0, key="lend_am")
    if st.button("Lend"):
        nr = pd.DataFrame([{"Date": datetime.now().strftime("%Y-%m-%d"), "Item": f"LENT TO: {fr}", "Shop": "N/A", "Quantity": 1, "Total Cost": am, "Wallet Left": current_balance - am, "Type": "Lend"}])
        nr.to_csv(log_file, mode='a', index=False); st.rerun()

with tab4:
    st.subheader("Cash Audit")
    c1, c2 = st.columns(2)
    n100 = c1.number_input("$100", 0); n50 = c1.number_input("$50", 0); n10 = c1.number_input("$10", 0)
    c50 = c2.number_input("50¢", 0); c20 = c2.number_input("20¢", 0); c10 = c2.number_input("10¢", 0)
    p_t = (n100*100)+(n50*50)+(n10*10)+(c50*0.5)+(c20*0.2)+(c10*0.1)
    st.write(f"Total: ${p_t:.2f}")
    if st.button("Audit"): st.info(f"Diff: ${p_t - current_balance:.2f}")

# --- HISTORY ---
st.divider()
st.header("📊 History")
st.dataframe(log_df.iloc[::-1], use_container_width=True)
if st.button("🧨 Wipe Data"):
    if os.path.exists(log_file): os.remove(log_file); st.rerun()
