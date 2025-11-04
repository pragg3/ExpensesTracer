import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
from database import (
    init_db, get_months, add_month, remove_month,
    get_balance, update_balance,
    add_expense, get_expenses,
    delete_expense, edit_expense
)
from utils import calculate_summary

st.set_page_config(page_title="💰 Expense Tracer", layout="wide")
st.title("💰 Expense Tracer")

init_db()


st.sidebar.header("📅 Months")

months = get_months()
new_month = st.sidebar.date_input("Add Month (pick any date in that month)")


if st.sidebar.button("➕ Add Month", use_container_width=True):
    month_str = new_month.strftime("%Y-%m")
    add_month(month_str)
    st.sidebar.success(f"Month {month_str} added!")
    st.session_state["selected_month"] = month_str
    st.rerun()


if months:
    st.sidebar.markdown("### Existing Months")
    for m in months:
        if st.sidebar.button(f"📆 {m}", key=f"month_{m}", use_container_width=True):
            st.session_state["selected_month"] = m
            st.rerun()

    st.sidebar.divider()
    remove_target = st.sidebar.selectbox("Remove Month", months)
    if st.sidebar.button("🗑️ Delete Selected Month", use_container_width=True):
        remove_month(remove_target)
        st.sidebar.warning(f"Deleted month {remove_target}")
        if "selected_month" in st.session_state and st.session_state["selected_month"] == remove_target:
            del st.session_state["selected_month"]
        st.rerun()
else:
    st.sidebar.info("No months yet! Add one above ⬆️")


if "selected_month" in st.session_state:
    selected_month = st.session_state["selected_month"]
    st.subheader(f"📊 Overview for {selected_month}")


    currency_options = ["DKK (kr)", "USD ($)", "EUR (€)"]
    currency_map = {"DKK (kr)": "kr", "USD ($)": "$", "EUR (€)": "€"}

    total_money, current_currency = get_balance(selected_month)
    current_idx = list(currency_map.values()).index(current_currency) if current_currency in currency_map.values() else 2
    selected_currency_display = st.selectbox("Select Currency:", currency_options, index=current_idx)
    selected_symbol = currency_map[selected_currency_display]

    total_money_input = st.number_input(
        "Total Monthly Budget:",
        min_value=0.0,
        step=100.0,
        value=float(total_money),
        key=f"balance_{selected_month}",
    )

    if st.button("💾 Save Budget"):
        update_balance(selected_month, total_money_input, selected_symbol)
        st.success("Budget saved successfully!")
        st.rerun()


    st.divider()
    st.subheader("➕ Add New Expense")

  
    colX, colY = st.columns([1, 3])
    with colX:
        add_date = st.checkbox("Add a specific date?")
    with colY:
        exp_date = st.date_input("Select Date", value=datetime.now()) if add_date else None

   
    with st.form(key=f"expense_form_{selected_month}", clear_on_submit=True):
        col1, col2 = st.columns([3, 2])
        with col1:
            desc = st.text_input("Description")
        with col2:
            amount = st.number_input("Amount", min_value=0.0, step=1.0)

        submitted = st.form_submit_button("Add Expense")
        if submitted:
            if desc and amount > 0:
                add_expense(desc, amount, exp_date.strftime("%Y-%m-%d") if exp_date else None, selected_month)
                st.success(f"Added: {desc} ({selected_symbol}{amount})")
                st.rerun()
            else:
                st.warning("Please enter valid description and amount.")


 
    expenses = get_expenses(selected_month)
    if expenses:
        spent, remaining, df = calculate_summary(expenses, total_money_input)

        colA, colB = st.columns(2)
        colA.metric("Total Spent", f"{selected_symbol}{spent:,.2f}")
        colB.metric("Remaining", f"{selected_symbol}{remaining:,.2f}")

        st.write("### All Expenses")
        st.caption("Edit inline and click **Update** to save, 🗑️ to remove.")

        for exp in expenses:
            cols = st.columns([3, 2, 2, 1, 1])
            with cols[0]:
                new_desc = st.text_input("Description", exp["description"], key=f"desc_{exp['id']}")
            with cols[1]:
                new_amount = st.number_input("Amount", value=float(exp["amount"]), step=1.0, key=f"amt_{exp['id']}")
            with cols[2]:
                st.text(exp["date"] or "—")
            with cols[3]:
                if st.button("Update", key=f"update_{exp['id']}"):
                    edit_expense(exp["id"], new_desc, new_amount)
                    st.success(f"Updated {exp['description']}")
                    st.rerun()
            with cols[4]:
                if st.button("🗑️", key=f"del_{exp['id']}"):
                    delete_expense(exp["id"])
                    st.warning(f"Deleted {exp['description']}")
                    st.rerun()

   
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
        df = df.sort_values("date")
        if not df.empty:
            fig = px.bar(
                df,
                x="date",
                y="amount",
                color="description",
                title=f"Expenses for {selected_month}",
                text_auto=True,
            )
            st.plotly_chart(fig, use_container_width=True)

        updated_expenses = get_expenses(selected_month)
        new_spent, new_remaining, _ = calculate_summary(updated_expenses, total_money_input)
        st.metric("🔁 Updated Total Spent", f"{selected_symbol}{new_spent:,.2f}")
        st.metric("Updated Remaining", f"{selected_symbol}{new_remaining:,.2f}")

    else:
        st.info("No expenses added yet for this month.")
else:
    st.info("Select or add a month from the sidebar to begin.")
