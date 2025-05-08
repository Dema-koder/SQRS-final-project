"""
Module main.

The entry point of a frontend application on Streamlit.
"""
import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
from personal_finance_tracker_front import api

st.set_page_config(layout="wide")


def main_app():
    """Run the application."""
    cats = api.get_categories()
    category_map = {c["name"]: c["id"] for c in cats}
    id_to_category = {c["id"]: c["name"] for c in cats}
    categories = list(category_map.keys())
    categories_by_type = {"income": [], "expense": []}
    for c in cats:
        categories_by_type[c["type"]].append(c["name"])

    # TABS
    tab_overview, tab_manage, tab_add = st.tabs(
        ["Overview", "Manage Transactions", "Add Category"]
    )

    # OVERVIEW TAB
    with tab_overview:
        st.markdown("<h1 style='color:#0A1DEF;'>FinanceTracker</h1>",
                    unsafe_allow_html=True)
        summary_slot = st.empty()

        col_f, col_c1, col_c2 = st.columns([2, 3, 3])
        with col_f:
            start_date = st.date_input("Start Date",
                                       value=datetime.now().replace(day=1))
            end_date = st.date_input("End Date", value=datetime.now())
            sel_all = st.checkbox("Select All Categories", value=True)
            if sel_all:
                sel_names = st.multiselect("Categories",
                                           categories,
                                           default=categories)
            else:
                sel_names = st.multiselect("Categories", categories)
        sel_ids = [category_map[n] for n in sel_names] if sel_names else None
        summary = api.get_summary(start_date.isoformat(),
                                  end_date.isoformat(), sel_ids)
        with summary_slot.container():
            c1, c2, c3, c4 = st.columns(4)
            with c1:
                st.markdown("### Net Balance")
                st.markdown(f"<h2>${summary['net_balance']}</h2>",
                            unsafe_allow_html=True)
            with c2:
                st.markdown("### Total Income")
                st.markdown(f"<h2>${summary['total_income']}</h2>",
                            unsafe_allow_html=True)
            with c3:
                st.markdown("### Total Expenses")
                st.markdown(f"<h2>${summary['total_expenses']}</h2>",
                            unsafe_allow_html=True)
            with c4:
                st.markdown("### Period")
                st.markdown(f"<h5>{start_date} to {end_date}</h5>",
                            unsafe_allow_html=True)

        st.markdown("---")

        txns = api.get_transactions(start_date.isoformat(),
                                    end_date.isoformat(), sel_ids)
        df = pd.DataFrame(txns)
        if not df.empty:
            csv_data = df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="Export Transactions to CSV",
                data=csv_data,
                file_name=f"transactions_{start_date}_{end_date}.csv",
                mime="text/csv"
            )
        if not df.empty:
            df["Date"] = pd.to_datetime(df["date"])
            df["Amount"] = df["amount"]
            df["Category"] = df["category_id"].map(id_to_category)

            with col_c1:
                st.subheader("By Category")
                pie_data = df.groupby("Category")["Amount"] \
                    .sum() \
                    .abs() \
                    .reset_index()
                fig1 = px.pie(pie_data, names="Category",
                              values="Amount",
                              hole=0.5)
                st.plotly_chart(fig1, use_container_width=True)

            with col_c2:
                st.subheader("Over Time")
                fig2 = px.line(df.sort_values("Date"), x="Date", y="Amount")
                st.plotly_chart(fig2, use_container_width=True)
        else:
            col_c1.warning("No transactions found.")

    # TRANSACTIONS TAB
    with tab_manage:
        t_create, t_edit = st.tabs(["Create", "Edit/Delete"])

        with t_create:
            st.session_state["current_category"] = "income"
            st.subheader("Add New Transaction")
            with st.form("create_txn"):
                c_type = st.selectbox("Type", ["income", "expense"])
                c_amount = st.number_input("Amount", format="%.2f")
                c_description = st.text_input("Description")
                c_date = st.date_input("Date", value=datetime.now())
                c_category = st.selectbox(
                    "Category",
                    categories_by_type[st.session_state["current_category"]]
                )
                c_is_recurring = st.checkbox("Is Recurring", value=False)
                submitted = st.form_submit_button("Create")
                if submitted:
                    txn = {
                        "type": c_type,
                        "amount": c_amount,
                        "description": c_description,
                        "date": c_date.isoformat(),
                        "category_id": category_map[c_category],
                        "is_recurring": c_is_recurring,
                    }
                    try:
                        api.create_transaction(txn)
                        st.success("Transaction created.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Create failed: {e}")

        with t_edit:
            st.subheader("Edit or Delete Transaction")
            all_txns = api.get_transactions(None, None)
            if not all_txns:
                st.warning("No transactions to manage.")
            else:
                options = {
                    f"{id_to_category[t['category_id']]} - \
                    {t['date']} - \
                    ${t['amount']}": t
                    for t in all_txns
                }
                choice = st.selectbox("Select Transaction", options.keys())
                txn = options[choice]
                with st.form("edit_txn"):
                    e_type = st.selectbox(
                        "Type",
                        ["income", "expense"],
                        index=["income", "expense"].index(txn["type"])
                    )
                    e_amount = st.number_input(
                        "Amount", value=txn["amount"], format="%.2f"
                    )
                    e_description = st.text_input(
                        "Description", value=txn["description"] or ""
                    )
                    e_date = st.date_input(
                        "Date", value=pd.to_datetime(txn["date"])
                    )
                    e_category = st.selectbox(
                        "Category",
                        categories,
                        index=categories
                        .index(id_to_category[txn["category_id"]])
                    )
                    e_is_recurring = st.checkbox(
                        "Is Recurring", value=txn.get("is_recurring", False)
                    )
                    btn_update = st.form_submit_button("Update")
                    btn_delete = st.form_submit_button("Delete")
                    if btn_update:
                        update = {
                            "type": e_type,
                            "amount": e_amount,
                            "description": e_description,
                            "date": e_date.isoformat(),
                            "category_id": category_map[e_category],
                            "is_recurring": e_is_recurring,
                        }
                        try:
                            api.update_transaction(txn["id"], update)
                            st.success("Updated.")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Update failed: {e}")
                    if btn_delete:
                        try:
                            api.delete_transaction(txn["id"])
                            st.success("Deleted.")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Delete failed: {e}")

    # CATEGORY TAB
    with tab_add:
        st.header("Add New Category")
        name = st.text_input("Category Name")
        type_ = st.selectbox("Category Type", ["expense", "income"])
        if st.button("Create Category"):
            if not name.strip():
                st.warning("Enter a name.")
            else:
                try:
                    cat = api.create_category(name.strip(), type_)
                    st.success(f"Created **{cat['name']}** (ID {cat['id']})")
                    st.rerun()
                except Exception as e:
                    st.error(f"Create failed: {e}")


if "token" not in st.session_state:
    with st.sidebar:
        st.title("🔐 Authentication")
        mode = st.radio("Select action", ["Login", "Register"])
        if mode == "Login":
            u = st.text_input("Username", key="login_user")
            p = st.text_input("Password", type="password", key="login_pw")
            if st.button("Login"):
                try:
                    st.session_state.token = api.login(u, p)
                    st.success("Logged in successfully.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Login failed: {e}")
        else:
            u2 = st.text_input("New username", key="reg_user")
            e2 = st.text_input("Email", key="reg_email")
            p2 = st.text_input("Password", type="password", key="reg_pw")
            if st.button("Register"):
                try:
                    api.register_user(u2, e2, p2)
                    st.success("Registration successful! You can now log in.")
                except Exception as e:
                    st.error(f"Registration failed: {e}")
    st.stop()
else:
    main_app()
