import streamlit as st
import pandas as pd
import plotly.express as px
from streamlit_autorefresh import st_autorefresh
from datetime import datetime
from pathlib import Path

# ==============================
# CONFIG
# ==============================
SHEET_ID = "1TZcv_U-U7R9OM98AEMzZ2gvu2Ca6ddqd3yCCxXsTvhE"
staff1_name = "Amira"
staff2_name = "Idham"

# ==============================
# LOGO (LOAD FIRST)
# ==============================
logo_path = Path(__file__).parent / "logo.png"

# ==============================
# PAGE CONFIG (MUST BE FIRST ST COMMAND)
# ==============================
st.set_page_config(
    page_title="Attendance Tracking",
    page_icon=str(logo_path) if logo_path.exists() else "🔴",
    layout="wide"
)

# ==============================
# HIDE STREAMLIT DEFAULT UI
# ==============================
st.markdown("""
<style>
header {visibility: hidden;}
[data-testid="stHeader"] {display: none;}
[data-testid="stToolbar"] {display: none;}
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
.block-container {padding-top: 1rem;}
</style>
""", unsafe_allow_html=True)

# ==============================
# HEADER
# ==============================
col1, col2 = st.columns([1.2, 10])

with col1:
    if logo_path.exists():
        st.image(logo_path, width=70)
    else:
        st.write("🔴")

with col2:
    st.markdown("""
    <h1 style='margin-bottom:0;'>Attendance Tracking</h1>
    <p style='color:gray;margin-top:0;'>Real-time monitoring system</p>
    """, unsafe_allow_html=True)

st.divider()

# ==============================
# AUTO REFRESH
# ==============================
st_autorefresh(interval=30000, key="refresh")

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
# DATA TRANSFORMATION
# ==============================
df_raw = df_raw.dropna(how="all").reset_index(drop=True)

df1 = df_raw.iloc[:, 0:6].copy()
df2 = df_raw.iloc[:, 7:13].copy()

df1.columns = ["Date","Day","Leave Type","Reason","Late","Relief"]
df2.columns = ["Date","Day","Leave Type","Reason","Late","Relief"]

df1["Name"] = staff1_name
df2["Name"] = staff2_name

df = pd.concat([df1, df2])

df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
df = df.dropna(subset=["Date"])

start_date = pd.to_datetime("2024-12-30")
df = df[df["Date"] >= start_date]

df["Leave Type"] = df["Leave Type"].astype(str).str.strip().str.lower()

today = pd.Timestamp.today().normalize()
calendar_days = (today - start_date).days + 1

# ==============================
# ABSENCE FUNCTION
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
# SUMMARY TAB
# ==============================
with tabs[0]:

    st.markdown("## 🟢 Today Status")
    today_df = df[df["Date"] == today]

    if today_df.empty:
        st.success("✅ Everyone Present")
    else:
        st.dataframe(today_df, use_container_width=True)

    st.markdown("## 📊 Summary")

    ml, vl, ccl, urgent, emergency, absence_total = get_absence_breakdown(df)
    late_count = df["Leave Type"].str.contains("late", case=False).sum()
    absence_rate = (absence_total / max(calendar_days,1)) * 100

    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric("ML", ml)
    c2.metric("VL", vl)
    c3.metric("CCL", ccl)
    c4.metric("Urgent", urgent)
    c5.metric("Emergency", emergency)
    c6.metric("Total Absence", f"{absence_total} ({absence_rate:.2f}%)")

    st.metric("Late Count", late_count)

    # ==============================
    # COMPARISON CHART
    # ==============================
    st.markdown("## 📊 Total Absence Comparison")

    comparison_data = []
    for person in staff_names:
        person_df = df[df["Name"] == person]
        _, _, _, _, _, total_abs = get_absence_breakdown(person_df)
        comparison_data.append({"Name": person, "Total Absence": total_abs})

    comparison_df = pd.DataFrame(comparison_data)

    fig = px.bar(
        comparison_df,
        x="Name",
        y="Total Absence",
        text="Total Absence",
        color="Name"
    )

    fig.update_traces(textposition="outside")
    fig.update_layout(
        showlegend=False,
        yaxis_title="Absences",
        xaxis_title="Staff"
    )

    st.plotly_chart(fig, use_container_width=True)

# ==================================================
# 👤 STAFF TABS
# ==================================================
for i, person in enumerate(staff_names, start=1):

    with tabs[i]:

        st.markdown(f"### 👤 {person}")

        person_df = df[df["Name"] == person]

        ml, vl, ccl, urgent, emergency, absence_total = get_absence_breakdown(person_df)
        late_count = person_df["Leave Type"].str.contains("late", case=False).sum()

        absence_rate = (absence_total / max(calendar_days,1)) * 100

        c1, c2, c3, c4, c5, c6 = st.columns(6)
        c1.metric("ML", ml)
        c2.metric("VL", vl)
        c3.metric("CCL", ccl)
        c4.metric("Urgent", urgent)
        c5.metric("Emergency", emergency)
        c6.metric("Total Absence", f"{absence_total} ({absence_rate:.2f}%)")

        st.metric("Late Count", late_count)

        # Monthly Chart
        st.markdown("### 📈 Monthly")

        temp = person_df.copy()
        temp["Month"] = temp["Date"].dt.to_period("M").dt.to_timestamp()

        monthly = temp.groupby("Month").size().reset_index(name="Count")

        full_range = pd.date_range(start=start_date, end=today, freq="MS")
        full_df = pd.DataFrame({"Month": full_range})

        monthly = full_df.merge(monthly, on="Month", how="left").fillna(0)
        monthly["Month_str"] = monthly["Month"].dt.strftime("%b %Y")

        fig = px.bar(monthly, x="Month_str", y="Count", text="Count")

        fig.update_traces(textposition="outside")
        fig.update_layout(xaxis_tickangle=-45)

        st.plotly_chart(fig, use_container_width=True)
