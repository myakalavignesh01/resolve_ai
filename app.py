import streamlit as st
import pandas as pd
import datetime
import uuid
import sqlite3
import os
from dotenv import load_dotenv
from textblob import TextBlob

# Load environment variables
load_dotenv()

st.set_page_config(page_title="ResolveAI Ultra", layout="wide", page_icon="🚀")

# ===================== DATABASE =====================
def init_db():
    conn = sqlite3.connect("resolveai.db")
    conn.execute('''CREATE TABLE IF NOT EXISTS tickets (
                    ticket TEXT PRIMARY KEY,
                    user TEXT,
                    text TEXT,
                    issue TEXT,
                    priority TEXT,
                    status TEXT,
                    time TEXT,
                    confidence REAL,
                    rating INTEGER)''')
    conn.commit()
    conn.close()

def save_ticket(entry):
    conn = sqlite3.connect("resolveai.db")
    conn.execute("""INSERT OR REPLACE INTO tickets 
                    (ticket, user, text, issue, priority, status, time, confidence, rating)
                    VALUES (?,?,?,?,?,?,?,?,?)""",
                 (entry["ticket"], entry["user"], entry["text"], entry["issue"],
                  entry["priority"], entry["status"], entry["time"], 
                  entry.get("confidence", 70), entry.get("rating")))
    conn.commit()
    conn.close()

def load_tickets():
    conn = sqlite3.connect("resolveai.db")
    df = pd.read_sql_query("SELECT * FROM tickets ORDER BY time DESC", conn)
    conn.close()
    return df

init_db()

# ===================== AI HELPERS =====================
def analyze_issue(text):
    t = text.lower()
    if any(word in t for word in ["wifi", "internet", "network", "speed"]):
        return "Network", "High", 88
    elif any(word in t for word in ["power", "electric", "light", "fan"]):
        return "Electrical", "High", 75
    elif any(word in t for word in ["water", "leak", "tap"]):
        return "Water", "Medium", 72
    elif any(word in t for word in ["clean", "dirty", "room", "hostel"]):
        return "Maintenance", "Medium", 65
    return "General", "Medium", 60

# ===================== SIDEBAR =====================
st.sidebar.title("⚙️ Settings")
language = st.sidebar.selectbox("Language", ["English", "Hindi"], index=0)
st.sidebar.caption("ResolveAI Ultra v2.0")

# ===================== MAIN APP =====================
st.title("🚀 ResolveAI Ultra - Smart Grievance System")

tab1, tab2, tab3, tab4 = st.tabs(["Submit Complaint", "My Tickets", "Admin Panel", "Analytics"])

# ------------------- TAB 1: SUBMIT -------------------
with tab1:
    st.subheader("Submit New Grievance")
    
    user_id = st.text_input("Your Student ID / Roll Number", placeholder="BTECH20231234")
    complaint = st.text_area("Describe your problem clearly", height=150)
    
    if st.button("Submit Complaint", type="primary", use_container_width=True):
        if user_id and complaint:
            issue, priority, confidence = analyze_issue(complaint)
            
            entry = {
                "ticket": str(uuid.uuid4())[:8].upper(),
                "user": user_id,
                "text": complaint,
                "issue": issue,
                "priority": priority,
                "status": "Received",
                "time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
                "confidence": confidence,
                "rating": None
            }
            
            save_ticket(entry)
            st.success(f"✅ Ticket Created Successfully! **Ticket ID: {entry['ticket']}**")
            st.info(f"**Issue Detected:** {issue} | **Priority:** {priority} | **AI Confidence:** {confidence}%")
            
            # Simple AI Suggestion
            st.write("**AI Suggested Actions:**")
            suggestions = {
                "Network": ["Restart router", "Check WiFi signal", "Clear cache"],
                "Electrical": ["Check MCB", "Report to electrician"],
                "Water": ["Check tank", "Report leak with photo"],
                "Maintenance": ["Maintenance team will visit soon"],
                "General": ["Forwarded to concerned department"]
            }
            for sug in suggestions.get(issue, ["Will be reviewed shortly"]):
                st.write(f"• {sug}")
        else:
            st.error("Please enter both Student ID and Complaint")

# ------------------- TAB 2: MY TICKETS -------------------
with tab2:
    st.subheader("📋 My Tickets")
    user_id_input = st.text_input("Enter your Student ID to see your tickets", key="user_check")
    
    if user_id_input:
        df = load_tickets()
        my_df = df[df['user'] == user_id_input]
        if not my_df.empty:
            st.dataframe(my_df[["ticket", "issue", "status", "priority", "time"]], use_container_width=True)
        else:
            st.info("No tickets found for this ID.")

# ------------------- TAB 3: ADMIN -------------------
with tab3:
    st.subheader("🛠 Admin Dashboard")
    df = load_tickets()
    if not df.empty:
        st.dataframe(df, use_container_width=True)
        
        ticket_to_update = st.selectbox("Select Ticket to Update", df["ticket"].tolist())
        new_status = st.selectbox("New Status", ["Received", "In Progress", "Resolved", "Closed"])
        
        if st.button("Update Status"):
            conn = sqlite3.connect("resolveai.db")
            conn.execute("UPDATE tickets SET status = ? WHERE ticket = ?", (new_status, ticket_to_update))
            conn.commit()
            conn.close()
            st.success("Status Updated!")
            st.rerun()
    else:
        st.info("No tickets yet.")

# ------------------- TAB 4: ANALYTICS -------------------
with tab4:
    st.subheader("📊 Analytics")
    df = load_tickets()
    if not df.empty:
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Tickets", len(df))
        col2.metric("Resolved", len(df[df['status'] == "Resolved"]))
        col3.metric("Avg Confidence", f"{df['confidence'].mean():.1f}%")
        
        st.bar_chart(df['issue'].value_counts())
        st.bar_chart(df['status'].value_counts())
    else:
        st.info("No data available yet.")

st.caption("Made with ❤️ for Hackathon | ResolveAI Ultra")
