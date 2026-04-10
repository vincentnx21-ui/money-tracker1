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

# --- REMINDERS SECTION ---
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

# --- TAB 1: PURCHASE (FIXED PRICE LOGIC) ---
with tab1:
    st.subheader("Order Builder")
    
    # Shop Selection
    all_shops = log_df["Shop"].unique().tolist() if not log_df.empty else []
    shop_name = st.selectbox("Where are you?", ["-- New Shop --"] + [s for s in all_shops if s != "N/A"])
    if shop_name == "-- New Shop --":
        shop_name = st.text_input("Enter Shop Name")

    # Clean Menu Logic (Only show base items)
    clean_items = []
    if not log_df.empty and shop_name != "-- New Shop --":
        raw_items = log_df[(log_df["Shop"] == shop_name) & (log_df["Type"] == "Spend")]["Item"].unique().tolist()
        clean_items = sorted(list(set([name.split(' +')[0].strip() for name in raw_items])))
    
    selection = st.selectbox("What are you buying?", ["-- New Item --"] + clean_items)
    
    if selection == "-- New Item --":
        i_name = st.text_input("Item Name")
        base_price = st.number_input("Base Price ($)", min_value=0.0, step=0.10)
    else:
        i_name = selection
        # --- THE FIX ---
        # Look for the last time you bought this item WITHOUT any '+' in the name (Clean Base Price)
        base_match = log_df[(log_df["Shop"] == shop_name) & (log_df["Item"] == selection)]
        
        if not base_match.empty:
            # We found a clean version!
            last_row = base_match.iloc[-1]
            base_price = last_row["Total Cost"] / last_row["Quantity"]
        else:
            # If we never bought it "clean", we take the first purchase of it and subtract nothing 
            # (In this case, user might need to adjust price manually once)
            match_any = log_df[(log_df["Shop"] == shop_name) & (log_df["Item"].str.startswith(selection))]
            last_row = match_any.iloc[-1]
            base_price = last_row["Total Cost"] / last_row["Quantity"]
            st.warning("Note: Last order had extras. Please check if this base price is correct.")
            
        base_price = st.number_input("Base Price ($)", value=float(base_price), step=0.10)

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
    final_unit_price = base_price + total_ex
    final_total = final_unit_price * qty
    st.write(f"### Total: **${final_total:.2f}**")

    if st.button("Confirm Order", use_container_width=True, type="primary"):
        if i_name and shop_name:
            full_save_name = i_name + (" +" + " +".join(ex_names) if ex_names else "")
            new_row = pd.DataFrame([{"Date": datetime.now().strftime("%Y-%m-%d"), "Item": full_save_name, "Shop": shop_name, "Quantity": qty, "Total Cost": final_total, "Wallet Left": current_balance - final_total, "Type": "Spend"}])
            new_row.to_csv(log_file, mode='a', header=not os.path.isfile(log_file), index=False)
            st.session_state.addons_list = []
            st.rerun()

# --- OTHER TABS (TOP UP, LEND, AUDIT) ---
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
    # Audit logic goes here...

# --- HISTORY ---
st.divider()
st.header("📊 History")
st.dataframe(log_df.iloc[::-1], use_container_width=True)
