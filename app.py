import streamlit as st
import pandas as pd
from datetime import datetime
import os

# File names
log_file = "money_tracker.csv"
menu_file = "item_menu.csv"

st.set_page_config(page_title="Auto-Budget Tracker", layout="centered")

# --- DATABASE HELPERS ---
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
menu_cols = ["Item", "Price"]

menu_df = load_data(menu_file, menu_cols)
log_df = load_data(log_file, log_cols)

# --- SIDEBAR: MASTER MENU MANAGEMENT ---
st.sidebar.header("📋 Master Menu")

# Add Section
with st.sidebar.expander("➕ Add Item"):
    m_item = st.text_input("Item Name")
    m_price = st.number_input("Price ($)", min_value=0.0, step=0.01)
    if st.button("Save to Menu"):
        if m_item:
            new_row = pd.DataFrame([{"Item": m_item, "Price": m_price}])
            menu_df = pd.concat([menu_df, new_row]).drop_duplicates(subset=['Item'], keep='last')
            menu_df.to_csv(menu_file, index=False)
            st.rerun()

# Delete Section
if not menu_df.empty:
    st.sidebar.divider()
    with st.sidebar.expander("🗑️ Delete from Menu"):
        items_to_del = st.multiselect("Select items:", options=menu_df["Item"].tolist())
        if st.button("Confirm Delete"):
            # This line removes the selected items
            menu_df = menu_df[~menu_df["Item"].isin(items_to_del)]
            menu_df.to_csv(menu_file, index=False)
            st.rerun()
    
    st.sidebar.write("Current Prices:")
    st.sidebar.dataframe(menu_df, hide_index=True)

# --- MAIN APP LOGIC ---
current_balance = float(log_df["Wallet Left"].iloc[-1]) if not log_df.empty else 0.0

st.title("💰 Smart Money Tracker")
st.metric("Current Balance", f"${current_balance:,.2f}")

tab1, tab2 = st.tabs(["🛒 Log Purchase", "💵 Top Up"])

with tab1:
    if not menu_df.empty:
        selected_item = st.selectbox("What did you buy?", menu_df["Item"].tolist())
        unit_price = menu_df.loc[menu_df["Item"] == selected_item, "Price"].values[0]
        qty = st.number_input("Quantity", min_value=1, step=1)
        total_cost = qty * unit_price
        new_balance = current_balance - total_cost
        
        st.write(f"Total: **${total_cost:.2f}**")
        if st.button("Confirm Purchase", use_container_width=True):
            new_entry = pd.DataFrame([{
                "Date": datetime.now().strftime("%Y-%m-%d"),
                "Item": selected_item, "Quantity": qty,
                "Total Cost": total_cost, "Wallet Left": new_balance, "Type": "Spend"
            }])
            new_entry.to_csv(log_file, mode='a', header=not os.path.isfile(log_file), index=False)
            st.rerun()
    else:
        st.info("Add items to your menu in the sidebar first.")

with tab2:
    st.subheader("Add Money")
    top_up = st.number_input("Amount ($)", min_value=0.0, step=1.0)
    if st.button("Confirm Top Up", use_container_width=True):
        topup_entry = pd.DataFrame([{
            "Date": datetime.now().strftime("%Y-%m-%d"),
            "Item": "CASH TOP UP", "Quantity": 1,
            "Total Cost": 0, "Wallet Left": current_balance + top_up, "Type": "TopUp"
        }])
        topup_entry.to_csv(log_file, mode='a', header=not os.path.isfile(log_file), index=False)
        st.balloons()
        st.rerun()

# --- HISTORY ---
st.divider()
st.header("📊 History")
if not log_df.empty:
    st.dataframe(log_df.iloc[::-1], use_container_width=True)
    
    with st.expander("🗑️ Delete History Rows"):
        rows_to_del = st.multiselect("Pick rows:", options=log_df.index, 
                                     format_func=lambda x: f"{log_df.iloc[x]['Item']} (${log_df.iloc[x]['Total Cost']})")
        if st.button("Delete Selected"):
            log_df = log_df.drop(rows_to_del)
            log_df.to_csv(log_file, index=False)
            st.rerun()

    if st.button("🧨 Wipe All Data"):
        if os.path.exists(log_file): os.remove(log_file)
        if os.path.exists(menu_file): os.remove(menu_file)
        st.rerun()
