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

# Clean text
df["Leave Type"] = df["Leave Type"].astype(str).str.strip()

# ==============================
# CREATE TABS
# ==============================
staff_names = df["Name"].unique().tolist()
tabs = st.tabs(["🏠 Summary"] + [f"👤 {name}" for name in staff_names])

# ==============================
# 🏠 SUMMARY TAB
# ==============================
with tabs[0]:

    st.markdown("## 📊 Live KPIs")

    today = pd.Timestamp.today().normalize()
    today_df = df[df["Date"] == today]

    total = len(df)
    absent_today = len(today_df)
    late_count = df["Leave Type"].str.contains("Late", case=False).sum()
    late_rate = (late_count / max(total,1)) * 100

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("📅 Total Records", total)
    c2.metric("🚫 Absent Today", absent_today)
    c3.metric("⏰ Late Count", late_count)
    c4.metric("📈 Late %", f"{late_rate:.2f}%")

    col1, col2 = st.columns([2,1])

    # Live Status
    with col1:
        st.markdown("## 🟢 Live Status (Today)")
        if today_df.empty:
            st.success("✅ Everyone Present")
        else:
            st.dataframe(today_df, use_container_width=True)

    # Alerts
    with col2:
        st.markdown("## 🚨 Alerts")

        alerts = []
        freq = df["Name"].value_counts()

        for name, count in freq.items():
            if count >= 3:
                alerts.append(f"⚠️ {name} frequent absence")

        if late_count >= 3:
            alerts.append("⏰ High late cases")

        if absent_today > 0:
            alerts.append("🚫 Staff absent today")

        if not alerts:
            st.success("✅ No alerts")
        else:
            for a in alerts:
                st.error(a)

    # Today Breakdown
    st.markdown("## 📊 Today Breakdown")

    if not today_df.empty:
        breakdown = today_df["Leave Type"].value_counts().reset_index()
        breakdown.columns = ["Type", "Count"]

        fig = px.bar(breakdown, x="Type", y="Count", text="Count")
        fig.update_traces(textposition="outside")

        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No absences today")

    # Latest Entry
    st.markdown("## 🆕 Latest Entry")

    latest = df.sort_values("Date", ascending=False).head(1)
    st.dataframe(latest, use_container_width=True)

# ==============================
# 👤 STAFF TABS
# ==============================
for i, person in enumerate(staff_names, start=1):

    with tabs[i]:

        st.markdown(f"## 👤 {person} Dashboard")

        person_df = df[df["Name"] == person]

        total = len(person_df)
        late_count = person_df["Leave Type"].str.contains("Late", case=False).sum()
        absence_count = person_df["Leave Type"].isin(["ML","VL","UL"]).sum()

        late_rate = (late_count / max(total,1)) * 100
        absence_rate = (absence_count / max(total,1)) * 100

        c1, c2, c3 = st.columns(3)
        c1.metric("📅 Total", total)
        c2.metric("⏰ Late %", f"{late_rate:.2f}%")
        c3.metric("🚫 Absence %", f"{absence_rate:.2f}%")

        # Monthly Chart
        st.markdown("📈 Monthly")

        temp = person_df.copy()
        temp["Month"] = temp["Date"].dt.to_period("M").astype(str)

        monthly = temp.groupby("Month").size().reset_index(name="Count")

        fig = px.bar(monthly, x="Month", y="Count", text="Count")
        fig.update_traces(textposition="outside")

        st.plotly_chart(fig, use_container_width=True)

        # Leave Breakdown
        st.markdown("📊 Leave Breakdown")

        breakdown = person_df["Leave Type"].value_counts().reset_index()
        breakdown.columns = ["Type", "Count"]

        fig2 = px.pie(breakdown, names="Type", values="Count")
        st.plotly_chart(fig2, use_container_width=True)

        # Alerts
        st.markdown("🚨 Alerts")

        alerts = []
        if late_count >= 3:
            alerts.append("⏰ Frequent late")
        if absence_count >= 3:
            alerts.append("🚫 Frequent absence")

        if not alerts:
            st.success("✅ No issues")
        else:
            for a in alerts:
                st.warning(a)
