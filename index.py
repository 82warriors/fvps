import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(layout="wide")

st.title("📊 Attendance Monitoring System")

# ==============================
# 🔧 LOAD GOOGLE SHEET
# ==============================
SHEET_ID = "1TZcv_U-U7R9OM98AEMzZ2gvu2Ca6ddqd3yCCxXsTvhE"

@st.cache_data
def load_data():
    url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"
    df_raw = pd.read_csv(url)

    # Clean column names
    df_raw.columns = [str(col).strip() for col in df_raw.columns]

    return df_raw

df_raw = load_data()

# ==============================
# 🔥 TRANSFORM 2 TABLES → 1 TABLE
# ==============================
try:
    df1 = df_raw.iloc[:, 0:6].copy()
    df2 = df_raw.iloc[:, 6:12].copy()

    df1.columns = ["Date", "Day", "Leave Type", "Reason", "Late", "Relief"]
    df2.columns = ["Date", "Day", "Leave Type", "Reason", "Late", "Relief"]

    df1["Name"] = "Staff A"
    df2["Name"] = "Staff B"

    df = pd.concat([df1, df2], ignore_index=True)

    # Clean data
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    df = df.dropna(subset=["Date"])

except Exception as e:
    st.error("⚠️ Data format issue. Check your Google Sheet structure.")
    st.write(df_raw.head())
    st.stop()

# ==============================
# 🔎 SIDEBAR FILTERS
# ==============================
st.sidebar.header("🔎 Filters")

names = st.sidebar.multiselect(
    "Staff",
    options=df["Name"].unique(),
    default=df["Name"].unique()
)

leave_types = st.sidebar.multiselect(
    "Leave Type",
    options=df["Leave Type"].dropna().unique(),
    default=df["Leave Type"].dropna().unique()
)

df = df[df["Name"].isin(names)]
df = df[df["Leave Type"].isin(leave_types)]

# ==============================
# 📊 KPI DASHBOARD
# ==============================
col1, col2, col3 = st.columns(3)

col1.metric("Total Records", len(df))
col2.metric("Total Staff", df["Name"].nunique())
col3.metric("Total Leave Types", df["Leave Type"].nunique())

# ==============================
# 📅 TODAY MONITOR
# ==============================
st.subheader("📅 Today's Absentees")

today = pd.Timestamp.today().normalize()
today_df = df[df["Date"] == today]

if today_df.empty:
    st.success("✅ No absentees today")
else:
    st.dataframe(today_df)

# ==============================
# 📈 TREND ANALYSIS
# ==============================
st.subheader("📈 Absence Trend")

trend = df.groupby("Date").size().reset_index(name="Count")

fig1 = px.line(trend, x="Date", y="Count", title="Daily Absence Trend")
st.plotly_chart(fig1, use_container_width=True)

# ==============================
# 📊 LEAVE TYPE ANALYSIS
# ==============================
st.subheader("📊 Leave Type Distribution")

leave = df["Leave Type"].value_counts().reset_index()
leave.columns = ["Leave Type", "Count"]

fig2 = px.bar(leave, x="Leave Type", y="Count")
st.plotly_chart(fig2, use_container_width=True)

# ==============================
# ⚠️ FREQUENT ABSENTEES
# ==============================
st.subheader("⚠️ Frequent Absentees")

alert = df["Name"].value_counts().reset_index()
alert.columns = ["Name", "Absence Count"]

alert = alert[alert["Absence Count"] >= 3]

st.dataframe(alert)

# ==============================
# 📅 HEATMAP (PATTERN)
# ==============================
st.subheader("📅 Absence Pattern")

df["Day"] = df["Date"].dt.day_name()
df["Month"] = df["Date"].dt.month_name()

pivot = df.pivot_table(
    index="Day",
    columns="Month",
    values="Name",
    aggfunc="count"
)

st.dataframe(pivot)

# ==============================
# 📋 FULL DATA
# ==============================
st.subheader("📋 Full Data")

st.dataframe(df)
