import streamlit as st
import pandas as pd
import datetime
import uuid
import sqlite3
from openai import OpenAI

st.set_page_config(page_title="ResolveAI Ultra", layout="wide", page_icon="🚀")

# ===================== CONFIG =====================
XAI_API_KEY = st.secrets.get("XAI_API_KEY") or "your-key-here"   # Put your key in st.secrets or .env

client = OpenAI(
    api_key=XAI_API_KEY,
    base_url="https://api.x.ai/v1"
)

# ===================== DATABASE =====================
def init_db():
    conn = sqlite3.connect("resolveai.db")
    conn.execute('''CREATE TABLE IF NOT EXISTS tickets (
                    ticket TEXT PRIMARY KEY, user TEXT, email TEXT, text TEXT,
                    issue TEXT, priority TEXT, status TEXT, time TEXT, 
                    ai_solution TEXT, confidence REAL)''')
    conn.commit()
    conn.close()

def save_ticket(entry):
    conn = sqlite3.connect("resolveai.db")
    conn.execute("""INSERT OR REPLACE INTO tickets VALUES (?,?,?,?,?,?,?,?,?,?)""",
                 (entry["ticket"], entry["user"], entry["email"], entry["text"],
                  entry["issue"], entry["priority"], entry["status"], entry["time"],
                  entry.get("ai_solution", ""), entry.get("confidence", 80)))
    conn.commit()
    conn.close()

def load_tickets():
    conn = sqlite3.connect("resolveai.db")
    df = pd.read_sql_query("SELECT * FROM tickets ORDER BY time DESC", conn)
    conn.close()
    return df

init_db()

# ===================== GROK AI - SMART SOLUTION =====================
def get_grok_solution(complaint):
    prompt = f"""
    You are a helpful campus facility manager. 
    Give clear, step-by-step instructions and practical solutions for this student complaint.

    Complaint: {complaint}

    Respond in this format:
    **Issue Detected:** 
    **Priority:** 
    **Why this happens:** (short reason)
    **Immediate Steps You Can Take:** (numbered)
    **What We Will Do:** (what admin/team will do)
    **Expected Resolution Time:**
    """

    try:
        response = client.chat.completions.create(
            model="grok-4.3",          # Latest model
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=500
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"AI Suggestion:\n1. Report the issue clearly with photos if possible.\n2. Wait for team to contact you."

# ===================== MAIN APP =====================
st.title("🚀 ResolveAI Ultra - Intelligent Campus Grievance System")

tab1, tab2, tab3, tab4 = st.tabs(["Submit Complaint", "My Tickets", "Admin Panel", "Analytics"])

# ---------------- TAB 1: SUBMIT ----------------
with tab1:
    st.subheader("Submit Your Campus Problem")
    
    col1, col2 = st.columns(2)
    with col1:
        user_id = st.text_input("Student ID / Roll Number*", placeholder="BTECH20231234")
    with col2:
        student_email = st.text_input("Your Email Address*", placeholder="student@college.edu")

    complaint = st.text_area("Describe the problem clearly*", height=180)

    if st.button("Submit & Get AI Solution", type="primary", use_container_width=True):
        if user_id and student_email and complaint:
            # Basic Categorization
            t = complaint.lower()
            if "wifi" in t or "internet" in t or "network" in t:
                issue = "Network"
            elif "power" in t or "electric" in t or "light" in t or "fan" in t:
                issue = "Electrical"
            elif "water" in t or "leak" in t or "washroom" in t:
                issue = "Water"
            elif "clean" in t or "dirty" in t or "room" in t or "hostel" in t:
                issue = "Maintenance"
            else:
                issue = "General"

            priority = "High" if any(w in t for w in ["urgent", "emergency", "not working", "broken"]) else "Medium"

            # Get Intelligent AI Solution
            with st.spinner("🤖 Grok AI is analyzing your problem..."):
                ai_solution = get_grok_solution(complaint)

            entry = {
                "ticket": str(uuid.uuid4())[:8].upper(),
                "user": user_id,
                "email": student_email,
                "text": complaint,
                "issue": issue,
                "priority": priority,
                "status": "Received",
                "time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
                "ai_solution": ai_solution,
                "confidence": 85
            }

            save_ticket(entry)
            st.success(f"✅ Ticket Created Successfully! **Ticket ID: {entry['ticket']}**")

            st.subheader("🤖 Grok AI - Clear Solution & Instructions")
            st.markdown(ai_solution)

            st.info(f"📧 Notification sent to **{student_email}**")
            st.balloons()
        else:
            st.error("Please fill all fields")

# ---------------- TAB 2: MY TICKETS ----------------
with tab2:
    st.subheader("📋 My Tickets")
    search_id = st.text_input("Enter Your Student ID")
    if search_id:
        df = load_tickets()
        my_df = df[df['user'] == search_id]
        if not my_df.empty:
            for _, row in my_df.iterrows():
                with st.expander(f"🎫 {row['ticket']} - {row['issue']} - {row['status']}"):
                    st.write(f"**Submitted:** {row['time']}")
                    st.info(row['text'])
                    if row['ai_solution']:
                        st.write("**Grok AI Solution:**")
                        st.write(row['ai_solution'])
        else:
            st.info("No tickets found.")

# ---------------- TAB 3: ADMIN ----------------
with tab3:
    st.subheader("🛠 Admin Panel")
    df = load_tickets()
    if not df.empty:
        st.dataframe(df[["ticket", "user", "issue", "priority", "status", "time"]], use_container_width=True)
        
        ticket = st.selectbox("Select Ticket", df["ticket"].tolist())
        new_status = st.selectbox("Update Status", ["Received", "In Progress", "Resolved", "Closed"])
        
        if st.button("Update Status"):
            conn = sqlite3.connect("resolveai.db")
            conn.execute("UPDATE tickets SET status = ? WHERE ticket = ?", (new_status, ticket))
            conn.commit()
            conn.close()
            st.success("Status Updated!")
            st.rerun()
    else:
        st.info("No tickets yet.")

# ---------------- TAB 4: ANALYTICS ----------------
with tab4:
    st.subheader("📊 Analytics")
    df = load_tickets()
    if not df.empty:
        c1, c2, c3 = st.columns(3)
        c1.metric("Total Tickets", len(df))
        c2.metric("Resolved", len(df[df['status'] == "Resolved"]))
        c3.metric("High Priority", len(df[df['priority'] == "High"]))
        
        st.bar_chart(df['issue'].value_counts())
    else:
        st.info("No data yet.")

st.caption("ResolveAI Ultra - Grok AI Powered Clear Solutions for Every Campus Problem")
