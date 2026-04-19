import streamlit as st
import pandas as pd
import plotly.express as px
from streamlit_autorefresh import st_autorefresh
from datetime import datetime

# ==============================
# PAGE CONFIG
# ==============================
st.set_page_config(layout="wide")
st.title("🔴 Attendance Ops Dashboard")

# ==============================
# AUTO REFRESH
# ==============================
st_autorefresh(interval=30000, key="refresh")

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
    df = pd.read_csv(url)
    df.columns = [str(c).strip() for c in df.columns]
    return df

df_raw = load_data()

# Manual refresh
if st.button("🔄 Refresh Now"):
    st.cache_data.clear()
    st.rerun()

st.caption(f"Last updated: {datetime.now().strftime('%d %b %Y %H:%M:%S')}")

# ==============================
# TRANSFORM DATA
# ==============================
df_raw = df_raw.dropna(how="all").reset_index(drop=True)

df1 = df_raw.iloc[:, 0:6].copy()
df2 = df_raw.iloc[:, 7:13].copy()

df1.columns = ["Date","Day","Leave Type","Reason","Late","Relief"]
df2.columns = ["Date","Day","Leave Type","Reason","Late","Relief"]

df1["Name"] = staff1_name
df2["Name"] = staff2_name

df = pd.concat([df1, df2])

# Clean date
df["Date"] = pd.to_datetime(df["Date"].astype(str).str.strip(), errors="coerce")
df = df.dropna(subset=["Date"])

# ==============================
# FILTER START DATE
# ==============================
start_date = pd.to_datetime("2024-12-30")
df = df[df["Date"] >= start_date]

st.caption("Showing data from 30 Dec 2024 onwards")

# ==============================
# CLEAN TEXT
# ==============================
df["Leave Type"] = (
    df["Leave Type"]
    .astype(str)
    .str.strip()
    .str.lower()
)

# ==============================
# ABSENCE TYPES
# ==============================
absence_types = [
    "emergency leave",
    "ccl",
    "urgent leave",
    "vl",
    "ml"
]

# ==============================
# CREATE TABS
# ==============================
staff_names = df["Name"].unique().tolist()
tabs = st.tabs(["🏠 Summary"] + [f"👤 {name}" for name in staff_names])

# ==============================
# 🏠 SUMMARY TAB
# ==============================
with tabs[0]:

    st.markdown("## 📊 Summary")

    total_days = len(df)

    absence_count = df["Leave Type"].isin(absence_types).sum()
    late_count = df["Leave Type"].str.contains("late", case=False).sum()

    present_days = total_days - absence_count

    absence_rate = (absence_count / max(total_days,1)) * 100
    late_rate = (late_count / max(present_days,1)) * 100

    c1, c2, c3, c4 = st.columns(4)

    c1.metric("📅 Total Days", total_days)
    c2.metric("🚫 Absence", f"{absence_count} days", f"{absence_rate:.2f}%")
    c3.metric("⏰ Late", f"{late_count} days", f"{late_rate:.2f}%")
    c4.metric("✅ Present Days", present_days)

    # Today's data
    today = pd.Timestamp.today().normalize()
    today_df = df[df["Date"] == today]

    st.markdown("## 🟢 Live Status (Today)")
    if today_df.empty:
        st.success("✅ Everyone Present")
    else:
        st.dataframe(today_df, use_container_width=True)

    # Latest entry
    st.markdown("## 🆕 Latest Entry")
    latest = df.sort_values("Date", ascending=False).head(1)
    st.dataframe(latest, use_container_width=True)

# ==============================
# 👤 STAFF TABS
# ==============================
for i, person in enumerate(staff_names, start=1):

    with tabs[i]:

        st.markdown(f"## 👤 {person} Dashboard")

        # ✅ DEFINE FIRST
        person_df = df[df["Name"] == person]

        # ==========================
        # KPI
        # ==========================
        total_days = len(person_df)

        absence_count = person_df["Leave Type"].isin(absence_types).sum()
        late_count = person_df["Leave Type"].str.contains("late", case=False).sum()

        present_days = total_days - absence_count

        absence_rate = (absence_count / max(total_days,1)) * 100
        late_rate = (late_count / max(present_days,1)) * 100

        c1, c2, c3, c4 = st.columns(4)

        c1.metric("📅 Total Days", total_days)

        c2.metric(
            "🚫 Absence",
            f"{absence_count} days",
            f"{absence_rate:.2f}%"
        )

        c3.metric(
            "⏰ Late",
            f"{late_count} days",
            f"{late_rate:.2f}%"
        )

        c4.metric("✅ Present Days", present_days)

        # ==========================
        # MONTHLY CHART
        # ==========================
        st.markdown("📈 Monthly")

        temp = person_df.copy()
        temp["Month"] = temp["Date"].dt.to_period("M").astype(str)

        monthly = temp.groupby("Month").size().reset_index(name="Count")

        fig = px.bar(monthly, x="Month", y="Count", text="Count")
        fig.update_traces(textposition="outside")

        st.plotly_chart(fig, use_container_width=True)

        # ==========================
        # LEAVE BREAKDOWN
        # ==========================
        st.markdown("📊 Leave Breakdown")

        breakdown = person_df["Leave Type"].value_counts().reset_index()
        breakdown.columns = ["Type", "Count"]

        fig2 = px.pie(breakdown, names="Type", values="Count")
        st.plotly_chart(fig2, use_container_width=True)

        # ==========================
        # ALERTS
        # ==========================
        st.markdown("🚨 Alerts")

        alerts = []

        if absence_rate > 40:
            alerts.append("🚫 High absence rate")

        if late_rate > 30:
            alerts.append("⏰ High late rate")

        if not alerts:
            st.success("✅ No issues")
        else:
            for a in alerts:
                st.warning(a)
