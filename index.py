import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Absence Dashboard", layout="wide")

st.title("📊 DE Absence Analytics System")

# ==============================
# FILE UPLOAD
# ==============================
uploaded_file = st.file_uploader("Upload Excel File", type=["xlsx"])

if uploaded_file:
    df = pd.read_excel(uploaded_file)

    st.subheader("🔍 Raw Data")
    st.dataframe(df)

    # ==============================
    # DATA CLEANING
    # ==============================
    df.columns = df.columns.str.strip()

    # Example assumptions (adjust if needed)
    if "Start Date" in df.columns and "End Date" in df.columns:
        df["Start Date"] = pd.to_datetime(df["Start Date"], errors='coerce')
        df["End Date"] = pd.to_datetime(df["End Date"], errors='coerce')
        df["Duration"] = (df["End Date"] - df["Start Date"]).dt.days + 1

    if "Start Date" in df.columns:
        df["Month"] = df["Start Date"].dt.month_name()
        df["Week"] = df["Start Date"].dt.isocalendar().week

    # ==============================
    # SIDEBAR FILTERS
    # ==============================
    st.sidebar.header("🔎 Filters")

    if "Name" in df.columns:
        name_filter = st.sidebar.multiselect(
            "Select Staff",
            options=df["Name"].dropna().unique(),
            default=df["Name"].dropna().unique()
        )
        df = df[df["Name"].isin(name_filter)]

    if "Leave Type" in df.columns:
        leave_filter = st.sidebar.multiselect(
            "Leave Type",
            options=df["Leave Type"].dropna().unique(),
            default=df["Leave Type"].dropna().unique()
        )
        df = df[df["Leave Type"].isin(leave_filter)]

    # ==============================
    # KPI METRICS
    # ==============================
    col1, col2, col3 = st.columns(3)

    total_absence = len(df)
    total_days = df["Duration"].sum() if "Duration" in df.columns else 0
    unique_staff = df["Name"].nunique() if "Name" in df.columns else 0

    col1.metric("Total Records", total_absence)
    col2.metric("Total Days Absent", total_days)
    col3.metric("No. of Staff", unique_staff)

    # ==============================
    # CHARTS
    # ==============================
    st.subheader("📈 Absence Trends")

    if "Month" in df.columns:
        month_chart = df.groupby("Month").size().reset_index(name="Count")
        fig1 = px.bar(month_chart, x="Month", y="Count", title="Absence by Month")
        st.plotly_chart(fig1, use_container_width=True)

    if "Leave Type" in df.columns:
        leave_chart = df["Leave Type"].value_counts().reset_index()
        leave_chart.columns = ["Leave Type", "Count"]
        fig2 = px.pie(leave_chart, names="Leave Type", values="Count", title="Leave Distribution")
        st.plotly_chart(fig2, use_container_width=True)

    if "Name" in df.columns:
        staff_chart = df["Name"].value_counts().head(10).reset_index()
        staff_chart.columns = ["Name", "Count"]
        fig3 = px.bar(staff_chart, x="Name", y="Count", title="Top 10 Absences")
        st.plotly_chart(fig3, use_container_width=True)

    # ==============================
    # TABLE VIEW
    # ==============================
    st.subheader("📋 Processed Data")
    st.dataframe(df)

else:
    st.info("👆 Upload your DE Absence.xlsx file to start")
