import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
from supabase import create_client
from utils import calculate_summary

# ---------- SETUP ----------
st.set_page_config(page_title="💰 Expense Tracer", layout="wide")

# Initialize Supabase
SUPABASE_URL = st.secrets["supabase"]["url"]
SUPABASE_KEY = st.secrets["supabase"]["key"]
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

st.title("💰 Expense Tracer")

# ----------------- SESSION -----------------
if "user" not in st.session_state:
    st.session_state["user"] = None
if "user_id" not in st.session_state:
    st.session_state["user_id"] = None

# ----------------- LOGIN / SIGNUP -----------------
if st.session_state["user"] is None:
    tab_login, tab_signup = st.tabs(["Login", "Sign Up"])

    # ---- LOGIN ----
    with tab_login:
        st.subheader("Login to your account")
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        c1, c2 = st.columns([1, 1])
        with c1:
            login_btn = st.button("Login")
        with c2:
            reset_btn = st.button("Forgot Password?")

        # login
        if login_btn:
            try:
                res = supabase.auth.sign_in_with_password({"email": email, "password": password})
                if res.user:
                    st.session_state["user"] = res.user
                    st.session_state["user_id"] = res.user.id
                    name = res.user.user_metadata.get("full_name", res.user.email)
                    st.success(f"Welcome {name} 👋")
                    st.rerun()
                else:
                    st.warning("⚠️ Invalid email or password.")
            except Exception as e:
                msg = str(e).lower()
                if "invalid login credentials" in msg:
                    st.warning("⚠️ Invalid email or password.")
                elif "email not confirmed" in msg:
                    st.info("📧 Please confirm your email before logging in.")
                else:
                    st.error("❌ Unable to log in. Please try again later.")

        # password reset
        if reset_btn:
            if not email:
                st.warning("Enter your email first to receive a reset link.")
            else:
                try:
                    supabase.auth.reset_password_email(email)
                    st.info("📨 Password reset link sent! Check your inbox.")
                except Exception:
                    st.error("❌ Unable to send reset email. Try again later.")

    # ---- SIGN UP ----
    with tab_signup:
        st.subheader("Create new account")
        full_name = st.text_input("Full Name")
        username = st.text_input("Username")
        email_su = st.text_input("Email", key="signup_email")
        password_su = st.text_input("Password (min 6 chars)", type="password", key="signup_pass")

        if st.button("Sign Up"):
            if not all([full_name, username, email_su, password_su]):
                st.warning("Please fill in all fields.")
            elif len(password_su) < 6:
                st.warning("⚠️ Password must be at least 6 characters long.")
            else:
                try:
                    data = {"full_name": full_name, "username": username}
                    res = supabase.auth.sign_up(
                        {"email": email_su, "password": password_su, "data": data}
                    )
                    if res.user:
                        st.success("✅ Account created! Check your email for confirmation link.")
                    else:
                        st.warning("⚠️ Sign-up failed. Please verify your details.")
                except Exception as e:
                    msg = str(e).lower()
                    if "weak password" in msg:
                        st.warning("⚠️ Password must be at least 6 characters.")
                    elif "invalid" in msg and "email" in msg:
                        st.warning("⚠️ Please enter a valid email address.")
                    elif "already registered" in msg:
                        st.warning("⚠️ This email is already registered. Try logging in.")
                    else:
                        st.error("❌ Could not create account. Try again later.")
    st.stop()

# ----------------- MAIN APP -----------------
user = st.session_state.get("user")
user_id = st.session_state.get("user_id")

if not user or not user_id:
    st.warning("⚠️ Session expired. Please log in again.")
    st.session_state["user"] = None
    st.session_state["user_id"] = None
    st.rerun()

user_name = user.user_metadata.get("full_name", user.email)
st.sidebar.success(f"👤 Logged in as {user_name}")
if st.sidebar.button("Logout"):
    try:
        supabase.auth.sign_out()
    except Exception:
        pass
    st.session_state["user"] = None
    st.session_state["user_id"] = None
    st.rerun()

# ---------- DATABASE HELPERS ----------
def get_months():
    res = supabase.table("balance").select("month").eq("user_id", user_id).execute()
    return sorted({r["month"] for r in res.data}) if res.data else []

def add_month(month, currency="EUR"):
    months = get_months()
    if month not in months:
        supabase.table("balance").insert(
            {"user_id": user_id, "month": month, "total_money": 0, "currency": currency}
        ).execute()

def remove_month(month):
    supabase.table("expenses").delete().eq("user_id", user_id).eq("month", month).execute()
    supabase.table("balance").delete().eq("user_id", user_id).eq("month", month).execute()

def get_balance(month):
    res = supabase.table("balance").select("*").eq("user_id", user_id).eq("month", month).execute()
    if res.data:
        b = res.data[0]
        return b["total_money"], b["currency"]
    return 0, "EUR"

def update_balance(month, amount, currency):
    supabase.table("balance").update(
        {"total_money": amount, "currency": currency}
    ).eq("user_id", user_id).eq("month", month).execute()

def add_expense(description, amount, date, month):
    supabase.table("expenses").insert(
        {"user_id": user_id, "description": description, "amount": amount, "date": date, "month": month}
    ).execute()

def get_expenses(month):
    res = supabase.table("expenses").select("*").eq("user_id", user_id).eq("month", month).order("date").execute()
    return res.data or []

def delete_expense(expense_id):
    supabase.table("expenses").delete().eq("user_id", user_id).eq("id", expense_id).execute()

def edit_expense(expense_id, new_desc, new_amount):
    supabase.table("expenses").update(
        {"description": new_desc, "amount": new_amount}
    ).eq("user_id", user_id).eq("id", expense_id).execute()

# ---------- SIDEBAR ----------
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
        if st.session_state.get("selected_month") == remove_target:
            del st.session_state["selected_month"]
        st.rerun()
else:
    st.sidebar.info("No months yet! Add one above ⬆️")

# ---------- MAIN DASHBOARD ----------
if "selected_month" in st.session_state:
    selected_month = st.session_state["selected_month"]
    st.subheader(f"📊 Overview for {selected_month}")

    currency_options = ["DKK (kr)", "USD ($)", "EUR (€)"]
    currency_map = {"DKK (kr)": "kr", "USD ($)": "$", "EUR (€)": "€"}

    total_money, current_currency = get_balance(selected_month)
    current_idx = list(currency_map.values()).index(current_currency) if current_currency in currency_map.values() else 2
    selected_currency_display = st.selectbox("Select Currency:", currency_options, index=current_idx)
    selected_symbol = currency_map[selected_currency_display]

    total_money_input = st.number_input("Total Monthly Budget:", min_value=0.0, step=100.0, value=float(total_money))
    if st.button("💾 Save Budget"):
        update_balance(selected_month, total_money_input, selected_symbol)
        st.success("Budget saved successfully!")
        st.rerun()

    # ---- Add Expense ----
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
                st.success(f"Added {desc} ({selected_symbol}{amount})")
                st.rerun()
            else:
                st.warning("Please enter valid description and amount.")

    # ---- Expense Table ----
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

        # ---- Chart ----
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
        df = df.sort_values("date")
        if not df.empty:
            fig = px.bar(df, x="date", y="amount", color="description",
                         title=f"Expenses for {selected_month}", text_auto=True)
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No expenses added yet for this month.")
else:
    st.info("Select or add a month from the sidebar to begin.")
