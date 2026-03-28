
import streamlit as st
import pandas as pd

st.set_page_config(page_title="CampusAI", layout="wide")

# ---- STYLE ----
st.markdown("""
<style>
body {background:#0f172a;color:white;}
.card {background:#1e293b;padding:20px;border-radius:15px;margin-bottom:15px;}
</style>
""", unsafe_allow_html=True)

st.title("🎓 CampusAI - Predictive Grievance System")

if "history" not in st.session_state:
    st.session_state.history = []

# ---- FUNCTIONS ----
def analyze(text):
    t = text.lower()
    if "wifi" in t:
        return "Network Issue"
    elif "heat" in t or "hot" in t:
        return "Heat Problem"
    elif "water" in t:
        return "Water Issue"
    elif "electric" in t:
        return "Electrical Issue"
    else:
        return "General Issue"

def predict(history):
    wifi = sum("wifi" in h.lower() for h in history)
    if wifi >= 3:
        return "⚠️ Possible WiFi outage soon"
    return "✅ No major prediction"

def solution(issue):
    return {
        "Network Issue": "Restart router or contact IT",
        "Heat Problem": "Check ventilation / AC",
        "Water Issue": "Inform maintenance",
        "Electrical Issue": "Check power supply",
        "General Issue": "Forward to admin"
    }.get(issue)

# ---- INPUT ----
col1, col2 = st.columns([2,1])

with col1:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    text = st.text_area("Enter your issue")

    if st.button("Analyze"):
        if text:
            st.session_state.history.append(text)
            issue = analyze(text)
            st.success(f"Issue: {issue}")
            st.info(f"Solution: {solution(issue)}")
            st.warning(predict(st.session_state.history))
    st.markdown('</div>', unsafe_allow_html=True)

# ---- HEATMAP ----
with col2:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("📊 Issue Zones")

    data = pd.DataFrame({
        "Area": ["Hostel", "Library", "Block A"],
        "Count": [
            sum("hostel" in h.lower() for h in st.session_state.history),
            sum("library" in h.lower() for h in st.session_state.history),
            sum("block" in h.lower() for h in st.session_state.history),
        ]
    })

    st.bar_chart(data.set_index("Area"))
    st.markdown('</div>', unsafe_allow_html=True)

# ---- HISTORY ----
st.markdown('<div class="card">', unsafe_allow_html=True)
st.subheader("📜 History")

for h in st.session_state.history[::-1]:
    st.write("-", h)

st.markdown('</div>', unsafe_allow_html=True)

st.caption("Built for Hackathon 🚀")
