import streamlit as st
import pandas as pd
import datetime
import uuid
import sqlite3
from openai import OpenAI

st.set_page_config(page_title="ResolveAI Agent", layout="wide", page_icon="🤖")

# ===================== CONFIG =====================
XAI_API_KEY = st.secrets.get("XAI_API_KEY")  # Put your key in .streamlit/secrets.toml

if XAI_API_KEY:
    client = OpenAI(api_key=XAI_API_KEY, base_url="https://api.x.ai/v1")
else:
    client = None
    st.sidebar.warning("⚠️ Grok API key not configured. Running in demo mode.")

# ===================== DATABASE =====================
def init_db():
    conn = sqlite3.connect("resolveai.db")
    conn.execute('''CREATE TABLE IF NOT EXISTS tickets (
                    ticket TEXT PRIMARY KEY, user TEXT, email TEXT, text TEXT,
                    issue TEXT, priority TEXT, status TEXT, time TEXT,
                    ai_solution TEXT, conversation TEXT, resolution_notes TEXT)''')
    conn.commit()
    conn.close()

def save_ticket(entry):
    conn = sqlite3.connect("resolveai.db")
    conn.execute("""INSERT OR REPLACE INTO tickets VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
                 (entry["ticket"], entry["user"], entry["email"], entry["text"],
                  entry["issue"], entry["priority"], entry["status"], entry["time"],
                  entry.get("ai_solution",""), entry.get("conversation",""), entry.get("resolution_notes","")))
    conn.commit()
    conn.close()

def load_tickets():
    conn = sqlite3.connect("resolveai.db")
    df = pd.read_sql_query("SELECT * FROM tickets ORDER BY time DESC", conn)
    conn.close()
    return df

init_db()

# ===================== AI AGENT =====================
def ai_agent_response(user_message, conversation_history="", ticket_context=""):
    prompt = f"""
    You are ResolveAI Agent - an intelligent, helpful, and proactive campus problem-solving agent.
    Be friendly, professional, and solution-oriented.

    Previous Conversation:
    {conversation_history}

    Current Ticket Context: {ticket_context}

    Student: {user_message}

    Respond naturally. Ask clarifying questions if needed. Give clear actionable steps.
    If you have enough information, provide a complete solution.
    """

    if not client:
        return "Thank you for reporting. Our team will look into it shortly."

    try:
        response = client.chat.completions.create(
            model="grok-4",
            messages=[{"role": "system", "content": prompt}],
            temperature=0.7,
            max_tokens=500
        )
        return response.choices[0].message.content
    except:
        return "I'm here to help! Can you tell me more details about the issue?"

# ===================== MAIN INTERFACE =====================
st.title("🤖 ResolveAI Agent - Your Campus Problem Solver")

tab1, tab2, tab3 = st.tabs(["💬 Talk to AI Agent", "📋 My Tickets", "🛠 Admin"])

# ------------------- AI AGENT CHAT -------------------
with tab1:
    st.subheader("Talk to ResolveAI Agent")
    
    col1, col2 = st.columns(2)
    with col1:
        user_id = st.text_input("Student ID", placeholder="BTECH20231234", key="agent_user")
    with col2:
        email = st.text_input("Your Email", placeholder="student@college.edu", key="agent_email")

    if "agent_ticket" not in st.session_state:
        st.session_state.agent_ticket = None
        st.session_state.conversation = []

    # Start New Issue
    issue_desc = st.text_area("Describe your campus issue", height=120, key="initial_issue")

    if st.button("Start Conversation with Agent", type="primary"):
        if user_id and email and issue_desc:
            ticket = str(uuid.uuid4())[:8].upper()
            
            entry = {
                "ticket": ticket,
                "user": user_id,
                "email": email,
                "text": issue_desc,
                "issue": "Under Analysis",
                "priority": "Medium",
                "status": "In Progress",
                "time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
                "ai_solution": "",
                "conversation": issue_desc,
                "resolution_notes": ""
            }
            save_ticket(entry)
            st.session_state.agent_ticket = ticket
            st.session_state.conversation = [{"role": "user", "content": issue_desc}]
            st.success(f"Agent Activated! Ticket ID: **{ticket}**")
            st.rerun()

    # Chat Interface
    if st.session_state.agent_ticket:
        st.info(f"Chatting with Agent for Ticket: **{st.session_state.agent_ticket}**")
        
        # Display conversation
        for msg in st.session_state.conversation:
            if msg["role"] == "user":
                st.chat_message("user").write(msg["content"])
            else:
                st.chat_message("assistant").write(msg["content"])

        # User input
        user_input = st.chat_input("Type your message here...")
        if user_input:
            st.session_state.conversation.append({"role": "user", "content": user_input})
            
            with st.spinner("Agent is thinking..."):
                context = f"Ticket: {st.session_state.agent_ticket}"
                response = ai_agent_response(user_input, str(st.session_state.conversation), context)
            
            st.session_state.conversation.append({"role": "assistant", "content": response})
            st.rerun()

# ------------------- MY TICKETS -------------------
with tab2:
    st.subheader("My Tickets")
    sid = st.text_input("Enter Student ID")
    if sid:
        df = load_tickets()
        my_tickets = df[df['user'] == sid]
        if not my_tickets.empty:
            for _, row in my_tickets.iterrows():
                with st.expander(f"🎫 {row['ticket']} - {row['status']}"):
                    st.write(row['text'])
                    if row['ai_solution'] or row['conversation']:
                        st.write("**Agent Conversation:**")
                        st.write(row['conversation'] if row['conversation'] else row['ai_solution'])

# ------------------- ADMIN -------------------
with tab3:
    st.subheader("Admin Resolution Center")
    df = load_tickets()
    if not df.empty:
        st.dataframe(df[["ticket", "user", "issue", "status", "time"]], use_container_width=True)
        
        selected = st.selectbox("Select Ticket", df["ticket"])
        new_status = st.selectbox("Status", ["In Progress", "Resolved", "Closed"])
        notes = st.text_area("Resolution Notes")
        
        if st.button("Update Ticket"):
            conn = sqlite3.connect("resolveai.db")
            conn.execute("UPDATE tickets SET status=?, resolution_notes=? WHERE ticket=?", 
                        (new_status, notes, selected))
            conn.commit()
            conn.close()
            st.success("Updated!")
            st.rerun()

st.caption("🤖 ResolveAI Agent - Intelligent Campus Problem Solver")
