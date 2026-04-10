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

# --- TAB 1: ORDER FOOD (USE PRE-MADE MENU) ---
with tab1:
    st.subheader("Quick Purchase")
    all_shops = sorted([s for s in log_df["Shop"].unique().tolist() if s != "N/A"]) if not log_df.empty else []
    
    shop_name = st.selectbox("Select Stall/Location", ["-- Choose --"] + all_shops)
    
    if shop_name != "-- Choose --":
        # Get items assigned to this shop
        shop_items = log_df[log_df["Shop"] == shop_name]["Item"].unique().tolist()
        clean_items = sorted(list(set([name.split(' +')[0].strip() for name in shop_items])))
        
        selection = st.selectbox("What are you eating?", ["-- Select Item --"] + clean_items)
        
        if selection != "-- Select Item --":
            # Search for the "Clean" price (where cost > 0 but it's the base item)
            # We look for the most recent entry of this item at this shop
            item_data = log_df[(log_df["Shop"] == shop_name) & (log_df["Item"] == selection)]
            
            # If the item was only 'pre-loaded' (cost 0 in admin), we look for that
            base_price = 0.0
            if not item_data.empty:
                # Get the price from the most recent transaction that wasn't a 'Menu Setup'
                real_purchases = item_data[item_data["Type"] == "Spend"]
                if not real_purchases.empty:
                    base_price = real_purchases.iloc[-1]["Total Cost"] / real_purchases.iloc[-1]["Quantity"]
                else:
                    # If only pre-loaded via Admin (Type: MenuSetup)
                    base_price = item_data.iloc[-1]["Total Cost"] 

            st.info(f"Price: ${base_price:.2f}")
            
            # Extras Builder
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

# --- TAB 2, 3, 4 (Standard Logic) ---
with tab2:
    top_amt = st.number_input("Top up amount", min_value=0.0)
    if st.button("Add to Wallet"):
        nr = pd.DataFrame([{"Date": datetime.now().strftime("%Y-%m-%d"), "Item": "Wallet Top-up", "Shop": "N/A", "Quantity": 1, "Total Cost": 0, "Wallet Left": current_balance + top_amt, "Type": "TopUp"}])
        nr.to_csv(log_file, mode='a', index=False, header=not os.path.exists(log_file))
        st.rerun()

# --- ADMINISTRATION (THE MENU MAKER) ---
st.divider()
st.header("🔐 School Admin: Menu Setup")
pwd = st.text_input("Admin Password", type="password")

if pwd == ADMIN_PASSWORD:
    st.success("Admin Mode Active")
    
    st.subheader("📍 Register Shop & Menu Prices")
    col_s1, col_s2, col_s3 = st.columns([2, 2, 1])
    
    new_shop = col_s1.text_input("Stall Name (e.g. Noodle Shop)")
    new_item = col_s2.text_input("Food Name (e.g. Fishball Noodles)")
    new_price = col_s3.number_input("Price ($)", min_value=0.0, step=0.10)
    
    if st.button("Add to School Menu", use_container_width=True):
        if new_shop and new_item:
            # We save this as a "MenuSetup" type so it doesn't affect your wallet balance
            # Wallet Left stays the same as current
            setup_row = pd.DataFrame([{
                "Date": datetime.now().strftime("%Y-%m-%d"),
                "Item": new_item,
                "Shop": new_shop,
                "Quantity": 1,
                "Total Cost": new_price, 
                "Wallet Left": current_balance,
                "Type": "MenuSetup"
            }])
            setup_row.to_csv(log_file, mode='a', index=False, header=not os.path.exists(log_file))
            st.rerun()

    st.divider()
    st.subheader("📊 Data Management")
    st.dataframe(log_df.iloc[::-1], use_container_width=True)
    
    # Delete Tools
    rows_to_del = st.multiselect("Select rows to remove:", options=log_df.index)
    if st.button("Delete Selected"):
        log_df.drop(rows_to_del).to_csv(log_file, index=False)
        st.rerun()
    if st.button("🧨 Reset Everything", type="primary"):
        if os.path.exists(log_file): os.remove(log_file)
        st.rerun()
