import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(layout="wide")
st.title("📊 Attendance Monitoring System")

# ==============================
# 🔧 CONFIG
# ==============================
SHEET_ID = "1TZcv_U-U7R9OM98AEMzZ2gvu2Ca6ddqd3yCCxXsTvhE"

staff1_name = "Amira"
staff2_name = "Idham"

# ==============================
# 🔧 LOAD DATA
# ==============================
@st.cache_data
def load_data():
    url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"

    try:
        df_raw = pd.read_csv(url)
        if df_raw.empty:
            st.error("⚠️ Google Sheet empty")
            st.stop()
    except:
        st.error("❌ Cannot load Google Sheet")
        st.stop()

    df_raw.columns = [str(col).strip() for col in df_raw.columns]
    return df_raw

df_raw = load_data()

# ==============================
# 🔥 TRANSFORM DATA
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
# 🔎 SIDEBAR FILTERS
# ==============================
st.sidebar.header("🔎 Filters")

staff_list = sorted(df["Name"].unique())
leave_list = sorted(df["Leave Type"].unique())

selected_staff = st.sidebar.multiselect("Staff", staff_list, staff_list)
selected_leave = st.sidebar.multiselect("Leave Type", leave_list, leave_list)

df = df[df["Name"].isin(selected_staff)]
df = df[df["Leave Type"].isin(selected_leave)]

# ==============================
# 🧭 TABS UI
# ==============================
tab1, tab2, tab3, tab4 = st.tabs([
    "📊 Dashboard",
    "📅 Monitoring",
    "📈 Trends",
    "📋 Data"
])

# ==============================
# 📊 DASHBOARD
# ==============================
with tab1:
    st.subheader("📊 Overview")

    col1, col2, col3 = st.columns(3)

    col1.metric("Total Records", len(df))
    col2.metric("Total Staff", df["Name"].nunique())
    col3.metric("Leave Types", df["Leave Type"].nunique())

    st.markdown("### 📊 Leave Distribution")

    leave = df["Leave Type"].value_counts().reset_index()
    leave.columns = ["Leave Type", "Count"]

    fig = px.bar(leave, x="Leave Type", y="Count", text="Count")
    fig.update_traces(textposition="outside")

    st.plotly_chart(fig, use_container_width=True)

# ==============================
# 📅 MONITORING
# ==============================
with tab2:
    st.subheader("📅 Today's Absentees")

    today = pd.Timestamp.today().normalize()
    today_df = df[df["Date"] == today]

    if today_df.empty:
        st.success("✅ No absentees today")
    else:
        st.dataframe(today_df)

    st.subheader("⚠️ Frequent Absentees")

    alert = df["Name"].value_counts().reset_index()
    alert.columns = ["Name", "Count"]

    alert = alert[alert["Count"] >= 3]

    st.dataframe(alert)

# ==============================
# 📈 TRENDS
# ==============================
with tab3:
    st.subheader("📈 Trends")

    df["Week"] = df["Date"].dt.isocalendar().week
    df["Year"] = df["Date"].dt.year
    df["Year-Week"] = df["Year"].astype(str) + "-W" + df["Week"].astype(str)
    df["Month"] = df["Date"].dt.to_period("M").astype(str)

    # DAILY
    st.markdown("### 📅 Daily")
    daily = df.groupby("Date").size().reset_index(name="Count")
    st.plotly_chart(px.line(daily, x="Date", y="Count", markers=True), use_container_width=True)

    # WEEKLY
    st.markdown("### 📅 Weekly")
    weekly = df.groupby("Year-Week").size().reset_index(name="Count")
    fig_w = px.bar(weekly, x="Year-Week", y="Count", text="Count")
    fig_w.update_traces(textposition="outside")
    st.plotly_chart(fig_w, use_container_width=True)

    # MONTHLY
    st.markdown("### 📆 Monthly")
    monthly = df.groupby("Month").size().reset_index(name="Count")
    fig_m = px.bar(monthly, x="Month", y="Count", text="Count")
    fig_m.update_traces(textposition="outside")
    st.plotly_chart(fig_m, use_container_width=True)

# ==============================
# 📋 DATA
# ==============================
with tab4:
    st.subheader("📋 Data Explorer")
    st.dataframe(df)
