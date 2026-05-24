import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import os
import psycopg2
from sqlalchemy import create_engine
from dotenv import load_dotenv

# --- Configuration & Styling ---
st.set_page_config(page_title="Expense Tracker", page_icon="💳", layout="wide")

# Customizing the top header
st.markdown("""
    <h1 style='text-align: center; color: #2E86C1; margin-bottom: 0;'>💳 Personal Finance OS</h1>
    <p style='text-align: center; color: gray;'>AI-Powered Transaction Intelligence</p>
    <hr>
""", unsafe_allow_html=True)

# --- Database Setup & Connection ---
load_dotenv()

# Smart loading: Checks Streamlit secrets first (for cloud deployment), then local .env
try:
    DATABASE_URL = st.secrets["DATABASE_URL"]
except (KeyError, FileNotFoundError):
    DATABASE_URL = os.getenv("DATABASE_URL")

# SQLAlchemy requires the dialect to be 'postgresql://', not 'postgres://'
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# Create the engine Pandas will use to read data
engine = create_engine(DATABASE_URL)


def upgrade_database_schema():
    """Postgres natively supports 'IF NOT EXISTS' for adding columns."""
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()
    try:
        cursor.execute("ALTER TABLE expenses ADD COLUMN IF NOT EXISTS notes TEXT DEFAULT ''")
        conn.commit()
    except psycopg2.Error:
        pass
    finally:
        conn.close()


upgrade_database_schema()


@st.cache_data(ttl=60)
def load_data():
    # Pandas uses the SQLAlchemy engine for Postgres connections
    df = pd.read_sql_query("SELECT id, date_time, amount, merchant, category, payment_method, notes FROM expenses",
                           engine)

    df['date_time'] = pd.to_datetime(df['date_time'])
    df = df.sort_values(by='date_time', ascending=False).reset_index(drop=True)
    return df


if 'expense_data' not in st.session_state:
    st.session_state.expense_data = load_data()

df = st.session_state.expense_data

# --- Sidebar Filters ---
with st.sidebar:
    st.header("⚙️ Dashboard Controls")

    # Date Range Filter
    min_date = df['date_time'].min().date() if not df.empty else datetime.now().date()
    max_date = df['date_time'].max().date() if not df.empty else datetime.now().date()

    date_range = st.date_input(
        "Select Date Range",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date
    )

    # Category Filter
    categories = sorted(df['category'].dropna().unique())
    selected_categories = st.multiselect("Categories", categories, default=categories)

    # Payment Method Filter
    methods = sorted(df['payment_method'].dropna().unique())
    selected_methods = st.multiselect("Payment Methods", methods, default=methods)

    st.markdown("---")
    if st.button("🔄 Refresh Data"):
        st.cache_data.clear()  # Clear cache to ensure fresh pull from DB
        st.session_state.expense_data = load_data()
        st.rerun()

# --- Apply Filters ---
filtered_df = df[
    (df['category'].isin(selected_categories)) &
    (df['payment_method'].isin(selected_methods))
    ]

# Apply date filter safely
if len(date_range) == 2:
    start_date, end_date = date_range
    filtered_df = filtered_df[
        (filtered_df['date_time'].dt.date >= start_date) &
        (filtered_df['date_time'].dt.date <= end_date)
        ]

# Store the IDs of the currently filtered view so the editor callback can find them
st.session_state.current_filtered_ids = filtered_df['id'].tolist()

# --- Application Layout (Tabs) ---
tab1, tab2 = st.tabs(["📊 Dashboard Overview", "📝 Edit Transactions"])

with tab1:
    # --- Top Metric Cards ---
    total_spend = filtered_df['amount'].sum()
    total_tx = filtered_df.shape[0]

    if not filtered_df.empty:
        top_cat_name = filtered_df.groupby('category')['amount'].sum().idxmax()
        top_cat_val = filtered_df.groupby('category')['amount'].sum().max()
        top_cat_display = f"{top_cat_name} (₹{top_cat_val:,.0f})"
    else:
        top_cat_display = "N/A"

    # Use bordered containers for a "card" effect
    m1, m2, m3 = st.columns(3)
    with m1.container(border=True):
        st.metric("Total Spending", f"₹{total_spend:,.2f}")
    with m2.container(border=True):
        st.metric("Total Transactions", total_tx)
    with m3.container(border=True):
        st.metric("Top Expense Category", top_cat_display)

    st.write("")  # Spacer

    # --- Visualizations ---
    chart_col1, chart_col2 = st.columns(2)

    with chart_col1.container(border=True):
        st.subheader("Category Breakdown")
        if not filtered_df.empty:
            cat_df = filtered_df.groupby('category')['amount'].sum().reset_index()
            fig_pie = px.pie(cat_df, values='amount', names='category', hole=0.45)
            fig_pie.update_traces(textinfo='percent+label', textposition='inside')
            fig_pie.update_layout(margin=dict(t=20, b=20, l=20, r=20), showlegend=False)
            st.plotly_chart(fig_pie, use_container_width=True)
        else:
            st.info("No data available.")

    with chart_col2.container(border=True):
        st.subheader("Daily Spending Trend")
        if not filtered_df.empty:
            trend_df = filtered_df.copy()
            trend_df['Date'] = trend_df['date_time'].dt.date
            daily_trend = trend_df.groupby('Date')['amount'].sum().reset_index()

            fig_bar = px.bar(daily_trend, x='Date', y='amount', text_auto='.2s')
            fig_bar.update_traces(marker_color='#2E86C1')
            fig_bar.update_layout(
                yaxis_title="", xaxis_title="",
                margin=dict(t=20, b=20, l=20, r=20)
            )
            st.plotly_chart(fig_bar, use_container_width=True)
        else:
            st.info("No data available.")

with tab2:
    st.subheader("Transaction Ledger")
    st.caption("Click into the **Category** or **Notes** cells to edit. Changes save automatically.")


    def save_edits():
        """Callback to save edits securely using the raw database IDs via Postgres %s placeholders."""
        edited_rows = st.session_state.txn_editor["edited_rows"]
        if not edited_rows:
            return

        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()

        for row_idx, updates in edited_rows.items():
            db_id = st.session_state.current_filtered_ids[row_idx]

            # Use %s placeholders for Postgres, not ?
            if 'category' in updates:
                cursor.execute("UPDATE expenses SET category = %s WHERE id = %s", (updates['category'], db_id))
            if 'notes' in updates:
                cursor.execute("UPDATE expenses SET notes = %s WHERE id = %s", (updates['notes'], db_id))

        conn.commit()
        conn.close()

        # Update session state with fresh DB pull
        st.cache_data.clear()
        st.session_state.expense_data = load_data()
        st.toast("✅ Database updated successfully!", icon="💾")


    display_df = filtered_df.copy()

    st.data_editor(
        display_df,
        key="txn_editor",
        on_change=save_edits,
        use_container_width=True,
        hide_index=True,
        height=600,
        column_config={
            "id": None,
            "date_time": st.column_config.DatetimeColumn("Date & Time", format="DD MMM YYYY, h:mm a", disabled=True),
            "amount": st.column_config.NumberColumn("Amount", format="₹%.2f", disabled=True),
            "merchant": st.column_config.TextColumn("Merchant", disabled=True),
            "payment_method": st.column_config.TextColumn("Account/Card", disabled=True),
            "category": st.column_config.TextColumn("Category ✏️", required=True),
            "notes": st.column_config.TextColumn("Notes ✏️")
        },
        column_order=["date_time", "merchant", "amount", "category", "payment_method", "notes"]
    )