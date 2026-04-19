import streamlit as st
import pandas as pd
import plotly.express as px
from streamlit_autorefresh import st_autorefresh
from datetime import datetime

# ==============================
# PAGE CONFIG
# ==============================
st.set_page_config(layout="wide")
st.title("🔴 Real-Time Attendance Ops Dashboard")

# ==============================
# AUTO REFRESH (30 sec)
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

# ==============================
# MANUAL REFRESH
# ==============================
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

# Clean
df["Date"] = pd.to_datetime(df["Date"].astype(str).str.strip(), errors="coerce")
df = df.dropna(subset=["Date"])

df["Leave Type"] = df["Leave Type"].astype(str).str.strip()

# ==============================
# KPI SECTION
# ==============================
st.markdown("## 📊 Live KPIs")

today = pd.Timestamp.today().normalize()
today_df = df[df["Date"] == today]

total = len(df)
absent_today = len(today_df)
late_count = df["Leave Type"].str.contains("Late", case=False).sum()

late_rate = (late_count / max(total, 1)) * 100

c1, c2, c3, c4 = st.columns(4)

c1.metric("📅 Total Records", total)
c2.metric("🚫 Absent Today", absent_today)
c3.metric("⏰ Late Count", late_count)
c4.metric("📈 Late %", f"{late_rate:.2f}%")

# ==============================
# LIVE STATUS + ALERTS
# ==============================
col1, col2 = st.columns([2,1])

# ------------------------------
# LIVE STATUS
# ------------------------------
with col1:
    st.markdown("## 🟢 Live Status (Today)")

    if today_df.empty:
        st.success("✅ Everyone Present")
    else:
        def highlight(row):
            if "Late" in str(row["Leave Type"]):
                return ["background-color: #fff3cd"] * len(row)
            else:
                return ["background-color: #ffcccc"] * len(row)

        st.dataframe(today_df.style.apply(highlight, axis=1), use_container_width=True)

# ------------------------------
# ALERT PANEL
# ------------------------------
with col2:
    st.markdown("## 🚨 Alerts")

    alerts = []

    freq = df["Name"].value_counts()
    for name, count in freq.items():
        if count >= 3:
            alerts.append(f"⚠️ {name} frequent absence ({count})")

    if late_count >= 3:
        alerts.append("⏰ High late occurrences")

    if absent_today > 0:
        alerts.append("🚫 Staff absent today")

    if not alerts:
        st.success("✅ No alerts")
    else:
        for a in alerts:
            st.error(a)

# ==============================
# TODAY BREAKDOWN
# ==============================
st.markdown("## 📊 Today Breakdown")

if not today_df.empty:
    breakdown = today_df["Leave Type"].value_counts().reset_index()
    breakdown.columns = ["Type", "Count"]

    fig = px.bar(breakdown, x="Type", y="Count", text="Count")
    fig.update_traces(textposition="outside")

    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("No absences today")

# ==============================
# NEW ENTRY DETECTION
# ==============================
st.markdown("## 🆕 Latest Entry")

latest = df.sort_values("Date", ascending=False).head(1)

if "last_seen" not in st.session_state:
    st.session_state.last_seen = None

current_latest = latest["Date"].iloc[0]

if st.session_state.last_seen != current_latest:
    st.success("🆕 New entry detected!")
    st.session_state.last_seen = current_latest

st.dataframe(latest, use_container_width=True)
