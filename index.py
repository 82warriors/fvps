import streamlit as st
import pandas as pd
import plotly.express as px
from sklearn.linear_model import LinearRegression
import numpy as np
from streamlit_autorefresh import st_autorefresh
from datetime import datetime

# ==============================
# PAGE CONFIG
# ==============================
st.set_page_config(page_title="Attendance Monitoring", layout="wide")
st.title("📊 Attendance Monitoring System")

# ==============================
# AUTO REFRESH (30 sec)
# ==============================
st_autorefresh(interval=30000, key="datarefresh")

# ==============================
# CONFIG
# ==============================
SHEET_ID = "1TZcv_U-U7R9OM98AEMzZ2gvu2Ca6ddqd3yCCxXsTvhE"

staff1_name = "Amira"
staff2_name = "Idham"

# ==============================
# LOAD DATA
# ==============================
@st.cache_data(ttl=30)
def load_data():
    url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"
    df_raw = pd.read_csv(url)
    df_raw.columns = [str(col).strip() for col in df_raw.columns]
    return df_raw

df_raw = load_data()

# ==============================
# MANUAL REFRESH
# ==============================
col_refresh, col_time = st.columns([1, 3])

with col_refresh:
    if st.button("🔄 Refresh Now"):
        st.cache_data.clear()
        st.rerun()

with col_time:
    st.caption(f"Last updated: {datetime.now().strftime('%d %b %Y %H:%M:%S')}")

# ==============================
# TRANSFORM DATA
# ==============================
df_data = df_raw.dropna(how="all").reset_index(drop=True)

# Protect against column mismatch
if df_data.shape[1] < 13:
    st.error("❌ Sheet format mismatch. Please check column structure.")
    st.stop()

df1 = df_data.iloc[:, 0:6].copy()
df2 = df_data.iloc[:, 7:13].copy()

df1.columns = ["Date", "Day", "Leave Type", "Reason", "Late", "Relief"]
df2.columns = ["Date", "Day", "Leave Type", "Reason", "Late", "Relief"]

df1["Name"] = staff1_name
df2["Name"] = staff2_name

df = pd.concat([df1, df2], ignore_index=True)

# Clean
df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
df = df.dropna(subset=["Date"])

df["Name"] = df["Name"].astype(str).str.strip()
df["Leave Type"] = df["Leave Type"].astype(str).str.strip()

# ==============================
# SIDEBAR FILTERS
# ==============================
st.sidebar.header("📅 Date Filter")

min_date = df["Date"].min()
max_date = df["Date"].max()

date_range = st.sidebar.date_input(
    "Select Date Range",
    [min_date, max_date],
    min_value=min_date,
    max_value=max_date
)

if len(date_range) == 2:
    start_date, end_date = date_range
    df = df[
        (df["Date"] >= pd.to_datetime(start_date)) &
        (df["Date"] <= pd.to_datetime(end_date))
    ]

st.sidebar.header("🔎 Filters")

staff_list = sorted(df["Name"].unique())
leave_list = sorted(df["Leave Type"].unique())

selected_staff = st.sidebar.multiselect("Staff", staff_list, staff_list)
selected_leave = st.sidebar.multiselect("Leave Type", leave_list, leave_list)

df = df[df["Name"].isin(selected_staff)]
df = df[df["Leave Type"].isin(selected_leave)]

# ==============================
# TABS
# ==============================
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 Dashboard",
    "📅 Monitoring",
    "📈 Trends",
    "📋 Data Explorer",
    "🤖 Forecast"
])

# ==============================
# DASHBOARD
# ==============================
with tab1:
    st.subheader("📊 Overview")

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Records", len(df))
    col2.metric("Total Staff", df["Name"].nunique())
    col3.metric("Leave Types", df["Leave Type"].nunique())

    st.markdown("### 📊 Leave Distribution")

    if df["Name"].nunique() == 1:
        leave = df["Leave Type"].value_counts().reset_index()
        leave.columns = ["Leave Type", "Count"]

        fig = px.bar(leave, x="Leave Type", y="Count", text="Count")

    else:
        leave = df.groupby(["Leave Type", "Name"]).size().reset_index(name="Count")

        fig = px.bar(
            leave,
            x="Leave Type",
            y="Count",
            color="Name",
            barmode="group",
            text="Count"
        )

    fig.update_traces(textposition="outside")
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("### 📊 Staff Comparison")

    total = df.groupby("Name").size()
    leave_breakdown = df.groupby(["Name", "Leave Type"]).size().unstack(fill_value=0)

    comparison = pd.DataFrame({"Total Absences": total}).join(leave_breakdown).fillna(0)
    comparison = comparison.reset_index().sort_values("Total Absences", ascending=False)

    st.dataframe(comparison, use_container_width=True)

# ==============================
# MONITORING
# ==============================
with tab2:
    st.subheader("📅 Monitoring")

    df_monitor = df.copy()
    df_monitor["Year"] = df_monitor["Date"].dt.year

    years = sorted(df_monitor["Year"].unique(), reverse=True)
    selected_year = st.selectbox("Select Year", years)

    df_year = df_monitor[df_monitor["Year"] == selected_year].copy()
    df_year["Month"] = df_year["Date"].dt.month_name()

    month_order = [
        "January","February","March","April","May","June",
        "July","August","September","October","November","December"
    ]

    monthly = df_year.groupby(["Month", "Name"]).size().reset_index(name="Count")
    monthly["Month"] = pd.Categorical(monthly["Month"], categories=month_order, ordered=True)
    monthly = monthly.sort_values("Month")

    fig_month = px.bar(
        monthly,
        x="Month",
        y="Count",
        color="Name",
        barmode="group",
        text="Count"
    )

    fig_month.update_traces(textposition="outside")
    st.plotly_chart(fig_month, use_container_width=True)

    st.markdown("### 📅 Today's Absentees")

    today = pd.Timestamp.today().normalize()
    today_df = df[df["Date"] == today]

    if today_df.empty:
        st.success("✅ No absentees today")
    else:
        st.dataframe(today_df, use_container_width=True)

    st.markdown("### ⚠️ Frequent Absentees")

    alert = df["Name"].value_counts().reset_index()
    alert.columns = ["Name", "Count"]
    alert = alert[alert["Count"] >= 3]

    st.dataframe(alert, use_container_width=True)

# ==============================
# TRENDS
# ==============================
with tab3:
    st.subheader("📈 Trends")

    df_trend = df.copy()
    df_trend["Week"] = df_trend["Date"].dt.to_period("W").astype(str)
    df_trend["Month"] = df_trend["Date"].dt.to_period("M").astype(str)

    st.markdown("### 📅 Daily")
    daily = df_trend.groupby(["Date", "Name"]).size().reset_index(name="Count")
    st.line_chart(daily.pivot(index="Date", columns="Name", values="Count").fillna(0))

    st.markdown("### 📅 Weekly")
    weekly = df_trend.groupby(["Week", "Name"]).size().reset_index(name="Count")
    st.bar_chart(weekly.pivot(index="Week", columns="Name", values="Count").fillna(0))

    st.markdown("### 📆 Monthly")
    monthly = df_trend.groupby(["Month", "Name"]).size().reset_index(name="Count")
    st.bar_chart(monthly.pivot(index="Month", columns="Name", values="Count").fillna(0))

# ==============================
# DATA EXPLORER
# ==============================
with tab4:
    st.subheader("📋 Data Explorer")

    df_display = df.copy()
    df_display["Date"] = df_display["Date"].dt.strftime("%d %b %Y")

    st.dataframe(df_display, use_container_width=True)

# ==============================
# FORECAST
# ==============================
with tab5:
    st.subheader("🤖 Absence Forecast")

    df_forecast = df.copy()
    df_forecast["Month"] = df_forecast["Date"].dt.to_period("M")

    monthly = df_forecast.groupby("Month").size().reset_index(name="Count")
    monthly["Month"] = monthly["Month"].dt.to_timestamp()

    monthly["t"] = np.arange(len(monthly))

    model = LinearRegression()
    model.fit(monthly[["t"]], monthly["Count"])

    future_steps = 4
    future_t = np.arange(len(monthly), len(monthly) + future_steps)

    future_pred = model.predict(future_t.reshape(-1, 1))

    future_dates = pd.date_range(
        start=monthly["Month"].iloc[-1],
        periods=future_steps + 1,
        freq="MS"
    )[1:]

    future_df = pd.DataFrame({
        "Month": future_dates,
        "Value": future_pred,
        "Type": "Forecast"
    })

    monthly.rename(columns={"Count": "Value"}, inplace=True)
    monthly["Type"] = "Actual"

    combined = pd.concat([monthly[["Month", "Value", "Type"]], future_df])

    fig = px.line(
        combined,
        x="Month",
        y="Value",
        color="Type",
        markers=True
    )

    st.plotly_chart(fig, use_container_width=True)
    st.info("📌 Forecast uses linear trend (basic prediction)")
