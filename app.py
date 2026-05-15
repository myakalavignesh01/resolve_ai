import streamlit as st
import pandas as pd
import datetime
import uuid
import sqlite3

st.set_page_config(page_title="ResolveAI Ultra", layout="wide", page_icon="🚀")

# ===================== DATABASE =====================
def init_db():
    conn = sqlite3.connect("resolveai.db")
    conn.execute('''CREATE TABLE IF NOT EXISTS tickets (
                    ticket TEXT PRIMARY KEY,
                    user TEXT,
                    email TEXT,
                    text TEXT,
                    issue TEXT,
                    priority TEXT,
                    status TEXT,
                    time TEXT,
                    confidence REAL)''')
    conn.commit()
    conn.close()

def save_ticket(entry):
    conn = sqlite3.connect("resolveai.db")
    conn.execute("""INSERT OR REPLACE INTO tickets 
                    VALUES (?,?,?,?,?,?,?,?,?)""",
                 (entry["ticket"], entry["user"], entry["email"], entry["text"],
                  entry["issue"], entry["priority"], entry["status"], 
                  entry["time"], entry.get("confidence", 82)))
    conn.commit()
    conn.close()

def load_tickets():
    conn = sqlite3.connect("resolveai.db")
    df = pd.read_sql_query("SELECT * FROM tickets ORDER BY time DESC", conn)
    conn.close()
    return df

init_db()

# Initialize session state
if "tickets" not in st.session_state:
    st.session_state.tickets = load_tickets()

# ===================== MAIN APP =====================
st.title("🚀 ResolveAI Ultra - Smart Grievance System")

tab1, tab2, tab3, tab4 = st.tabs(["Submit Complaint", "My Tickets", "Admin Panel", "Analytics"])

# ---------------- TAB 1: SUBMIT ----------------
with tab1:
    st.subheader("Submit New Grievance")
    
    col1, col2 = st.columns(2)
    with col1:
        user_id = st.text_input("Student ID / Roll Number*", key="user_id")
    with col2:
        student_email = st.text_input("Student Email Address*", key="student_email")

    complaint = st.text_area("Describe your problem in detail*", height=180, key="complaint")

    if st.button("Submit Complaint", type="primary", use_container_width=True):
        if user_id and student_email and complaint:
            t = complaint.lower()
            if "wifi" in t or "internet" in t:
                issue = "Network"
            elif "power" in t or "electric" in t:
                issue = "Electrical"
            elif "water" in t:
                issue = "Water"
            elif "clean" in t or "dirty" in t or "room" in t:
                issue = "Maintenance"
            else:
                issue = "General"

            priority = "High" if any(word in t for word in ["urgent", "emergency", "not working"]) else "Medium"

            entry = {
                "ticket": str(uuid.uuid4())[:8].upper(),
                "user": user_id,
                "email": student_email,
                "text": complaint,
                "issue": issue,
                "priority": priority,
                "status": "Received",
                "time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
                "confidence": 82
            }

            save_ticket(entry)
            st.success(f"✅ Ticket Created Successfully! **Ticket ID: {entry['ticket']}**")
            
            # Refresh data
            st.session_state.tickets = load_tickets()
            st.rerun()
        else:
            st.error("All fields are required!")

# ---------------- TAB 2: MY TICKETS ----------------
with tab2:
    st.subheader("📋 My Tickets")
    search_id = st.text_input("Enter Your Student ID", key="search_id")
    if search_id:
        df = st.session_state.tickets
        my_df = df[df['user'] == search_id]
        if not my_df.empty:
            st.dataframe(my_df, use_container_width=True)
        else:
            st.info("No tickets found.")

# ---------------- TAB 3: ADMIN ----------------
with tab3:
    st.subheader("🛠 Admin Panel")
    df = st.session_state.tickets
    
    if not df.empty:
        st.dataframe(df, use_container_width=True)
        
        col1, col2 = st.columns([3, 1])
        with col1:
            ticket = st.selectbox("Select Ticket", df["ticket"].tolist())
        with col2:
            new_status = st.selectbox("New Status", ["Received", "In Progress", "Resolved", "Closed"])
        
        if st.button("Update Status", type="primary"):
            conn = sqlite3.connect("resolveai.db")
            conn.execute("UPDATE tickets SET status = ? WHERE ticket = ?", (new_status, ticket))
            conn.commit()
            conn.close()
            
            st.success("✅ Status Updated!")
            st.session_state.tickets = load_tickets()   # Refresh
            st.rerun()
    else:
        st.info("No tickets yet.")

# ---------------- TAB 4: ANALYTICS ----------------
with tab4:
    st.subheader("📊 Analytics")
    df = st.session_state.tickets
    if not df.empty:
        c1, c2, c3 = st.columns(3)
        c1.metric("Total Tickets", len(df))
        c2.metric("Resolved", len(df[df['status'] == "Resolved"]))
        c3.metric("High Priority", len(df[df['priority'] == "High"]))
        
        st.bar_chart(df['issue'].value_counts())                        
        st.bar_chart(df['status'].value_counts())
    else:
        st.info("No data yet. Submit some complaints.")

