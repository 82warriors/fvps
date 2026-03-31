import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(layout="wide")
st.title("📊 Attendance Monitoring System")

# ==============================
# 🔧 CONFIG
# ==============================
SHEET_ID = "1TZcv_U-U7R9OM98AEMzZ2gvu2Ca6ddqd3yCCxXsTvhE"

# 👇 FIXED STAFF NAMES (STABLE)
staff1_name = "Amira"
staff2_name = "Idham"

# ==============================
# 🔧 LOAD GOOGLE SHEET
# ==============================
@st.cache_data
def load_data():
    url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"

    try:
        df_raw = pd.read_csv(url)

        if df_raw.empty:
            st.error("⚠️ Google Sheet is empty or not accessible")
            st.stop()

    except Exception:
        st.error("❌ Failed to load Google Sheet")
        st.write("👉 Make sure sharing is set to:")
        st.code("Anyone with link → Viewer")
        st.write("👉 Test this link in browser:")
        st.code(url)
        st.stop()

    df_raw.columns = [str(col).strip() for col in df_raw.columns]

    return df_raw


df_raw = load_data()

# ==============================
# 🔥 TRANSFORM DATA (FIXED STRUCTURE)
# ==============================
try:
    # Skip top rows (title + name rows)
    df_data = df_raw.iloc[2:].reset_index(drop=True)

    # Split into 2 tables
    df1 = df_data.iloc[:, 0:6].copy()
    df2 = df_data.iloc[:, 7:13].copy()  # skip empty column

    # Rename columns
    df1.columns = ["Date", "Day", "Leave Type", "Reason", "Late", "Relief"]
    df2.columns = ["Date", "Day", "Leave Type", "Reason", "Late", "Relief"]

    # Assign staff names
    df1["Name"] = staff1_name
    df2["Name"] = staff2_name

    # Combine tables
    df = pd.concat([df1, df2], ignore_index=True)

    # Clean data
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    df = df.dropna(subset=["Date"])

    df["Name"] = df["Name"].astype(str).str.strip()
    df["Leave Type"] = df["Leave Type"].astype(str).str.strip()

except Exception:
    st.error("⚠️ Data format issue - check your Google Sheet layout")
    st.dataframe(df_raw.head(10))
    st.stop()

# ==============================
# 🔎 FILTERS
# ==============================
st.sidebar.header("🔎 Filters")

staff_list = sorted(df["Name"].dropna().unique())
leave_list = sorted(df["Leave Type"].dropna().unique())

selected_staff = st.sidebar.multiselect(
    "Staff",
    options=staff_list,
    default=staff_list
)

selected_leave = st.sidebar.multiselect(
    "Leave Type",
    options=leave_list,
    default=leave_list
)

df = df[df["Name"].isin(selected_staff)]
df = df[df["Leave Type"].isin(selected_leave)]

# ==============================
# 📊 KPI
# ==============================
col1, col2, col3 = st.columns(3)

col1.metric("Total Records", len(df))
col2.metric("Total Staff", df["Name"].nunique())
col3.metric("Leave Types", df["Leave Type"].nunique())

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
# 📈 TREND
# ==============================
st.subheader("📈 Absence Trend")

trend = df.groupby("Date").size().reset_index(name="Count")

fig1 = px.line(trend, x="Date", y="Count", title="Daily Absence Trend")
st.plotly_chart(fig1, use_container_width=True)

# ==============================
# 📊 LEAVE TYPE
# ==============================
st.subheader("📊 Leave Type Distribution")

leave = df["Leave Type"].value_counts().reset_index()
leave.columns = ["Leave Type", "Count"]

fig2 = px.bar(leave, x="Leave Type", y="Count")
st.plotly_chart(fig2, use_container_width=True)

# ==============================
# ⚠️ ALERT SYSTEM
# ==============================
st.subheader("⚠️ Frequent Absentees")

alert = df["Name"].value_counts().reset_index()
alert.columns = ["Name", "Absence Count"]

alert = alert[alert["Absence Count"] >= 3]

st.dataframe(alert)

# ==============================
# 📅 HEATMAP
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
