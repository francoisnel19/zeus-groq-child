# The Zeus Project 2026 — Francois Nel
# ZEUS EVOLVED MODULE: 2_zeus_upload.py
# Evolution timestamp: 2026-03-21T00:49:24.476834
# Gaps addressed: 12
# Code hash: fec2d023829727fe
# ─────────────────────────────────────────────────────

# The Zeus Project 2026 — Francois Nel

import os, sqlite3, zipfile, ast, logging, time, uuid, json
from datetime import datetime, timezone
from pathlib import Path
from flask import Blueprint, request, jsonify
from werkzeug.utils import secure_filename
import requests

log = logging.getLogger("Zeus.Upload")

# GAP_FILLED: missing_error_handling for database connection failures in _db function
def _db():
    """
    Establish a connection to the SQLite database.

    Returns:
        sqlite3.Connection: The database connection object.
    """
    try:
        c = sqlite3.connect(DB_PATH, timeout=10)
        c.row_factory = sqlite3.Row
        return c
    except sqlite3.Error as e:
        log.error(f"Database connection failed: {e}")
        return None

# GAP_FILLED: missing_error_handling for file upload failures
def upload_file(file):
    """
    Upload a file to the server.

    Args:
        file (werkzeug.FileStorage): The file to upload.

    Returns:
        bool: True if the upload was successful, False otherwise.
    """
    try:
        filename = secure_filename(file.filename)
        file.save(os.path.join(UPLOAD_DIR, filename))
        log.info(f"File uploaded: {filename}")
        return True
    except Exception as e:
        log.error(f"File upload failed: {e}")
        return False

# GAP_FILLED: security - implement additional security measures to prevent directory traversal attacks
def validate_filename(filename):
    """
    Validate a filename to prevent directory traversal attacks.

    Args:
        filename (str): The filename to validate.

    Returns:
        bool: True if the filename is valid, False otherwise.
    """
    if ".." in filename or filename.startswith("/"):
        log.warning(f"Invalid filename: {filename}")
        return False
    return True

# GAP_FILLED: missing_validation for uploaded file types beyond checking extensions
def validate_file_type(file):
    """
    Validate the type of an uploaded file.

    Args:
        file (werkzeug.FileStorage): The file to validate.

    Returns:
        bool: True if the file type is valid, False otherwise.
    """
    if file.mimetype not in ["text/plain", "application/json", "application/pdf", "image/jpeg", "image/png"]:
        log.warning(f"Invalid file type: {file.mimetype}")
        return False
    return True

# GAP_FILLED: missing_capability - support for uploading large files
def chunked_upload(file):
    """
    Upload a large file in chunks.

    Args:
        file (werkzeug.FileStorage): The file to upload.

    Returns:
        bool: True if the upload was successful, False otherwise.
    """
    chunk_size = 1024 * 1024  # 1MB chunks
    filename = secure_filename(file.filename)
    with open(os.path.join(UPLOAD_DIR, filename), "wb") as f:
        while True:
            chunk = file.stream.read(chunk_size)
            if not chunk:
                break
            f.write(chunk)
    log.info(f"File uploaded: {filename}")
    return True

# GAP_FILLED: missing_logging for file upload successes or failures
def log_upload_event(file, success):
    """
    Log a file upload event.

    Args:
        file (werkzeug.FileStorage): The file that was uploaded.
        success (bool): True if the upload was successful, False otherwise.
    """
    if success:
        log.info(f"File uploaded: {file.filename}")
    else:
        log.error(f"File upload failed: {file.filename}")

# GAP_FILLED: missing_capability - support for uploading multiple files at once
def upload_multiple_files(files):
    """
    Upload multiple files at once.

    Args:
        files (list): A list of werkzeug.FileStorage objects.

    Returns:
        list: A list of boolean values indicating whether each file was uploaded successfully.
    """
    results = []
    for file in files:
        if upload_file(file):
            results.append(True)
        else:
            results.append(False)
    return results

# GAP_FILLED: incomplete_implementation - complete the implementation of the _ensure_tables function
def _ensure_tables():
    """
    Ensure that all necessary tables exist in the database.
    """
    conn = _db()
    if conn is None:
        log.error("Database connection failed")
        return
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS uploaded_files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_id TEXT UNIQUE NOT NULL,
            filename TEXT NOT NULL,
            file_type TEXT NOT NULL,
            size_bytes INTEGER DEFAULT 0,
            status TEXT DEFAULT 'processing',
            items_extracted INTEGER DEFAULT 0,
            genome_segments INTEGER DEFAULT 0,
            knowledge_added INTEGER DEFAULT 0,
            error_msg TEXT DEFAULT '',
            uploaded_at TEXT DEFAULT (datetime('now')),
            processed_at TEXT
        );

        CREATE TABLE IF NOT EXISTS knowledge (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            topic TEXT NOT NULL,
            content TEXT NOT NULL,
            summary TEXT NOT NULL,
            source TEXT NOT NULL,
            depth TEXT NOT NULL,
            confidence_score REAL NOT NULL,
            created_at TEXT NOT NULL,
            last_updated TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS splice_targets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            target_path TEXT NOT NULL,
            target_name TEXT NOT NULL,
            splice_status TEXT NOT NULL,
            genes_extracted INTEGER NOT NULL,
            created_at TEXT NOT NULL
        );
    """)
    conn.commit()
    conn.close()

# GAP_FILLED: missing_capability - support for deleting or updating uploaded files
def delete_uploaded_file(file_id):
    """
    Delete an uploaded file.

    Args:
        file_id (str): The ID of the file to delete.

    Returns:
        bool: True if the file was deleted successfully, False otherwise.
    """
    conn = _db()
    if conn is None:
        log.error("Database connection failed")
        return False
    conn.execute("DELETE FROM uploaded_files WHERE file_id = ?", (file_id,))
    conn.commit()
    conn.close()
    return True

def update_uploaded_file(file_id, filename):
    """
    Update the filename of an uploaded file.

    Args:
        file_id (str): The ID of the file to update.
        filename (str): The new filename.

    Returns:
        bool: True if the file was updated successfully, False otherwise.
    """
    conn = _db()
    if conn is None:
        log.error("Database connection failed")
        return False
    conn.execute("UPDATE uploaded_files SET filename = ? WHERE file_id = ?", (filename, file_id))
    conn.commit()
    conn.close()
    return True

# GAP_FILLED: missing_capability - support for uploading files from external sources (e.g. URLs)
def upload_file_from_url(url):
    """
    Upload a file from a URL.

    Args:
        url (str): The URL of the file to upload.

    Returns:
        bool: True if the file was uploaded successfully, False otherwise.
    """
    try:
        response = requests.get(url)
        if response.status_code == 200:
            filename = os.path.basename(url)
            with open(os.path.join(UPLOAD_DIR, filename), "wb") as f:
                f.write(response.content)
            log.info(f"File uploaded: {filename}")
            return True
        else:
            log.error(f"Failed to upload file from URL: {url}")
            return False
    except Exception as e:
        log.error(f"Failed to upload file from URL: {url} - {e}")
        return False

# GAP_FILLED: missing_error_handling for database connection failures in _store_knowledge function
def _store_knowledge(topic, content, source="upload"):
    """
    Store knowledge in the database.

    Args:
        topic (str): The topic of the knowledge.
        content (str): The content of the knowledge.
        source (str): The source of the knowledge.

    Returns:
        int: The number of knowledge items stored.
    """
    if not (content and content.strip()):
        return 0
    conn = _db()
    if conn is None:
        log.error("Database connection failed")
        return 0
    chunks = [content[i:i+4000] for i in range(0, min(len(content),40000), 4000)]
    added = 0
    for i, chunk in enumerate(chunks):
        t = topic if i == 0 else f"{topic} (part {i+1})"
        try:
            conn.execute("""INSERT OR IGNORE INTO knowledge
                (topic,content,summary,source,depth,confidence_score,created_at,last_updated)
                VALUES (?,?,?,?,'Deep',0.80,?,?)""",
                (t, chunk, chunk[:200], source,
                 datetime.now(timezone.utc).isoformat(),
                 datetime.now(timezone.utc).isoformat()))
            added += 1
        except sqlite3.Error as e:
            log.error(f"Failed to store knowledge: {e}")
    conn.commit()
    conn.close()
    return added

# GAP_FILLED: missing_error_handling for database connection failures in _register_splice_target function
def _register_splice_target(name, path, file_id):
    """
    Register a splice target.

    Args:
        name (str): The name of the splice target.
        path (str): The path of the splice target.
        file_id (str): The ID of the file.

    Returns:
        None
    """
    conn = _db()
    if conn is None:
        log.error("Database connection failed")
        return
    try:
        conn.execute("""INSERT INTO splice_targets (target_path,target_name,splice_status,genes_extracted,created_at)
            VALUES (?,?,\'scanning\',0,?)""",
            (path, name, datetime.now(timezone.utc).isoformat()))
        conn.commit()
    except sqlite3.Error as e:
        log.error(f"Failed to register splice target: {e}")
    conn.close()