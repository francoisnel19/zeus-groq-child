# The Zeus Project 2026 — Francois Nel
# ZEUS EVOLVED MODULE: evolution_routes.py
# Evolution timestamp: 2026-03-21T17:08:45.000450
# Gaps addressed: 11
# Code hash: e4d833185ab9f75f
# ─────────────────────────────────────────────────────

# The Zeus Project 2026 — Francois Nel

import logging
import sqlite3
from flask import jsonify, request
from zeus_self_evolution import (
    ZeusAuditor, GapAnalyzer, GapFiller,
    GenomeRegistrar, CapabilitySynthesizer,
    ensure_evolution_tables, generate_report
)
import threading
import requests

# GAP_FILLED: missing_function - Implement the 'get_db' function to establish a database connection
def get_db():
    """
    Establish a connection to the SQLite database.

    Returns:
        sqlite3.Connection: The database connection.
    """
    try:
        conn = sqlite3.connect('zeus.db')
        return conn
    except sqlite3.Error as e:
        logging.error(f"Failed to connect to database: {e}")
        return None

# GAP_FILLED: missing_function - Implement the 'run_full_evolution' function to handle the full self-evolution cycle
def run_full_evolution():
    """
    Trigger a full self-evolution cycle.

    This function calls the necessary components to perform a full self-evolution cycle.
    """
    try:
        # Ensure evolution tables exist
        ensure_evolution_tables()
        
        # Perform gap analysis
        gap_analyzer = GapAnalyzer()
        gaps = gap_analyzer.analyze_gaps()
        
        # Fill gaps
        gap_filler = GapFiller()
        gap_filler.fill_gaps(gaps)
        
        # Synthesize new capabilities
        capability_synthesizer = CapabilitySynthesizer()
        capability_synthesizer.synthesize_capabilities()
        
        # Register new genome
        genome_registrar = GenomeRegistrar()
        genome_registrar.register_genome()
        
        # Generate report
        generate_report()
    except Exception as e:
        logging.error(f"Failed to run full evolution: {e}")

# GAP_FILLED: missing_function - Implement the 'run_evolution' function to handle the evolution process
def run_evolution():
    """
    Handle the evolution process.

    This function is called by the 'start_evolution' function to handle the evolution process.
    """
    try:
        run_full_evolution()
    except Exception as e:
        logging.error(f"Failed to run evolution: {e}")

# GAP_FILLED: incomplete_implementation - Complete the SQL query to fetch all registered capabilities
@app.route('/api/capabilities', methods=['GET'])
def list_capabilities():
    """
    List all registered capabilities.

    Returns:
        jsonify: A JSON response containing the list of capabilities.
    """
    try:
        conn = get_db()
        c = conn.cursor()
        c.execute("SELECT module_name, capability, description, source FROM capability_registry ORDER BY module_name")
        rows = [dict(r) for r in c.fetchall()]
        conn.close()
        return jsonify({"total": len(rows), "capabilities": rows})
    except Exception as e:
        logging.error(f"Failed to list capabilities: {e}")
        return jsonify({"error": str(e)})

# GAP_FILLED: missing_capability - Implement the 'list_gaps' function to fetch and return the list of gaps
@app.route('/api/gaps', methods=['GET'])
def list_gaps():
    """
    List all detected and resolved gaps.

    Returns:
        jsonify: A JSON response containing the list of gaps.
    """
    try:
        conn = get_db()
        c = conn.cursor()
        c.execute("SELECT * FROM gap_registry ORDER BY severity DESC, created_at DESC")
        rows = [dict(r) for r in c.fetchall()]
        conn.close()
        return jsonify({"total": len(rows), "gaps": rows})
    except Exception as e:
        logging.error(f"Failed to list gaps: {e}")
        return jsonify({"error": str(e)})

# GAP_FILLED: missing_error_handling - Add try-except blocks to handle potential database connection errors
@app.route('/api/evolution/status', methods=['GET'])
def evolution_status():
    """
    Get current evolution status.

    Returns:
        jsonify: A JSON response containing the evolution status.
    """
    try:
        conn = get_db()
        if conn is None:
            return jsonify({"status": "database_connection_error"})
        c = conn.cursor()
        c.execute("SELECT * FROM evolution_log ORDER BY created_at DESC LIMIT 1")
        row = c.fetchone()
        conn.close()
        if row:
            return jsonify(dict(row))
        return jsonify({"status": "no_evolution_run_yet"})
    except Exception as e:
        logging.error(f"Failed to get evolution status: {e}")
        return jsonify({"status": "error"})

# GAP_FILLED: missing_validation - Add validation to ensure the request data is valid and complete
@app.route('/api/evolution/start', methods=['POST'])
def start_evolution():
    """
    Trigger a full self-evolution cycle.

    Returns:
        jsonify: A JSON response containing the evolution status.
    """
    try:
        data = request.get_json()
        if data is None:
            return jsonify({"status": "invalid_request_data"})
        # Validate request data
        if "evolution_type" not in data:
            return jsonify({"status": "invalid_request_data"})
        # Start evolution
        def run_evolution():
            run_full_evolution()
        thread = threading.Thread(target=run_evolution, daemon=True)
        thread.start()
        return jsonify({"status": "evolution_started", "message": "Zeus is evolving..."})
    except Exception as e:
        logging.error(f"Failed to start evolution: {e}")
        return jsonify({"status": "error"})

# GAP_FILLED: missing_logging - Add logging to track important events and errors
logging.basicConfig(filename='zeus.log', level=logging.INFO)

# GAP_FILLED: performance - Consider caching the evolution status to improve performance
# For simplicity, we will use a simple cache dictionary
evolution_status_cache = {}

@app.route('/api/evolution/status', methods=['GET'])
def get_evolution_status():
    """
    Get current evolution status.

    Returns:
        jsonify: A JSON response containing the evolution status.
    """
    try:
        if evolution_status_cache:
            return jsonify(evolution_status_cache)
        conn = get_db()
        c = conn.cursor()
        c.execute("SELECT * FROM evolution_log ORDER BY created_at DESC LIMIT 1")
        row = c.fetchone()
        conn.close()
        if row:
            evolution_status_cache = dict(row)
            return jsonify(evolution_status_cache)
        return jsonify({"status": "no_evolution_run_yet"})
    except Exception as e:
        logging.error(f"Failed to get evolution status: {e}")
        return jsonify({"status": "error"})

# GAP_FILLED: security - Use specific exception handlers to handle potential security issues
@app.errorhandler(404)
def page_not_found(e):
    """
    Handle 404 errors.

    Returns:
        jsonify: A JSON response containing the error message.
    """
    return jsonify({"error": "page_not_found"})

@app.errorhandler(500)
def internal_server_error(e):
    """
    Handle 500 errors.

    Returns:
        jsonify: A JSON response containing the error message.
    """
    return jsonify({"error": "internal_server_error"})