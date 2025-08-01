import sqlite3
from typing import List, Dict, Any
import streamlit as st


def init_user_settings_db(db):
    """Initialize the user settings database"""
    conn = sqlite3.connect(db, check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_settings (
            api_key TEXT,
            base_url TEXT,
            model TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    return conn

def save_user_settings(db, api_key, base_url, model):
    """Save user API settings to database"""
    conn = sqlite3.connect(database=db, check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR REPLACE INTO user_settings ( api_key, base_url, model, updated_at)
        VALUES (?, ?, ?, CURRENT_TIMESTAMP)
    ''', (api_key, base_url, model))
    conn.commit()
    conn.close()


def load_user_settings(db):
    """Load user API settings from database"""
    conn = sqlite3.connect(database=db, check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute('SELECT api_key, base_url, model FROM user_settings')
    result = cursor.fetchone()
    conn.close()
    if result:
        return {"api_key": result[0], "base_url": result[1], "model": result[2]}
    return {"api_key": "", "base_url": "", "model": ""}

def get_thread_ids(conn):
    if conn:
        try:
            cursor = conn.cursor()
            query = """
            SELECT DISTINCT thread_id
            FROM checkpoints
            ORDER BY thread_id DESC;
            """
            cursor.execute(query,)
            return [item[0] for item in cursor.fetchall()]
        except sqlite3.OperationalError: # Table might not exist yet
            return []
    return []

def load_messages_for_thread(thread_id: str, checkpointer) -> List[Dict[str, Any]]:
    if not thread_id or not checkpointer:
        return []

    agent_config = {"configurable": {"thread_id": st.session_state.thread_id}}
    state_data = checkpointer.get(config=agent_config)

    if state_data and "channel_values" in state_data and "messages" in state_data["channel_values"]:
        raw_messages = state_data["channel_values"]["messages"]
        return raw_messages
    return []