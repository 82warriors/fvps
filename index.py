# ==========================
# KPI (IMPROVED)
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
