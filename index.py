from pathlib import Path
import base64

# ==============================
# LOGO PATH (SAFE LOAD)
# ==============================
logo_path = Path(__file__).parent / "logo.png"

# Convert logo to base64 (for page icon)
def get_base64_image(path):
    if path.exists():
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    return None

logo_base64 = get_base64_image(logo_path)

# ==============================
# PAGE CONFIG (USE LOGO)
# ==============================
st.set_page_config(
    page_title="Attendance Tracking",
    page_icon=logo_path if logo_path.exists() else "🔴",
    layout="wide"
)

# ==============================
# HEADER (LOGO + TITLE)
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
