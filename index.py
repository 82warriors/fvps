import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(layout="wide")
st.title("📊 Attendance Monitoring System")

# ==============================
# CONFIG
# ==============================
SHEET_ID = "1TZcv_U-U7R9OM98AEMzZ2gvu2Ca6ddqd3yCCxXsTvhE"

staff1_name = "Amira"
staff2_name = "Idham"

# ==============================
# LOAD DATA
# ==============================
@st.cache_data
def load_data():
    url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"
    df_raw = pd.read_csv(url)
    df_raw.columns = [str(col).strip() for col in df_raw.columns]
    return df_raw

df_raw = load_data()

# ==============================
# TRANSFORM DATA
# ==============================
df_data = df_raw.iloc[2:].reset_index(drop=True)

df1 = df_data.iloc[:, 0:6].copy()
df2 = df_data.iloc[:, 7:13].copy()

df1.columns = ["Date", "Day", "Leave Type", "Reason", "Late", "Relief"]
df2.columns = ["Date", "Day", "Leave Type", "Reason", "Late", "Relief"]

df1["Name"] = staff1_name
df2["Name"] = staff2_name

df = pd.concat([df1, df2], ignore_index=True)

df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
df = df.dropna(subset=["Date"])

df["Name"] = df["Name"].astype(str).str.strip()
df["Leave Type"] = df["Leave Type"].astype(str).str.strip()

# ==============================
# DATE FILTER
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
    df = df[(df["Date"] >= pd.to_datetime(start_date)) & (df["Date"] <= pd.to_datetime(end_date))]

# ==============================
# OTHER FILTERS
# ==============================
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
tab1, tab2, tab3, tab4 = st.tabs([
    "📊 Dashboard",
    "📅 Monitoring",
    "📈 Trends",
    "📋 Data Explorer"
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

    # ==============================
    # 📊 LEAVE DISTRIBUTION (DYNAMIC)
    # ==============================
    st.markdown("### 📊 Leave Distribution")

    num_staff = df["Name"].nunique()

    if num_staff == 1:
        leave = df["Leave Type"].value_counts().reset_index()
        leave.columns = ["Leave Type", "Count"]

        fig = px.bar(
            leave,
            x="Leave Type",
            y="Count",
            text="Count",
            color="Leave Type"
        )

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

    # ==============================
    # 📊 STAFF COMPARISON
    # ==============================
    st.markdown("### 📊 Staff Comparison")

    total = df.groupby("Name").size()
    leave_breakdown = df.groupby(["Name", "Leave Type"]).size().unstack(fill_value=0)

    comparison = pd.DataFrame({
        "Total Absences": total
    }).join(leave_breakdown).fillna(0)

    comparison = comparison.reset_index().sort_values("Total Absences", ascending=False)

    st.dataframe(comparison, use_container_width=True)

# ==============================
# MONITORING (UPGRADED)
# ==============================
with tab2:
    st.subheader("📅 Monitoring")

    df_monitor = df.copy()
    df_monitor["Year"] = df_monitor["Date"].dt.year

    years = sorted(df_monitor["Year"].unique(), reverse=True)
    selected_year = st.selectbox("Select Year", years)

    df_year = df_monitor[df_monitor["Year"] == selected_year].copy()

    # Month order
    month_order = [
        "January","February","March","April","May","June",
        "July","August","September","October","November","December"
    ]

    df_year["Month"] = df_year["Date"].dt.month_name()

    monthly = df_year.groupby(["Month", "Name"]).size().reset_index(name="Count")

    monthly["Month"] = pd.Categorical(monthly["Month"], categories=month_order, ordered=True)
    monthly = monthly.sort_values("Month")

    st.markdown("### 📆 Monthly Summary")

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

    # Today
    st.markdown("### 📅 Today's Absentees")

    today = pd.Timestamp.today().normalize()
    today_df = df[df["Date"] == today]

    if today_df.empty:
        st.success("✅ No absentees today")
    else:
        st.dataframe(today_df)

    # Alerts
    st.markdown("### ⚠️ Frequent Absentees")

    alert = df["Name"].value_counts().reset_index()
    alert.columns = ["Name", "Count"]
    alert = alert[alert["Count"] >= 3]

    st.dataframe(alert)

# ==============================
# TRENDS (UNCHANGED - GOOD)
# ==============================
with tab3:
    st.subheader("📈 Pair Comparison Trends")

    df["Week"] = df["Date"].dt.to_period("W").astype(str)
    df["Month"] = df["Date"].dt.to_period("M").astype(str)

    st.markdown("### 📅 Daily Pair Comparison")
    daily = df.groupby(["Date", "Name"]).size().reset_index(name="Count")
    st.line_chart(daily.pivot(index="Date", columns="Name", values="Count").fillna(0))

    st.markdown("### 📊 Daily ECDF")
    st.plotly_chart(px.ecdf(daily, x="Count", color="Name"), use_container_width=True)

    st.markdown("### 📅 Weekly Pair")
    weekly = df.groupby(["Week", "Name"]).size().reset_index(name="Count")
    st.bar_chart(weekly.pivot(index="Week", columns="Name", values="Count").fillna(0))

    st.markdown("### 📆 Monthly Pair")
    monthly = df.groupby(["Month", "Name"]).size().reset_index(name="Count")
    st.bar_chart(monthly.pivot(index="Month", columns="Name", values="Count").fillna(0))

# ==============================
# DATA EXPLORER
# ==============================
with tab4:
    st.subheader("📋 Data Explorer")

    df_display = df.copy()
    df_display["Date"] = df_display["Date"].dt.strftime("%d %b %Y")

    def highlight_leave(val):
        if val == "ML":
            return "background-color: #ffcccc"
        elif val == "VL":
            return "background-color: #cce5ff"
        elif val == "UL":
            return "background-color: #fff3cd"
        return ""

    styled_df = df_display.style.map(highlight_leave, subset=["Leave Type"])

    st.dataframe(styled_df, use_container_width=True)
