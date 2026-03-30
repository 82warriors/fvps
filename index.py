uploaded_file = st.file_uploader("Upload Excel File", type=["xlsx"])

if uploaded_file:
    # 🔥 KEY FIX: force correct header row
    df = pd.read_excel(uploaded_file, header=0)

    st.subheader("🔍 Raw Data")
    st.dataframe(df)

    # ==============================
    # SAFE COLUMN CLEANING
    # ==============================

    # Convert ALL columns safely
    df.columns = [str(col).strip() for col in df.columns]

    # Remove empty / unnamed columns
    df = df.loc[:, df.columns != ""]
    df = df.loc[:, ~pd.Series(df.columns).str.contains("Unnamed", case=False)]

    # DEBUG (keep this for now)
    st.write("Columns detected:", df.columns.tolist())
