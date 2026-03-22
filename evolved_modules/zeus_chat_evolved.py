# The Zeus Project 2026 — Francois Nel
# ZEUS EVOLVED MODULE: zeus_chat.py
# Evolution timestamp: 2026-03-21T00:51:10.050325
# Gaps addressed: 13
# Code hash: cfe82a7287507004
# ─────────────────────────────────────────────────────

# The Zeus Project 2026 — Francois Nel

import os, sqlite3, re, logging, time, uuid
from datetime import datetime, timezone
from flask import Blueprint, request, jsonify
import requests

log = logging.getLogger("Zeus.Chat")
ZEUS_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH  = os.path.join(ZEUS_DIR, "zeus.db")
chat_bp  = Blueprint("chat", __name__)

# GAP_FILLED: missing_error_handling for database connection failures in _db function
def _db():
    """
    Establish a connection to the SQLite database.

    Returns:
        conn (sqlite3.Connection): The database connection object.
    """
    try:
        conn = sqlite3.connect(DB_PATH, timeout=10)
        conn.row_factory = sqlite3.Row
        return conn
    except sqlite3.Error as e:
        log.error(f"Database connection failed: {e}")
        return None

# GAP_FILLED: missing_error_handling for database query execution failures in _ensure_tables function
def _ensure_tables():
    """
    Create the necessary tables in the database if they do not exist.

    Returns:
        None
    """
    conn = _db()
    if conn:
        try:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS chat_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    confidence REAL DEFAULT 1.0,
                    provider TEXT DEFAULT 'groq',
                    web_used INTEGER DEFAULT 0,
                    created_at TEXT DEFAULT (datetime('now'))
                );
                CREATE TABLE IF NOT EXISTS chat_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT UNIQUE NOT NULL,
                    title TEXT DEFAULT 'New Chat',
                    created_at TEXT DEFAULT (datetime('now')),
                    updated_at TEXT DEFAULT (datetime('now'))
                );
                CREATE TABLE IF NOT EXISTS knowledge (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    topic TEXT NOT NULL,
                    content TEXT NOT NULL,
                    created_at TEXT DEFAULT (datetime('now'))
                );
            """)
            conn.commit()
        except sqlite3.Error as e:
            log.error(f"Database query execution failed: {e}")
        finally:
            conn.close()

# GAP_FILLED: missing_validation for user input in chat_send function
def _validate_input(input_str):
    """
    Validate the user input to prevent malicious input.

    Args:
        input_str (str): The user input string.

    Returns:
        bool: True if the input is valid, False otherwise.
    """
    if not input_str:
        log.warning("Empty input received")
        return False
    if len(input_str) > 1000:
        log.warning("Input too long")
        return False
    return True

# GAP_FILLED: missing_error_handling for Groq or Claude API failures
def _groq_api_request(prompt):
    """
    Send a request to the Groq API.

    Args:
        prompt (str): The input prompt.

    Returns:
        response (dict): The API response.
    """
    try:
        response = requests.post("https://api.groq.com/v1/completion", json={"prompt": prompt})
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        log.error(f"Groq API request failed: {e}")
        return None

# GAP_FILLED: missing_error_handling for DuckDuckGo API failures
def _duckduckgo_api_request(prompt):
    """
    Send a request to the DuckDuckGo API.

    Args:
        prompt (str): The input prompt.

    Returns:
        response (dict): The API response.
    """
    try:
        response = requests.get(f"https://api.duckduckgo.com/?q={prompt}&format=json")
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        log.error(f"DuckDuckGo API request failed: {e}")
        return None

# GAP_FILLED: security - Potential SQL injection vulnerability in _db function
def _execute_query(conn, query, params):
    """
    Execute a SQL query with parameters to prevent SQL injection.

    Args:
        conn (sqlite3.Connection): The database connection object.
        query (str): The SQL query.
        params (tuple): The query parameters.

    Returns:
        results (list): The query results.
    """
    try:
        cursor = conn.cursor()
        cursor.execute(query, params)
        results = cursor.fetchall()
        return results
    except sqlite3.Error as e:
        log.error(f"Database query execution failed: {e}")
        return None

# GAP_FILLED: missing_capability - No support for multiple chat sessions per user
def _create_session(user_id, title):
    """
    Create a new chat session for a user.

    Args:
        user_id (str): The user ID.
        title (str): The session title.

    Returns:
        session_id (str): The session ID.
    """
    conn = _db()
    if conn:
        try:
            session_id = str(uuid.uuid4())
            query = "INSERT INTO chat_sessions (session_id, title, user_id) VALUES (?, ?, ?)"
            params = (session_id, title, user_id)
            _execute_query(conn, query, params)
            conn.commit()
            return session_id
        except sqlite3.Error as e:
            log.error(f"Database query execution failed: {e}")
        finally:
            conn.close()
    return None

# GAP_FILLED: missing_logging - No logging for chat history and sessions
def _log_chat_history(session_id, role, content):
    """
    Log the chat history.

    Args:
        session_id (str): The session ID.
        role (str): The role (user or assistant).
        content (str): The chat content.

    Returns:
        None
    """
    log.info(f"Chat history: session_id={session_id}, role={role}, content={content}")

def _log_session_created(session_id, title):
    """
    Log the creation of a new chat session.

    Args:
        session_id (str): The session ID.
        title (str): The session title.

    Returns:
        None
    """
    log.info(f"Session created: session_id={session_id}, title={title}")

# GAP_FILLED: incomplete_implementation - The _ensure_tables function only creates the chat_history table
def _create_knowledge_table():
    """
    Create the knowledge table if it does not exist.

    Returns:
        None
    """
    conn = _db()
    if conn:
        try:
            query = "CREATE TABLE IF NOT EXISTS knowledge (id INTEGER PRIMARY KEY AUTOINCREMENT, topic TEXT NOT NULL, content TEXT NOT NULL, created_at TEXT DEFAULT (datetime('now')))"
            _execute_query(conn, query, ())
            conn.commit()
        except sqlite3.Error as e:
            log.error(f"Database query execution failed: {e}")
        finally:
            conn.close()

# GAP_FILLED: missing_capability - No support for deleting or editing chat history
def _delete_chat_history(session_id, id):
    """
    Delete a chat history entry.

    Args:
        session_id (str): The session ID.
        id (int): The chat history ID.

    Returns:
        None
    """
    conn = _db()
    if conn:
        try:
            query = "DELETE FROM chat_history WHERE session_id = ? AND id = ?"
            params = (session_id, id)
            _execute_query(conn, query, params)
            conn.commit()
        except sqlite3.Error as e:
            log.error(f"Database query execution failed: {e}")
        finally:
            conn.close()

def _edit_chat_history(session_id, id, content):
    """
    Edit a chat history entry.

    Args:
        session_id (str): The session ID.
        id (int): The chat history ID.
        content (str): The new chat content.

    Returns:
        None
    """
    conn = _db()
    if conn:
        try:
            query = "UPDATE chat_history SET content = ? WHERE session_id = ? AND id = ?"
            params = (content, session_id, id)
            _execute_query(conn, query, params)
            conn.commit()
        except sqlite3.Error as e:
            log.error(f"Database query execution failed: {e}")
        finally:
            conn.close()