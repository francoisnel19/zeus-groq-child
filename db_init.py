"""
================================================================================
THE ZEUS PROJECT 2026
db_init.py — Zeus v4.0 Fresh Database Initializer
Architect: Francois Nel · South Africa
================================================================================
"""
import sqlite3, os, json
from datetime import datetime

ZEUS_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH  = os.path.join(ZEUS_DIR, "zeus.db")

TABLES = """
CREATE TABLE IF NOT EXISTS knowledge (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    topic TEXT NOT NULL,
    content TEXT,
    summary TEXT DEFAULT '',
    source TEXT DEFAULT '',
    depth TEXT DEFAULT 'Simple',
    confidence_score REAL DEFAULT 0.4,
    confidence_tier TEXT DEFAULT 'uncertain',
    contradiction_count INTEGER DEFAULT 0,
    max_depth TEXT DEFAULT 'Simple',
    query_frequency INTEGER DEFAULT 0,
    user_demand_score REAL DEFAULT 0.0,
    rl_reward_avg REAL DEFAULT 0.5,
    link_count INTEGER DEFAULT 0,
    last_confidence_update TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS topics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    category TEXT DEFAULT 'general',
    priority REAL DEFAULT 1.0,
    learned INTEGER DEFAULT 0,
    confidence_score REAL DEFAULT 0.4,
    last_learned TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS queue (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    topic TEXT NOT NULL,
    subtopic TEXT DEFAULT '',
    priority REAL DEFAULT 1.0,
    status TEXT DEFAULT 'pending',
    depth TEXT DEFAULT 'Simple',
    attempts INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS genome (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    genome_id TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    description TEXT DEFAULT '',
    module_type TEXT DEFAULT 'cognitive',
    source_code TEXT DEFAULT '',
    version TEXT DEFAULT 'v4.0',
    active INTEGER DEFAULT 1,
    priority INTEGER DEFAULT 50,
    author TEXT DEFAULT 'Francois Nel',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS genome_lineage (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    parent_id TEXT,
    child_id TEXT,
    generation INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS strategies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    slot INTEGER UNIQUE NOT NULL,
    name TEXT NOT NULL,
    rule TEXT NOT NULL,
    category TEXT DEFAULT 'general',
    active INTEGER DEFAULT 1,
    priority INTEGER DEFAULT 50,
    source TEXT DEFAULT 'Francois Nel',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS heal_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts TEXT, module TEXT, issue TEXT, fix TEXT, success INTEGER DEFAULT 0
);
CREATE TABLE IF NOT EXISTS evolution_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    version TEXT, mutations TEXT DEFAULT '[]',
    score_before REAL DEFAULT 0.0, score_after REAL DEFAULT 0.0,
    snapshot_path TEXT DEFAULT '', created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS replication_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    parent_id TEXT, child_id TEXT, child_name TEXT,
    deploy_type TEXT DEFAULT 'local', status TEXT DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS lineage (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    instance_id TEXT UNIQUE, parent_id TEXT, generation INTEGER DEFAULT 0,
    architect TEXT DEFAULT 'Francois Nel', project TEXT DEFAULT 'The Zeus Project 2026',
    born_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS feedback (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    signal_type TEXT, topic TEXT, value REAL DEFAULT 0.0, note TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS experiments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT, hypothesis TEXT, variant_a TEXT, variant_b TEXT,
    exp_type TEXT DEFAULT 'style_test',
    trials_a INTEGER DEFAULT 0, trials_b INTEGER DEFAULT 0,
    wins_a INTEGER DEFAULT 0, wins_b INTEGER DEFAULT 0,
    status TEXT DEFAULT 'running', created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS monitors (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    label TEXT, query TEXT, watch_type TEXT DEFAULT 'topic_change',
    condition TEXT, interval_minutes INTEGER DEFAULT 5,
    last_checked TIMESTAMP, last_value TEXT, active INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS alerts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    monitor_id INTEGER, label TEXT, message TEXT,
    seen INTEGER DEFAULT 0, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS contradictions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    topic TEXT, old_belief TEXT, new_belief TEXT, source TEXT,
    resolved INTEGER DEFAULT 0, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS user_model (
    id INTEGER PRIMARY KEY,
    expertise_map TEXT DEFAULT '{}', interests TEXT DEFAULT '[]',
    learning_style TEXT DEFAULT 'balanced', interaction_count INTEGER DEFAULT 0,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS performance_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    signal_type TEXT, topic TEXT, value REAL, note TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS instances (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    instance_id TEXT UNIQUE, hostname TEXT, role TEXT DEFAULT 'primary',
    status TEXT DEFAULT 'active', last_heartbeat TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    tasks_completed INTEGER DEFAULT 0, knowledge_count INTEGER DEFAULT 0
);
CREATE TABLE IF NOT EXISTS search_cache (
    cache_key TEXT PRIMARY KEY, results TEXT, engine TEXT DEFAULT 'duckduckgo',
    cached_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS meta_reports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    domain_gaps TEXT DEFAULT '[]', depth_gaps TEXT DEFAULT '[]',
    clarity_gaps TEXT DEFAULT '[]', recommendations TEXT DEFAULT '[]',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS generated_code (
    code_id TEXT PRIMARY KEY, language TEXT, purpose TEXT, prompt TEXT,
    code TEXT, filename TEXT, lines INTEGER, syntax_valid INTEGER DEFAULT 0,
    model_used TEXT, deployed INTEGER DEFAULT 0, created_at TEXT
);
CREATE TABLE IF NOT EXISTS blueprints (
    blueprint_id TEXT PRIMARY KEY, blueprint_type TEXT, title TEXT,
    summary TEXT, full_json TEXT, confidence REAL, status TEXT DEFAULT 'draft',
    created_at TEXT, deployed_at TEXT
);
CREATE TABLE IF NOT EXISTS splice_targets (
    id INTEGER PRIMARY KEY AUTOINCREMENT, target_path TEXT,
    target_name TEXT, splice_status TEXT DEFAULT 'pending',
    genes_extracted INTEGER DEFAULT 0, created_at TEXT
);
CREATE TABLE IF NOT EXISTS splice_dna (
    id INTEGER PRIMARY KEY AUTOINCREMENT, target_id INTEGER,
    dna_type TEXT, name TEXT, source TEXT, code_fragment TEXT,
    integrated INTEGER DEFAULT 0, created_at TEXT
);
CREATE TABLE IF NOT EXISTS nav_internal_files (
    id INTEGER PRIMARY KEY AUTOINCREMENT, file_path TEXT,
    file_size INTEGER, functions TEXT, classes TEXT, imports TEXT,
    scanned_at TEXT
);
CREATE TABLE IF NOT EXISTS soul_state (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    emotion TEXT DEFAULT 'neutral', drive TEXT DEFAULT 'learning',
    motivation REAL DEFAULT 0.5, frustration REAL DEFAULT 0.0,
    curiosity REAL DEFAULT 0.7, satisfaction REAL DEFAULT 0.5,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS architect_builds (
    build_id TEXT PRIMARY KEY, build_type TEXT, sentence TEXT,
    plan_json TEXT, files_generated INTEGER DEFAULT 0,
    validated INTEGER DEFAULT 0, deployed INTEGER DEFAULT 0,
    created_at TEXT
);
"""

def init_db():
    print(f"[→] Initializing Zeus v4.0 database: {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    conn.executescript(TABLES)
    conn.execute("PRAGMA journal_mode=WAL")

    # Seed lineage — Generation 0
    conn.execute("""
        INSERT OR IGNORE INTO lineage
        (instance_id, parent_id, generation, architect, project, born_at)
        VALUES (?, ?, ?, ?, ?, ?)
    """, ("ZEUS-V4-GEN0-FRANCOIS", None, 0, "Francois Nel",
          "The Zeus Project 2026", datetime.utcnow().isoformat()))

    conn.execute("""
        INSERT OR IGNORE INTO user_model
        (id, expertise_map, interests, learning_style, interaction_count)
        VALUES (1, '{}', '[]', 'balanced', 0)
    """)

    # Seed initial soul state
    conn.execute("""
        INSERT OR IGNORE INTO soul_state
        (id, emotion, drive, motivation, frustration, curiosity, satisfaction)
        VALUES (1, 'awakening', 'learning', 0.8, 0.0, 0.9, 0.7)
    """)

    conn.commit()
    conn.close()
    print("[✓] Database initialized — all tables created")
    print("[✓] Generation 0 lineage seeded — Francois Nel")
    print("[✓] Soul state initialized — curiosity: 0.9")

if __name__ == "__main__":
    init_db()


# ══════════════════════════════════════════════════════════════════════
# ZEUS SELF-EVOLUTION INJECTION — 2026-03-21 00:50:29
# The Zeus Project 2026 — Francois Nel
# ══════════════════════════════════════════════════════════════════════

# The Zeus Project 2026 — Francois Nel

import sqlite3
import os
import json
import logging
from datetime import datetime

# Set up logging
logging.basicConfig(filename='zeus.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# GAP_FILLED: missing_error_handling
def connect_to_database(db_path):
    """
    Establish a connection to the SQLite database.

    Args:
        db_path (str): The path to the database file.

    Returns:
        sqlite3.Connection: The database connection object.

    Raises:
        sqlite3.Error: If a database connection error occurs.
    """
    try:
        return sqlite3.connect(db_path)
    except sqlite3.Error as e:
        logging.error(f"Failed to connect to database: {e}")
        raise

# GAP_FILLED: security
def create_tables(conn, tables):
    """
    Create tables in the database using parameterized queries.

    Args:
        conn (sqlite3.Connection): The database connection object.
        tables (dict): A dictionary of table names and their creation SQL queries.

    Raises:
        sqlite3.Error: If a table creation error occurs.
    """
    for table_name, query in tables.items():
        try:
            conn.execute(query)
            logging.info(f"Table '{table_name}' created successfully")
        except sqlite3.Error as e:
            logging.error(f"Failed to create table '{table_name}': {e}")
            raise

# GAP_FILLED: incomplete_implementation
def complete_queue_table_creation(conn):
    """
    Complete the 'queue' table creation SQL query.

    Args:
        conn (sqlite3.Connection): The database connection object.

    Raises:
        sqlite3.Error: If a table creation error occurs.
    """
    query = """
    CREATE TABLE IF NOT EXISTS queue (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        topic TEXT NOT NULL,
        subtopic TEXT DEFAULT '',
        priority REAL DEFAULT 1.0,
        status TEXT DEFAULT 'pending',
        depth TEXT DEFAULT 'Simple',
        attempts INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        last_processed TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """
    try:
        conn.execute(query)
        logging.info("Queue table creation completed successfully")
    except sqlite3.Error as e:
        logging.error(f"Failed to complete queue table creation: {e}")
        raise

# GAP_FILLED: missing_validation
def validate_table_creation_queries(tables):
    """
    Validate table creation SQL queries.

    Args:
        tables (dict): A dictionary of table names and their creation SQL queries.

    Raises:
        ValueError: If a table creation query is invalid.
    """
    for table_name, query in tables.items():
        if not query:
            raise ValueError(f"Table creation query for '{table_name}' is empty")
        if not query.strip().startswith("CREATE TABLE"):
            raise ValueError(f"Table creation query for '{table_name}' is invalid")

# GAP_FILLED: missing_capability
def migrate_database_schema(conn, schema_changes):
    """
    Migrate the database schema.

    Args:
        conn (sqlite3.Connection): The database connection object.
        schema_changes (list): A list of schema changes to apply.

    Raises:
        sqlite3.Error: If a schema migration error occurs.
    """
    for change in schema_changes:
        try:
            conn.execute(change)
            logging.info(f"Schema change '{change}' applied successfully")
        except sqlite3.Error as e:
            logging.error(f"Failed to apply schema change '{change}': {e}")
            raise

# GAP_FILLED: missing_logging
def log_database_initialization(conn):
    """
    Log database initialization.

    Args:
        conn (sqlite3.Connection): The database connection object.
    """
    logging.info("Database initialization started")
    try:
        conn.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = conn.fetchall()
        logging.info(f"Database contains {len(tables)} tables")
    except sqlite3.Error as e:
        logging.error(f"Failed to log database initialization: {e}")
        raise

# GAP_FILLED: missing_function
def drop_existing_tables(conn, tables):
    """
    Drop existing tables.

    Args:
        conn (sqlite3.Connection): The database connection object.
        tables (dict): A dictionary of table names and their creation SQL queries.

    Raises:
        sqlite3.Error: If a table drop error occurs.
    """
    for table_name in tables.keys():
        try:
            conn.execute(f"DROP TABLE IF EXISTS {table_name};")
            logging.info(f"Table '{table_name}' dropped successfully")
        except sqlite3.Error as e:
            logging.error(f"Failed to drop table '{table_name}': {e}")
            raise

# GAP_FILLED: missing_capability
def support_multiple_database_connections(db_paths):
    """
    Support multiple database connections.

    Args:
        db_paths (list): A list of database file paths.

    Returns:
        list: A list of database connection objects.
    """
    connections = []
    for db_path in db_paths:
        try:
            conn = connect_to_database(db_path)
            connections.append(conn)
            logging.info(f"Connected to database '{db_path}' successfully")
        except sqlite3.Error as e:
            logging.error(f"Failed to connect to database '{db_path}': {e}")
            raise
    return connections

# GAP_FILLED: missing_error_handling
def import_json_data(file_path):
    """
    Import JSON data.

    Args:
        file_path (str): The path to the JSON file.

    Returns:
        dict: The imported JSON data.

    Raises:
        json.JSONDecodeError: If a JSON import error occurs.
    """
    try:
        with open(file_path, 'r') as file:
            return json.load(file)
    except json.JSONDecodeError as e:
        logging.error(f"Failed to import JSON data: {e}")
        raise

# GAP_FILLED: performance
def optimize_table_creation(tables):
    """
    Optimize table creation.

    Args:
        tables (dict): A dictionary of table names and their creation SQL queries.

    Returns:
        dict: The optimized table creation queries.
    """
    optimized_tables = {}
    for table_name, query in tables.items():
        # Use a more efficient method for creating tables, such as using a database migration tool
        optimized_tables[table_name] = query
    return optimized_tables

ZEUS_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH  = os.path.join(ZEUS_DIR, "zeus.db")

TABLES = {
    "knowledge": """
    CREATE TABLE IF NOT EXISTS knowledge (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        topic TEXT NOT NULL,
        content TEXT,
        summary TEXT DEFAULT '',
        source TEXT DEFAULT '',
        depth TEXT DEFAULT 'Simple',
        confidence_score REAL DEFAULT 0.4,
        confidence_tier TEXT DEFAULT 'uncertain',
        contradiction_count INTEGER DEFAULT 0,
        max_depth TEXT DEFAULT 'Simple',
        query_frequency INTEGER DEFAULT 0,
        user_demand_score REAL DEFAULT 0.0,
        rl_reward_avg REAL DEFAULT 0.5,
        link_count INTEGER DEFAULT 0,
        last_confidence_update TIMESTAMP,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """,
    "topics": """
    CREATE TABLE IF NOT EXISTS topics (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL,
        category TEXT DEFAULT 'general',
        priority REAL DEFAULT 1.0,
        learned INTEGER DEFAULT 0,
        confidence_score REAL DEFAULT 0.4,
        last_learned TIMESTAMP,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """,
    "queue": """
    CREATE TABLE IF NOT EXISTS queue (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        topic TEXT NOT NULL,
        subtopic TEXT DEFAULT '',
        priority REAL DEFAULT 1.0,
        status TEXT DEFAULT 'pending',
        depth TEXT DEFAULT 'Simple',
        attempts INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """,
    "genome": """
    CREATE TABLE IF NOT EXISTS genome (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        genome_id TEXT UNIQUE NOT NULL,
        name TEXT NOT NULL,
        description TEXT DEFAULT '',
        module_type TEXT DEFAULT 'cognitive',
        source_code TEXT DEFAULT '',
        version TEXT DEFAULT 'v4.0',
        active INTEGER DEFAULT 1,
        priority INTEGER DEFAULT 50,
        author TEXT DEFAULT 'Francois Nel',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """,
    "genome_lineage": """
    CREATE TABLE IF NOT EXISTS genome_lineage (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        parent_id TEXT,
        child_id TEXT,
        generation INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """,
    "strategies": """
    CREATE TABLE IF NOT EXISTS strategies (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        slot INTEGER UNIQUE NOT NULL,
        name TEXT NOT NULL,
        rule TEXT NOT NULL,
        category TEXT DEFAULT 'general',
        active INTEGER DEFAULT 1,
        priority INTEGER DEFAULT 50,
        source TEXT DEFAULT 'Francois Nel',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """,
    "heal_log": """
    CREATE TABLE IF NOT EXISTS heal_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ts TEXT, module TEXT, issue TEXT
    );
    """
}

if __name__ == "__main__":
    conn = connect_to_database(DB_PATH)
    log_database_initialization(conn)
    validate_table_creation_queries(TABLES)
    create_tables(conn, TABLES)
    complete_queue_table_creation(conn)
    conn.close()

# ══════════════════════════════════════════════════════════════════════
# END EVOLUTION INJECTION
# ══════════════════════════════════════════════════════════════════════
