import streamlit as st
import pandas as pd
from datetime import datetime
import os

# --- CONFIG ---
log_file = "money_tracker.csv"
ADMIN_PASSWORD = "123"

st.set_page_config(page_title="Multi-Location Tracker", layout="centered")

# --- DATABASE HELPER ---
def load_data(file, columns):
    if os.path.exists(file):
        try:
            df = pd.read_csv(file)
            # Ensure all required columns exist in the CSV
            for col in ["Location", "Shop", "Type"]:
                if col not in df.columns:
                    df[col] = "Unknown"
            return df
        except:
            return pd.DataFrame(columns=columns)
    return pd.DataFrame(columns=columns)

# Added 'Location' to the core columns
log_cols = ["Date", "Location", "Shop", "Item", "Quantity", "Total Cost", "Wallet Left", "Type"]
log_df = load_data(log_file, log_cols)
current_balance = float(log_df["Wallet Left"].iloc[-1]) if not log_df.empty else 0.0

if "addons_list" not in st.session_state:
    st.session_state.addons_list = []

st.title("💰 Smart Money Tracker")
st.metric("Current Balance", f"${current_balance:,.2f}")

tab1, tab2, tab3, tab4 = st.tabs(["🛒 Order Food", "💵 Top Up", "🤝 Lend", "🪙 Audit"])

# --- TAB 1: ORDER FOOD ---
with tab1:
    st.subheader("Quick Purchase")
    
    # 1. Select Location
    all_locs = sorted(log_df["Location"].unique().tolist()) if not log_df.empty else []
    loc_choice = st.selectbox("Select Location", ["-- Choose Location --"] + [l for l in all_locs if l != "Unknown"])
    
    if loc_choice != "-- Choose Location --":
        # 2. Select Stall based on Location
        stalls_at_loc = sorted(log_df[log_df["Location"] == loc_choice]["Shop"].unique().tolist())
        stall_choice = st.selectbox("Select Stall", ["-- Choose Stall --"] + stalls_at_loc)
        
        if stall_choice != "-- Choose Stall --":
            # 3. Select Product based on Stall
            items_at_stall = log_df[(log_df["Location"] == loc_choice) & (log_df["Shop"] == stall_choice)]["Item"].unique().tolist()
            clean_items = sorted(list(set([name.split(' +')[0].strip() for name in items_at_stall])))
            prod_choice = st.selectbox("What are you buying?", ["-- Select Product --"] + clean_items)
            
            if prod_choice != "-- Select Product --":
                # Find Price from MenuSetup
                item_data = log_df[(log_df["Shop"] == stall_choice) & (log_df["Item"] == prod_choice)]
                base_price = 0.0
                if not item_data.empty:
                    # Priority: Get price from MenuSetup rows
                    setup_rows = item_data[item_data["Type"] == "MenuSetup"]
                    if not setup_rows.empty:
                        base_price = setup_rows.iloc[-1]["Total Cost"]
                    else:
                        base_price = item_data.iloc[-1]["Total Cost"] / item_data.iloc[-1]["Quantity"]

                st.info(f"Unit Price: ${base_price:.2f}")
                
                with st.expander("Add Extras (Optional)"):
                    ca, cb, cc = st.columns([2, 1, 1])
                    en = ca.text_input("Extra Item")
                    ep = cb.number_input("Cost", min_value=0.0, step=0.10, key="extra_cost")
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
                st.write(f"### Total: **${final_total:.2f}**")
                
                if st.button("Confirm Purchase", use_container_width=True, type="primary"):
                    full_name = prod_choice + (" +" + " +".join([a['name'] for a in st.session_state.addons_list]) if st.session_state.addons_list else "")
                    new_row = pd.DataFrame([{
                        "Date": datetime.now().strftime("%Y-%m-%d"),
                        "Location": loc_choice,
                        "Shop": stall_choice,
                        "Item": full_name,
                        "Quantity": qty,
                        "Total Cost": final_total,
                        "Wallet Left": current_balance - final_total,
                        "Type": "Spend"
                    }])
                    new_row.to_csv(log_file, mode='a', header=not os.path.exists(log_file), index=False)
                    st.session_state.addons_list = []
                    st.rerun()

# --- OTHER TABS (Logic remains same) ---
with tab2:
    top_amt = st.number_input("Top up", min_value=0.0)
    if st.button("Add Cash"):
        nr = pd.DataFrame([{"Date": datetime.now().strftime("%Y-%m-%d"), "Location": "N/A", "Shop": "N/A", "Item": "Top-up", "Quantity": 1, "Total Cost": 0, "Wallet Left": current_balance + top_amt, "Type": "TopUp"}])
        nr.to_csv(log_file, mode='a', index=False); st.rerun()

# --- USER HISTORY & DELETE (ALWAYS VISIBLE) ---
st.divider()
st.header("📊 History & Mistakes")
if not log_df.empty:
    display_df = log_df[log_df["Type"] == "Spend"]
    st.dataframe(display_df.iloc[::-1], use_container_width=True)
    rows_to_del = st.multiselect("Select transactions to delete:", options=display_df.index, format_func=lambda x: f"{log_df.loc[x, 'Item']} @ {log_df.loc[x, 'Shop']} (${log_df.loc[x, 'Total Cost']:.2f})")
    if st.button("Delete Selected History"):
        log_df = log_df.drop(rows_to_del)
        log_df.to_csv(log_file, index=False); st.rerun()

# --- ADMIN SECTION: MENU SETUP ---
st.divider()
with st.expander("🔐 Administration (Master Menu Setup)"):
    pwd = st.text_input("Admin Password", type="password")
    if pwd == ADMIN_PASSWORD:
        st.subheader("📍 Build Master Menu")
        c1, c2 = st.columns(2)
        adm_loc = c1.text_input("Location (e.g. West Campus)")
        adm_stall = c2.text_input("Stall (e.g. Drinks Stall)")
        
        c3, c4 = st.columns([3, 1])
        adm_item = c3.text_input("Product Name (e.g. Ice Milo)")
        adm_price = c4.number_input("Price", min_value=0.0, step=0.05)
        
        if st.button("Save to Menu", use_container_width=True):
            if adm_loc and adm_stall and adm_item:
                setup_row = pd.DataFrame([{
                    "Date": datetime.now().strftime("%Y-%m-%d"),
                    "Location": adm_loc,
                    "Shop": adm_stall,
                    "Item": adm_item,
                    "Quantity": 1,
                    "Total Cost": adm_price,
                    "Wallet Left": current_balance,
                    "Type": "MenuSetup"
                }])
                setup_row.to_csv(log_file, mode='a', index=False, header=not os.path.exists(log_file))
                st.success(f"Added {adm_item} to {adm_stall} at {adm_loc}")
                st.rerun()

        st.divider()
        st.subheader("🗑️ Menu Cleanup")
        # Logic to delete menu items if needed...
        if st.button("🧨 Wipe ALL Data (Reset App)", type="primary"):
            if os.path.exists(log_file): os.remove(log_file)
            st.rerun()
