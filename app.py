import streamlit as st
import pandas as pd
from datetime import datetime
import os

# --- CONFIG ---
log_file = "money_tracker.csv"
ADMIN_PASSWORD = "123"

st.set_page_config(page_title="School Money Tracker", layout="centered")

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

st.title("💰 School Money Tracker")
st.metric("Current Balance", f"${current_balance:,.2f}")

tab1, tab2, tab3, tab4 = st.tabs(["🛒 Order Food", "💵 Top Up", "🤝 Lend", "🪙 Audit"])

# --- TAB 1: ORDER FOOD ---
with tab1:
    st.subheader("Quick Purchase")
    all_shops = sorted([s for s in log_df["Shop"].unique().tolist() if s != "N/A"]) if not log_df.empty else []
    shop_name = st.selectbox("Select Stall", ["-- Choose --"] + all_shops)
    
    if shop_name != "-- Choose --":
        shop_items = log_df[log_df["Shop"] == shop_name]["Item"].unique().tolist()
        clean_items = sorted(list(set([name.split(' +')[0].strip() for name in shop_items])))
        selection = st.selectbox("What are you eating?", ["-- Select Item --"] + clean_items)
        
        if selection != "-- Select Item --":
            item_data = log_df[(log_df["Shop"] == shop_name) & (log_df["Item"] == selection)]
            base_price = 0.0
            if not item_data.empty:
                # Get the price from the most recent transaction (including setup rows)
                base_price = item_data.iloc[-1]["Total Cost"] if item_data.iloc[-1]["Type"] == "MenuSetup" else item_data.iloc[-1]["Total Cost"] / item_data.iloc[-1]["Quantity"]

            st.info(f"Base Price: ${base_price:.2f}")
            
            with st.expander("Add Extras (Optional)"):
                ca, cb, cc = st.columns([2, 1, 1])
                en = ca.text_input("Extra Item")
                ep = cb.number_input("Cost", min_value=0.0, step=0.10)
                if cc.button("➕ Add"):
                    if en:
                        st.session_state.addons_list.append({"name": en, "price": ep})
                        st.rerun()
                
                for add in st.session_state.addons_list:
                    st.write(f"✅ {add['name']} (+${add['price']:.2f})")
                if st.session_state.addons_list and st.button("Clear Extras"):
                    st.session_state.addons_list = []
                    st.rerun()

            qty = st.number_input("Quantity", min_value=1, step=1)
            total_addons = sum(a['price'] for a in st.session_state.addons_list)
            final_total = (base_price + total_addons) * qty
            st.write(f"### Total to Pay: **${final_total:.2f}**")
            
            if st.button("Confirm Purchase", use_container_width=True, type="primary"):
                full_name = selection + (" +" + " +".join([a['name'] for a in st.session_state.addons_list]) if st.session_state.addons_list else "")
                new_row = pd.DataFrame([{"Date": datetime.now().strftime("%Y-%m-%d"), "Item": full_name, "Shop": shop_name, "Quantity": qty, "Total Cost": final_total, "Wallet Left": current_balance - final_total, "Type": "Spend"}])
                new_row.to_csv(log_file, mode='a', header=not os.path.exists(log_file), index=False)
                st.session_state.addons_list = []
                st.rerun()

# --- TABS 2, 3, 4 ---
with tab2:
    top_amt = st.number_input("Top up amount", min_value=0.0)
    if st.button("Add to Wallet"):
        nr = pd.DataFrame([{"Date": datetime.now().strftime("%Y-%m-%d"), "Item": "Top-up", "Shop": "N/A", "Quantity": 1, "Total Cost": 0, "Wallet Left": current_balance + top_amt, "Type": "TopUp"}])
        nr.to_csv(log_file, mode='a', index=False); st.rerun()

with tab3:
    fr = st.text_input("Who borrowed?")
    am = st.number_input("Amount", min_value=0.0)
    if st.button("Lend Money"):
        nr = pd.DataFrame([{"Date": datetime.now().strftime("%Y-%m-%d"), "Item": f"LENT: {fr}", "Shop": "N/A", "Quantity": 1, "Total Cost": am, "Wallet Left": current_balance - am, "Type": "Lend"}])
        nr.to_csv(log_file, mode='a', index=False); st.rerun()

with tab4:
    st.subheader("Physical Cash Audit")
    # (Audit logic here)

# --- USER SECTION: HISTORY & DELETE (ALWAYS VISIBLE) ---
st.divider()
st.header("📊 History & Mistakes")
if not log_df.empty:
    # Filter out "MenuSetup" rows so the user only sees their actual spending
    display_df = log_df[log_df["Type"] != "MenuSetup"]
    st.dataframe(display_df.iloc[::-1], use_container_width=True)
    
    rows_to_del = st.multiselect("Select mistakes to delete:", options=display_df.index, format_func=lambda x: f"{log_df.loc[x, 'Item']} (${log_df.loc[x, 'Total Cost']:.2f})")
    if st.button("Delete Selected History"):
        log_df = log_df.drop(rows_to_del)
        log_df.to_csv(log_file, index=False)
        st.rerun()
else:
    st.info("No history yet.")

# --- ADMIN SECTION: MENU SETUP (PASSWORD PROTECTED) ---
st.divider()
with st.expander("🔐 Administration (Menu Setup)"):
    pwd = st.text_input("Admin Password", type="password")
    if pwd == ADMIN_PASSWORD:
        st.subheader("📍 Register Menu Prices")
        c_a, c_b, c_c = st.columns([2, 2, 1])
        n_shop = c_a.text_input("Stall")
        n_item = c_b.text_input("Item")
        n_price = c_c.number_input("Price", min_value=0.0, step=0.10)
        
        if st.button("Save to Master Menu", use_container_width=True):
            if n_shop and n_item:
                setup_row = pd.DataFrame([{"Date": datetime.now().strftime("%Y-%m-%d"), "Item": n_item, "Shop": n_shop, "Quantity": 1, "Total Cost": n_price, "Wallet Left": current_balance, "Type": "MenuSetup"}])
                setup_row.to_csv(log_file, mode='a', index=False); st.rerun()

        st.divider()
        st.subheader("🗑️ Menu Cleanup")
        col_del1, col_del2 = st.columns(2)
        with col_del1:
            s_wipe = st.selectbox("Forget Stall", ["-- Select --"] + all_shops)
            if st.button("Delete Stall Menu"):
                log_df = log_df[log_df["Shop"] != s_wipe]
                log_df.to_csv(log_file, index=False); st.rerun()
        if st.button("🧨 Wipe ALL Data (Reset App)", type="primary", use_container_width=True):
            if os.path.exists(log_file): os.remove(log_file); st.rerun()
    elif pwd != "":
        st.error("Incorrect Password")
