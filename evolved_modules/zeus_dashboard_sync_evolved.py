# The Zeus Project 2026 — Francois Nel
# ZEUS EVOLVED MODULE: zeus_dashboard_sync.py
# Evolution timestamp: 2026-03-21T17:08:56.679598
# Gaps addressed: 13
# Code hash: beeeef371004ca61
# ─────────────────────────────────────────────────────

# The Zeus Project 2026 — Francois Nel

import logging
import os
import re
import sqlite3
import json
import time
import threading
import queue
from pathlib import Path
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# GAP_FILLED: missing_error_handling - No error handling for database operations in _init_db and _conn functions
class ModuleRegistry:
    def __init__(self, db_path=DB_PATH):
        self._db   = Path(db_path)
        self._db.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._clients: list[queue.Queue] = []
        self._init_db()

    def _init_db(self):
        try:
            with self._conn() as c:
                c.execute("""CREATE TABLE IF NOT EXISTS modules (
                    module_id TEXT PRIMARY KEY, name TEXT, category TEXT DEFAULT 'general',
                    status TEXT DEFAULT 'active', description TEXT DEFAULT '',
                    version TEXT DEFAULT '1.0', filepath TEXT
                )""")
        except sqlite3.Error as e:
            logging.error(f"Error initializing database: {e}")

    def _conn(self):
        try:
            return sqlite3.connect(self._db)
        except sqlite3.Error as e:
            logging.error(f"Error connecting to database: {e}")
            return None

# GAP_FILLED: incomplete_implementation - The _push function is not fully implemented
    def _push(self, client, data):
        """Push data to a client queue."""
        try:
            client.put(data)
        except Exception as e:
            logging.error(f"Error pushing data to client: {e}")

# GAP_FILLED: security - Potential security vulnerability in using os.environ to get ZEUS_ROOT and ZEUS_MODULES_PATH
def get_env_var(var_name, default_value):
    """Get an environment variable securely."""
    try:
        return os.environ[var_name]
    except KeyError:
        return default_value

ZEUS_ROOT   = Path(get_env_var("ZEUS_ROOT", str(Path.home() / "zeus_v4")))
MODULES_DIR = Path(get_env_var("ZEUS_MODULES_PATH", str(ZEUS_ROOT / "modules")))

# GAP_FILLED: missing_error_handling - No error handling for watchdog observer in start_watcher function
class Watcher:
    def __init__(self, directory):
        self.directory = directory
        self.observer = None

    def start_watcher(self):
        try:
            self.observer = Observer()
            self.observer.schedule(event_handler=ModuleHandler(), path=self.directory, recursive=True)
            self.observer.start()
        except Exception as e:
            logging.error(f"Error starting watchdog observer: {e}")

# GAP_FILLED: missing_validation - No validation for module header patterns in parse_header function
def parse_header(filepath):
    """Parse a module header and validate its patterns."""
    try:
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            text = "".join(f.readline() for _ in range(30))
    except OSError:
        return None
    if not re.search(r"#\s*ZEUS_MODULE:", text, re.I):
        return None
    meta = {"filepath": str(filepath), "filename": Path(filepath).name}
    for k, p in HEADER_PATTERNS.items():
        m = p.search(text)
        if m:
            meta[k] = m.group(1).strip()
    if "module_id" not in meta or "name" not in meta:
        return None
    # Validate header patterns
    if not re.match(r"^[a-zA-Z0-9_]+$", meta["module_id"]):
        logging.warning(f"Invalid module ID: {meta['module_id']}")
        return None
    if not re.match(r"^[a-zA-Z0-9_]+$", meta["name"]):
        logging.warning(f"Invalid module name: {meta['name']}")
        return None
    meta["routes"]  = [r.strip() for r in meta.get("routes","").split(",") if r.strip()]
    meta["buttons"] = [b.strip() for b in meta.get("buttons","").split(",") if b.strip()]
    meta.setdefault("category","general")
    meta.setdefault("status","active")
    meta.setdefault("description","")
    meta.setdefault("version","1.0")
    return meta

# GAP_FILLED: missing_logging - No logging for important events such as module registration and unregistration
def register_module(module):
    """Register a module and log the event."""
    try:
        with ModuleRegistry()._conn() as c:
            c.execute("INSERT INTO modules (module_id, name, category, status, description, version, filepath) VALUES (?, ?, ?, ?, ?, ?, ?)",
                       (module["module_id"], module["name"], module["category"], module["status"], module["description"], module["version"], module["filepath"]))
        logging.info(f"Module registered: {module['module_id']}")
    except sqlite3.Error as e:
        logging.error(f"Error registering module: {e}")

def unregister_module(module_id):
    """Unregister a module and log the event."""
    try:
        with ModuleRegistry()._conn() as c:
            c.execute("DELETE FROM modules WHERE module_id = ?", (module_id,))
        logging.info(f"Module unregistered: {module_id}")
    except sqlite3.Error as e:
        logging.error(f"Error unregistering module: {e}")

# GAP_FILLED: missing_function - No function to handle module updates
def update_module(module):
    """Update a module and log the event."""
    try:
        with ModuleRegistry()._conn() as c:
            c.execute("UPDATE modules SET name = ?, category = ?, status = ?, description = ?, version = ? WHERE module_id = ?",
                       (module["name"], module["category"], module["status"], module["description"], module["version"], module["module_id"]))
        logging.info(f"Module updated: {module['module_id']}")
    except sqlite3.Error as e:
        logging.error(f"Error updating module: {e}")

# GAP_FILLED: missing_function - No function to handle module deletion
def delete_module(module_id):
    """Delete a module and log the event."""
    try:
        with ModuleRegistry()._conn() as c:
            c.execute("DELETE FROM modules WHERE module_id = ?", (module_id,))
        logging.info(f"Module deleted: {module_id}")
    except sqlite3.Error as e:
        logging.error(f"Error deleting module: {e}")

# GAP_FILLED: missing_capability - No support for filtering or sorting modules
def get_modules(filter_by=None, sort_by=None):
    """Get modules with optional filtering and sorting."""
    try:
        with ModuleRegistry()._conn() as c:
            if filter_by:
                c.execute("SELECT * FROM modules WHERE category = ?", (filter_by,))
            else:
                c.execute("SELECT * FROM modules")
            modules = c.fetchall()
            if sort_by:
                modules.sort(key=lambda x: x[sort_by])
            return modules
    except sqlite3.Error as e:
        logging.error(f"Error getting modules: {e}")

class ModuleHandler(FileSystemEventHandler):
    def on_modified(self, event):
        if event.is_directory:
            return None
        logging.info(f"Module file modified: {event.src_path}")
        module = parse_header(event.src_path)
        if module:
            register_module(module)

    def on_created(self, event):
        if event.is_directory:
            return None
        logging.info(f"Module file created: {event.src_path}")
        module = parse_header(event.src_path)
        if module:
            register_module(module)

    def on_deleted(self, event):
        if event.is_directory:
            return None
        logging.info(f"Module file deleted: {event.src_path}")
        module_id = Path(event.src_path).stem
        unregister_module(module_id)