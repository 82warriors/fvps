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

if st.button("🔄 Refresh Now"):
    st.cache_data.clear()
    st.rerun()

st.caption(f"Last updated: {datetime.now().strftime('%d %b %Y %H:%M:%S')}")

# ==============================
# TRANSFORM
# ==============================
df_raw = df_raw.dropna(how="all").reset_index(drop=True)

df1 = df_raw.iloc[:, 0:6].copy()
df2 = df_raw.iloc[:, 7:13].copy()

df1.columns = ["Date","Day","Leave Type","Reason","Late","Relief"]
df2.columns = ["Date","Day","Leave Type","Reason","Late","Relief"]

df1["Name"] = staff1_name
df2["Name"] = staff2_name

df = pd.concat([df1, df2])

df["Date"] = pd.to_datetime(df["Date"].astype(str).str.strip(), errors="coerce")
df = df.dropna(subset=["Date"])

# Filter start date
start_date = pd.to_datetime("2024-12-30")
df = df[df["Date"] >= start_date]

# Clean text
df["Leave Type"] = (
    df["Leave Type"]
    .astype(str)
    .str.strip()
    .str.lower()
)

# Calendar days
today = pd.Timestamp.today().normalize()
calendar_days = (today - start_date).days + 1

# ==============================
# FUNCTION: ABSENCE BREAKDOWN
# ==============================
def get_absence_breakdown(data):
    ml = (data["Leave Type"] == "ml").sum()
    vl = (data["Leave Type"] == "vl").sum()
    ccl = (data["Leave Type"] == "ccl").sum()
    urgent = (data["Leave Type"] == "urgent leave").sum()
    emergency = (data["Leave Type"] == "emergency leave").sum()

    total = ml + vl + ccl + urgent + emergency

    return ml, vl, ccl, urgent, emergency, total

# ==============================
# TABS
# ==============================
staff_names = df["Name"].unique().tolist()
tabs = st.tabs(["🏠 Summary"] + [f"👤 {name}" for name in staff_names])

# ==============================
# 🏠 SUMMARY
# ==============================
with tabs[0]:

    st.markdown("## 📊 Summary")

    ml, vl, ccl, urgent, emergency, absence_total = get_absence_breakdown(df)

    late_count = df["Leave Type"].str.contains("late", case=False).sum()

    absence_rate = (absence_total / max(calendar_days,1)) * 100

    c1, c2, c3, c4, c5, c6 = st.columns(6)

    c1.metric("🩺 ML", ml)
    c2.metric("🏖 VL", vl)
    c3.metric("👶 CCL", ccl)
    c4.metric("⚡ Urgent", urgent)
    c5.metric("🚨 Emergency", emergency)

    c6.metric(
        "🚫 Total Absence",
        f"{absence_total}",
        f"{absence_rate:.2f}%"
    )

    st.metric("⏰ Late Count", late_count)

    # Today status
    today_df = df[df["Date"] == today]

    st.markdown("## 🟢 Today Status")
    if today_df.empty:
        st.success("✅ Everyone Present")
    else:
        st.dataframe(today_df, use_container_width=True)

    # Latest entry
    st.markdown("## 🆕 Latest Entry")
    latest = df.sort_values("Date", ascending=False).head(1)
    st.dataframe(latest)

# ==============================
# 👥 STAFF COMPARISON TABLE
# ==============================
st.markdown("## 👥 Staff Comparison")

comparison_data = []

for person in staff_names:

    person_df = df[df["Name"] == person]

    ml, vl, ccl, urgent, emergency, absence_total = get_absence_breakdown(person_df)
    late_count = person_df["Leave Type"].str.contains("late", case=False).sum()

    absence_rate = (absence_total / max(calendar_days,1)) * 100

    comparison_data.append({
        "Name": person,
        "ML": ml,
        "VL": vl,
        "CCL": ccl,
        "Urgent": urgent,
        "Emergency": emergency,
        "Total Absence": absence_total,
        "Absence %": round(absence_rate, 2),
        "Late": late_count
    })

comparison_df = pd.DataFrame(comparison_data)

st.dataframe(comparison_df, use_container_width=True)

# ==============================
# 👤 STAFF TABS
# ==============================
for i, person in enumerate(staff_names, start=1):

    with tabs[i]:

        st.markdown(f"## 👤 {person}")

        person_df = df[df["Name"] == person]

        ml, vl, ccl, urgent, emergency, absence_total = get_absence_breakdown(person_df)

        late_count = person_df["Leave Type"].str.contains("late", case=False).sum()

        absence_rate = (absence_total / max(calendar_days,1)) * 100

        # KPI
        c1, c2, c3, c4, c5, c6 = st.columns(6)

        c1.metric("🩺 ML", ml)
        c2.metric("🏖 VL", vl)
        c3.metric("👶 CCL", ccl)
        c4.metric("⚡ Urgent", urgent)
        c5.metric("🚨 Emergency", emergency)

        c6.metric(
            "🚫 Total Absence",
            f"{absence_total}",
            f"{absence_rate:.2f}%"
        )

        st.metric("⏰ Late Count", late_count)

        # Chart
        st.markdown("📊 Absence Breakdown")

        chart_df = pd.DataFrame({
            "Type": ["ML","VL","CCL","Urgent","Emergency"],
            "Count": [ml, vl, ccl, urgent, emergency]
        })

        fig = px.bar(chart_df, x="Type", y="Count", text="Count")
        fig.update_traces(textposition="outside")
        st.plotly_chart(fig, use_container_width=True)

        # Monthly
        st.markdown("📈 Monthly")

        temp = person_df.copy()
        temp["Month"] = temp["Date"].dt.to_period("M").astype(str)

        monthly = temp.groupby("Month").size().reset_index(name="Count")

        fig2 = px.bar(monthly, x="Month", y="Count", text="Count")
        st.plotly_chart(fig2, use_container_width=True)

        # Alerts
        st.markdown("🚨 Alerts")

        alerts = []

        if absence_rate > 40:
            alerts.append("🚫 High absence rate")

        if late_count > 10:
            alerts.append("⏰ High late frequency")

        if not alerts:
            st.success("✅ No issues")
        else:
            for a in alerts:
                st.warning(a)
