# To set up dependencies:
# poetry add streamlit pandas plotly requests

import os
import streamlit as st
import pandas as pd
import plotly.express as px
import requests
from datetime import datetime
from typing import Optional

API_URL = st.secrets.get("api_url", "http://localhost:8000")

if "token" not in st.session_state:
    with st.sidebar:
        st.title("🔐 Authentication")

        mode = st.radio("Select action", ["Login", "Register"])

        if mode == "Login":
            st.subheader("Login")
            username = st.text_input("Username", key="login_user")
            password = st.text_input("Password", type="password", key="login_pw")
            if st.button("Login"):
                resp = requests.post(
                    f"{API_URL}/token",
                    data={"username": username, "password": password},
                )
                if resp.status_code == 200:
                    st.session_state.token = resp.json()["access_token"]
                    st.success("Logged in successfully.")
                    st.rerun()
                else:
                    st.error(f"Login failed: {resp.status_code} – {resp.text}")

        else: 
            st.subheader("Register")
            new_username = st.text_input("New username", key="reg_user")
            new_email    = st.text_input("Email",         key="reg_email")
            new_password = st.text_input("Password",      type="password", key="reg_pw")
            if st.button("Register"):
                payload = {
                    "username": new_username,
                    "email":    new_email,
                    "password": new_password
                }
                reg = requests.post(f"{API_URL}/register", json=payload)
                if reg.status_code == 200:
                    st.success("Registration successful! You can now log in.")
                else:
                    st.error(f"Registration failed: {reg.status_code} – {reg.text}")

    st.stop()
headers = {"Authorization": f"Bearer {st.session_state.token}"}

cat_resp = requests.get(f"{API_URL}/categories/", headers=headers)
with st.sidebar.expander("Categories Debug"):
    try:
        body = cat_resp.json()
    except ValueError:
        body = cat_resp.text
    st.write({
        "status_code": cat_resp.status_code,
        "headers": dict(cat_resp.headers),
        "body": body
    })
cat_resp.raise_for_status()
categories_data = cat_resp.json()
category_map = {c['name']: c['id'] for c in categories_data}
id_to_category = {c['id']: c['name'] for c in categories_data}
categories = list(category_map.keys())

tab_overview, tab_manage = st.tabs(["Overview", "Manage Transactions"])

with tab_overview:
    st.markdown("<h1 style='color:#0A1DEF;'>FinanceTracker</h1>", unsafe_allow_html=True)
    start_date = st.date_input("Start Date", value=datetime.now().replace(day=1))
    end_date   = st.date_input("End Date",   value=datetime.now())
    select_all = st.checkbox("Select All Categories", value=True)
    if select_all:
        selected_names = st.multiselect("Categories", categories, default=categories)
    else:
        selected_names = st.multiselect("Categories", categories)

    params = {
        "start_date": start_date.isoformat(),
        "end_date":   end_date.isoformat()
    }
    if selected_names:
        cat_ids = [str(category_map[name]) for name in selected_names]
        params["category_id"] = ",".join(cat_ids)

    txn_resp = requests.get(
        f"{API_URL}/transactions/",
        headers=headers,
        params=params
    )
    txn_resp.raise_for_status()
    df = pd.DataFrame(txn_resp.json())

    if df.empty:
        st.warning("No transactions found for the selected criteria.")
    else:
        df["Date"]     = pd.to_datetime(df["date"])
        df["Amount"]   = df["amount"]
        df["Category"] = df["category_id"].map(id_to_category)

        sum_params = {
            "start_date": start_date.isoformat(),
            "end_date":   end_date.isoformat()
        }
        summary = requests.get(
            f"{API_URL}/analytics/summary",
            headers=headers,
            params=sum_params
        ).json()

        k1, k2, k3, k4 = st.columns(4)
        with k1:
            st.markdown("### Net Balance")
            st.markdown(f"<h2>${summary['net_balance']}</h2>", unsafe_allow_html=True)

        with k2:
            st.markdown("### Total Income")
            st.markdown(f"<h2>${summary['total_income']}</h2>", unsafe_allow_html=True)

        with k3:
            st.markdown("### Total Expenses")
            st.markdown(f"<h2>${summary['total_expenses']}</h2>", unsafe_allow_html=True)

        with k4:
            st.markdown("### Period")
            st.markdown(f"<h5>{start_date} to {end_date}</h5>", unsafe_allow_html=True)

        st.markdown("---")
        st.subheader("Transactions by Category")
        pie_data = (
            df
            .groupby("Category")["Amount"]
            .sum()
            .abs()
            .reset_index()
        )
        fig1 = px.pie(pie_data, names="Category", values="Amount", hole=0.5)
        st.plotly_chart(fig1, use_container_width=True)

        st.subheader("Transactions Over Time")
        fig2 = px.line(df.sort_values("Date"), x="Date", y="Amount")
        st.plotly_chart(fig2, use_container_width=True)

        st.markdown("---")

        st.header("Recent Transactions")
        for _, row in df.sort_values("Date", ascending=False).iterrows():
            cols = st.columns([2, 2, 2, 4, 2])
            cols[0].write(row["type"])
            cols[1].write(row["Date"].date())
            cols[2].write(row["Category"])
            cols[3].write(row["description"])
            cols[4].write(f"${row['Amount']}")


with tab_manage:
    t_create, t_edit = st.tabs(["Create", "Edit/Delete"])

    with t_create:
        st.subheader("Add New Transaction")
        with st.form("create_txn"):  
            c_type = st.selectbox("Type", ["income", "expense"])
            c_amount = st.number_input("Amount", format="%.2f")
            c_description = st.text_input("Description")
            c_date = st.date_input("Date", value=datetime.now())
            c_category = st.selectbox("Category", categories)
            submitted = st.form_submit_button("Create")
            if submitted:
                payload = {
                    "type": c_type,
                    "amount": c_amount,
                    "description": c_description,
                    "date": c_date.isoformat(),
                    "category_id": category_map[c_category],
                }
                resp = requests.post(f"{API_URL}/transactions/", json=payload, headers=headers)
                if resp.status_code == 200:
                    st.success("Transaction created successfully.")
                    st.rerun()
                else:
                    st.error(f"Failed: {resp.status_code} - {resp.text}")

    with t_edit:
        st.subheader("Edit or Delete Transaction")
        all_txn = requests.get(f"{API_URL}/transactions/", headers=headers).json()
        if not all_txn:
            st.warning("No transactions available to edit or delete.")
        else:
            txn_options = {f"{id_to_category[t['category_id']]} - {t['date']} - {t['amount']}$": t for t in all_txn}
            choice = st.selectbox("Select Transaction", list(txn_options.keys()))
            txn = txn_options[choice]
            with st.form("edit_txn"):  
                e_type = st.selectbox("Type", ["income", "expense"], index=["income","expense"].index(txn['type']))
                e_amount = st.number_input("Amount", value=txn['amount'], format="%.2f")
                e_description = st.text_input("Description", value=txn['description'])
                e_date = st.date_input("Date", value=pd.to_datetime(txn['date']))
                e_category = st.selectbox("Category", categories, index=list(categories).index(id_to_category[txn['category_id']]))
                update = st.form_submit_button("Update")
                delete = st.form_submit_button("Delete")
                if update:
                    up_payload = {
                        "type": e_type,
                        "amount": e_amount,
                        "description": e_description,
                        "date": e_date.isoformat(),
                        "category_id": category_map[e_category],
                    }
                    up_resp = requests.patch(f"{API_URL}/transactions/{txn['id']}", json=up_payload, headers=headers)
                    if up_resp.status_code == 200:
                        st.success("Transaction updated successfully.")
                        st.rerun()
                    else:
                        st.error(f"Update failed: {up_resp.status_code} - {up_resp.text}")
                if delete:
                    del_resp = requests.delete(f"{API_URL}/transactions/{txn['id']}", headers=headers)
                    if del_resp.status_code == 204:
                        st.success("Transaction deleted.")
                        st.rerun()
                    else:
                        st.error(f"Delete failed: {del_resp.status_code} - {del_resp.text}")
