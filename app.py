import streamlit as st
import pandas as pd
import datetime
import uuid
import sqlite3

# Try to import OpenAI with error message
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    st.error("❌ `openai` package is not installed. Run: `pip install openai`")

st.set_page_config(page_title="ResolveAI Agent", layout="wide", page_icon="🤖")

# ===================== YOUR REAL GROK API KEY =====================
XAI_API_KEY = "xai-XhJMsLwDP1JyOTQeUobPJLnhoL8VowKxEmHL92qQOe43cPAOU3EXWz73K2a8uPZAxDXSppMKFtYhjXX3"

if OPENAI_AVAILABLE:
    client = OpenAI(
        api_key=XAI_API_KEY,
        base_url="https://api.x.ai/v1"
    )
    st.sidebar.success("✅ Real Grok AI Connected")
else:
    client = None

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
                    ai_solution TEXT)''')
    conn.commit()
    conn.close()

def save_ticket(entry):
    conn = sqlite3.connect("resolveai.db")
    conn.execute("""INSERT OR REPLACE INTO tickets 
                    VALUES (?,?,?,?,?,?,?,?,?)""",
                 (entry["ticket"], entry["user"], entry["email"], entry["text"],
                  entry["issue"], entry["priority"], entry["status"], entry["time"],
                  entry.get("ai_solution","")))
    conn.commit()
    conn.close()

def load_tickets():
    conn = sqlite3.connect("resolveai.db")
    df = pd.read_sql_query("SELECT * FROM tickets ORDER BY time DESC", conn)
    conn.close()
    return df

init_db()

# ===================== GROK AI FUNCTION =====================
def call_grok_agent(prompt):
    if not OPENAI_AVAILABLE:
        return "Please install openai package first: pip install openai"
    if not client:
        return "API not connected."

    try:
        response = client.chat.completions.create(
            model="grok-4",
            messages=[
                {"role": "system", "content": "You are a helpful, smart campus AI agent that solves student problems effectively."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=600
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error: {str(e)}"

# ===================== MAIN APP =====================
st.title("🤖 ResolveAI Agent - Real Grok AI")

tab1, tab2, tab3 = st.tabs(["💬 Chat with Agent", "📋 My Tickets", "🛠 Admin"])

with tab1:
    st.subheader("Describe Your Problem")
    
    col1, col2 = st.columns(2)
    with col1:
        user_id = st.text_input("Student ID *")
    with col2:
        email = st.text_input("Email *")

    problem = st.text_area("What is the problem?", height=150)

    if st.button("Send to Grok Agent", type="primary"):
        if user_id and email and problem:
            with st.spinner("Grok Agent is thinking..."):
                ai_response = call_grok_agent(problem)

            ticket = str(uuid.uuid4())[:8].upper()

            entry = {
                "ticket": ticket,
                "user": user_id,
                "email": email,
                "text": problem,
                "issue": "AI Processed",
                "priority": "Medium",
                "status": "In Progress",
                "time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
                "ai_solution": ai_response
            }
            save_ticket(entry)

            st.success(f"✅ Ticket Created: **{ticket}**")
            st.write("**Grok Agent Response:**")
            st.info(ai_response)
        else:
            st.error("Please fill all fields.")

with tab2:
    st.subheader("My Tickets")
    sid = st.text_input("Enter Student ID")
    if sid:
        df = load_tickets()
        my_tickets = df[df['user'] == sid]
        if not my_tickets.empty:
            st.dataframe(my_tickets, use_container_width=True)
        else:
            st.info("No tickets found.")

with tab3:
    st.subheader("Admin Panel")
    df = load_tickets()
    if not df.empty:
        st.dataframe(df, use_container_width=True)
    else:
        st.info("No tickets yet.")

st.caption("Real Grok AI Agent Running")
