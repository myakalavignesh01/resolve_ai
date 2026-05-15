import streamlit as st
import pandas as pd
import datetime
import uuid
import sqlite3
from openai import OpenAI

st.set_page_config(page_title="ResolveAI Agent", layout="wide", page_icon="🤖")

# ===================== YOUR REAL GROK API KEY =====================
XAI_API_KEY = "xai-XhJMsLwDP1JyOTQeUobPJLnhoL8VowKxEmHL92qQOe43cPAOU3EXWz73K2a8uPZAxDXSppMKFtYhjXX3"

client = OpenAI(
    api_key=XAI_API_KEY,
    base_url="https://api.x.ai/v1"
)

st.sidebar.success("✅ Connected to Real Grok AI")

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
                    ai_solution TEXT,
                    conversation TEXT)''')
    conn.commit()
    conn.close()

def save_ticket(entry):
    conn = sqlite3.connect("resolveai.db")
    conn.execute("""INSERT OR REPLACE INTO tickets 
                    VALUES (?,?,?,?,?,?,?,?,?,?)""",
                 (entry["ticket"], entry["user"], entry["email"], entry["text"],
                  entry["issue"], entry["priority"], entry["status"], entry["time"],
                  entry.get("ai_solution",""), str(entry.get("conversation",[]))))
    conn.commit()
    conn.close()

def load_tickets():
    conn = sqlite3.connect("resolveai.db")
    df = pd.read_sql_query("SELECT * FROM tickets ORDER BY time DESC", conn)
    conn.close()
    return df

init_db()

# ===================== REAL GROK AI AGENT =====================
def call_grok_agent(prompt, history=[]):
    messages = [{"role": "system", "content": """You are ResolveAI Agent, a smart, friendly, and proactive campus problem solver.
    Solve real issues like WiFi, electricity, water, cleanliness, maintenance, etc. Give clear step-by-step solutions."""}]
    
    for msg in history:
        messages.append(msg)
    
    messages.append({"role": "user", "content": prompt})

    try:
        response = client.chat.completions.create(
            model="grok-4",           # Using latest model
            messages=messages,
            temperature=0.7,
            max_tokens=700
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error: {str(e)}"

# ===================== MAIN APP =====================
st.title("🤖 ResolveAI Agent - Real Grok AI Campus Solver")

tab1, tab2, tab3 = st.tabs(["💬 Chat with Agent", "📋 My Tickets", "🛠 Admin"])

with tab1:
    st.subheader("Describe Your Problem")
    
    col1, col2 = st.columns(2)
    with col1:
        user_id = st.text_input("Student ID *", key="u_id")
    with col2:
        email = st.text_input("Email *", key="u_email")

    if "messages" not in st.session_state:
        st.session_state.messages = []

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("Type your issue here..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Grok Agent is working..."):
                response = call_grok_agent(prompt, st.session_state.messages[:-1])
                st.markdown(response)
        
        st.session_state.messages.append({"role": "assistant", "content": response})

        # Auto Save Ticket
        if len(st.session_state.messages) <= 3 and user_id and email:
            ticket_id = str(uuid.uuid4())[:8].upper()
            entry = {
                "ticket": ticket_id,
                "user": user_id,
                "email": email,
                "text": prompt,
                "issue": "AI Processed",
                "priority": "Medium",
                "status": "In Progress",
                "time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
                "ai_solution": response,
                "conversation": st.session_state.messages
            }
            save_ticket(entry)
            st.toast(f"Ticket Created: **{ticket_id}**", icon="✅")

with tab2:
    st.subheader("My Tickets")
    sid = st.text_input("Enter Student ID")
    if sid:
        df = load_tickets()
        mine = df[df['user'] == sid]
        if not mine.empty:
            st.dataframe(mine[["ticket","issue","status","time"]], use_container_width=True)
        else:
            st.info("No tickets found.")

with tab3:
    st.subheader("Admin Panel")
    df = load_tickets()
    if not df.empty:
        st.dataframe(df, use_container_width=True)

st.caption("Real Grok AI Agent Running | Your Key is Active")
