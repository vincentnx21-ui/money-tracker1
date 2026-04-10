# --- ADVANCED SUPERADMIN SPACE ---
if choice == "🛠️ SUPERADMIN SPACE":
    if current_user != SUPER_USER:
        st.error("🚨 SECURITY BREACH: Unauthorized Access")
    else:
        st.title("🛡️ System Command Center")
        
        # 1. TOP ROW: SYSTEM METRICS
        total_users = len(user_df) if not user_df.empty else 0
        total_tx = len(log_df[log_df["Type"] != "MenuSetup"]) if not log_df.empty else 0
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Registered Accounts", total_users)
        col2.metric("Total Transactions", total_tx)
        col3.metric("System Status", "ONLINE", delta="Stable")

        st.divider()

        # 2. TABBED MANAGEMENT
        adm_tab1, adm_tab2, adm_tab3 = st.tabs([
            "👥 User Management", 
            "📂 Global Logs", 
            "⚙️ System Settings"
        ])

        with adm_tab1:
            st.subheader("Account Registry (Decoded)")
            if not user_df.empty:
                # Add a search bar for users
                search_query = st.text_input("🔍 Search Username", "")
                filtered_users = user_df[user_df["Username"].str.contains(search_query, case=False)]
                
                # Display the table
                st.dataframe(filtered_users, use_container_width=True)

                # ADVANCED FEATURE: Delete User
                st.divider()
                user_to_kick = st.selectbox("Select User to Remove", ["-- Select --"] + user_df["Username"].tolist())
                if st.button("❌ Terminate Account", type="primary"):
                    if user_to_kick != "-- Select --" and user_to_kick != SUPER_USER:
                        new_users = user_df[user_df["Username"] != user_to_kick]
                        new_users.to_csv(USER_FILE, index=False)
                        st.success(f"Account {user_to_kick} deleted.")
                        st.rerun()
            else:
                st.info("No users registered yet.")

        with adm_tab2:
            st.subheader("Live Activity Stream")
            # Filter out the setup rows for a clean audit
            activity_only = log_df[log_df["Type"].isin(["Spend", "TopUp", "Lend"])]
            
            # Multi-select filter by user
            user_filter = st.multiselect("Filter by User", options=log_df["User"].unique())
            if user_filter:
                activity_only = activity_only[activity_only["User"].isin(user_filter)]
            
            st.dataframe(activity_only.iloc[::-1], use_container_width=True)

        with adm_tab3:
            st.subheader("Global Menu Controller")
            c1, c2, c3, c4 = st.columns(4)
            al = c1.text_input("New Location")
            as_ = c2.text_input("New Stall")
            ai = c3.text_input("New Product")
            ap = c4.number_input("Unit Price", step=0.10)
            
            if st.button("➕ Inject into Global Menu", use_container_width=True):
                if al and as_ and ai:
                    new_item = pd.DataFrame([{
                        "Date": "MASTER", "User": "ADMIN", "Location": al, 
                        "Shop": as_, "Item": ai, "Quantity": "1", 
                        "Total Cost": str(ap), "Wallet Left": "0", "Type": "MenuSetup"
                    }])
                    new_item.to_csv(LOG_FILE, mode='a', index=False)
                    st.success("Menu updated successfully!")
                    st.rerun()

            st.divider()
            st.subheader("Danger Zone")
            if st.button("🧨 Factory Reset (Wipe All Transactions)", type="primary", use_container_width=True):
                # Keeps menu but kills all spending
                clean_logs = log_df[log_df["Type"] == "MenuSetup"]
                clean_logs.to_csv(LOG_FILE, index=False)
                st.warning("All user data has been wiped.")
                st.rerun()
