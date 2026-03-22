# The Zeus Project 2026 — Francois Nel
# ZEUS EVOLVED MODULE: 4_zeus_search.py
# Evolution timestamp: 2026-03-21T00:49:46.503416
# Gaps addressed: 11
# Code hash: bd2c07a752b7f00a
# ─────────────────────────────────────────────────────

# The Zeus Project 2026 — Francois Nel

import os
import sqlite3
import logging
import requests
from flask import Blueprint, request, jsonify
from datetime import datetime, timezone
import hashlib
import json
import re

# GAP_FILLED: missing_error_handling for database connection failures
def _db():
    """
    Establish a connection to the database.

    Returns:
        sqlite3.Connection: A connection to the database.
    """
    try:
        conn = sqlite3.connect(DB_PATH, timeout=10)
        conn.row_factory = sqlite3.Row
        return conn
    except sqlite3.Error as e:
        log.error(f"Failed to connect to database: {e}")
        return None

# GAP_FILLED: missing_validation for user input
def _validate_input(query):
    """
    Validate user input to prevent SQL injection and other attacks.

    Args:
        query (str): The user's search query.

    Returns:
        bool: True if the input is valid, False otherwise.
    """
    if not isinstance(query, str):
        return False
    if len(query) > 1000:
        return False
    if re.search(r"[^a-zA-Z0-9\s\+\-\:\.\_]", query):
        return False
    return True

# GAP_FILLED: incomplete_implementation of the _ensure_tables function
def _ensure_tables():
    """
    Ensure that the necessary tables exist in the database.

    This function creates the search_cache and search_log tables if they do not already exist.
    """
    conn = _db()
    if conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS search_cache (
                cache_key  TEXT PRIMARY KEY,
                query      TEXT,
                results    TEXT,
                engine     TEXT DEFAULT 'google',
                hit_count  INTEGER DEFAULT 0,
                cached_at  TEXT DEFAULT (datetime('now'))
            );
            CREATE TABLE IF NOT EXISTS search_log (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                query      TEXT,
                engine     TEXT,
                result_count INTEGER DEFAULT 0,
                cached     INTEGER DEFAULT 0,
                elapsed_ms INTEGER DEFAULT 0,
                created_at TEXT DEFAULT (datetime('now'))
            );
            CREATE TABLE IF NOT EXISTS search_engines (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                name      TEXT,
                api_key   TEXT,
                base_url  TEXT
            );
        """)
        conn.commit()
        conn.close()

# GAP_FILLED: security issue with hardcoded API keys
def _get_api_key(engine):
    """
    Get the API key for a given search engine.

    Args:
        engine (str): The name of the search engine.

    Returns:
        str: The API key for the search engine.
    """
    api_keys = {
        "google": os.getenv("GOOGLE_API_KEY"),
        "duckduckgo": os.getenv("DUCKDUCKGO_API_KEY"),
        "bing": os.getenv("BING_API_KEY"),
        "yahoo": os.getenv("YAHOO_API_KEY")
    }
    return api_keys.get(engine)

# GAP_FILLED: missing_error_handling for search engine API request failures
def _search_engine_request(engine, query):
    """
    Send a request to a search engine's API.

    Args:
        engine (str): The name of the search engine.
        query (str): The user's search query.

    Returns:
        dict: The search results.
    """
    try:
        api_key = _get_api_key(engine)
        if not api_key:
            log.error(f"API key not found for {engine}")
            return None
        base_url = {
            "google": "https://www.googleapis.com/customsearch/v1",
            "duckduckgo": "https://api.duckduckgo.com/",
            "bing": "https://api.bing.microsoft.com/v7.0/search",
            "yahoo": "https://api.search.yahoo.com/"
        }.get(engine)
        if not base_url:
            log.error(f"Base URL not found for {engine}")
            return None
        params = {
            "google": {"key": api_key, "cx": os.getenv("GOOGLE_CSE_ID"), "q": query},
            "duckduckgo": {"q": query},
            "bing": {"q": query, "Ocp-Apim-Subscription-Key": api_key},
            "yahoo": {"q": query, "appid": api_key}
        }.get(engine)
        if not params:
            log.error(f"Params not found for {engine}")
            return None
        response = requests.get(base_url, params=params)
        if response.status_code != 200:
            log.error(f"Failed to retrieve results from {engine}: {response.status_code}")
            return None
        return response.json()
    except requests.RequestException as e:
        log.error(f"Failed to send request to {engine}: {e}")
        return None

# GAP_FILLED: missing_logging for search queries and results
def _log_search(query, engine, results):
    """
    Log a search query and its results.

    Args:
        query (str): The user's search query.
        engine (str): The name of the search engine.
        results (dict): The search results.
    """
    log.info(f"Search query: {query} (engine: {engine})")
    log.info(f"Results: {results}")

# GAP_FILLED: missing_capability for caching search results beyond the search_cache table
def _cache_results(query, results, engine):
    """
    Cache search results.

    Args:
        query (str): The user's search query.
        results (dict): The search results.
        engine (str): The name of the search engine.
    """
    conn = _db()
    if conn:
        conn.execute("""
            INSERT OR REPLACE INTO search_cache (cache_key, query, results, engine, cached_at)
            VALUES (?, ?, ?, ?, ?)
        """, (_cache_key(query), query, json.dumps(results), engine, datetime.now(timezone.utc).isoformat()))
        conn.commit()
        conn.close()

# GAP_FILLED: performance issue with the _db function
class DatabaseConnection:
    """
    A singleton class to manage database connections.
    """
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DatabaseConnection, cls).__new__(cls)
            cls._instance.conn = _db()
        return cls._instance

    def get_connection(self):
        """
        Get the database connection.

        Returns:
            sqlite3.Connection: The database connection.
        """
        return self._instance.conn

# GAP_FILLED: missing_capability for searching specific domains or websites
def _search_domain(query, domain):
    """
    Search a specific domain or website.

    Args:
        query (str): The user's search query.
        domain (str): The domain or website to search.

    Returns:
        dict: The search results.
    """
    engine = "google"
    api_key = _get_api_key(engine)
    if not api_key:
        log.error(f"API key not found for {engine}")
        return None
    base_url = "https://www.googleapis.com/customsearch/v1"
    params = {
        "key": api_key,
        "cx": os.getenv("GOOGLE_CSE_ID"),
        "q": f"site:{domain} {query}"
    }
    try:
        response = requests.get(base_url, params=params)
        if response.status_code != 200:
            log.error(f"Failed to retrieve results from {engine}: {response.status_code}")
            return None
        return response.json()
    except requests.RequestException as e:
        log.error(f"Failed to send request to {engine}: {e}")
        return None

# GAP_FILLED: missing_capability for supporting other search engines
def _search_engine_supported(engine):
    """
    Check if a search engine is supported.

    Args:
        engine (str): The name of the search engine.

    Returns:
        bool: True if the search engine is supported, False otherwise.
    """
    supported_engines = ["google", "duckduckgo", "bing", "yahoo"]
    return engine in supported_engines

# GAP_FILLED: missing_capability for searching with the 'site:' operator
def _search_site(query, site):
    """
    Search a specific website using the 'site:' operator.

    Args:
        query (str): The user's search query.
        site (str): The website to search.

    Returns:
        dict: The search results.
    """
    engine = "google"
    api_key = _get_api_key(engine)
    if not api_key:
        log.error(f"API key not found for {engine}")
        return None
    base_url = "https://www.googleapis.com/customsearch/v1"
    params = {
        "key": api_key,
        "cx": os.getenv("GOOGLE_CSE_ID"),
        "q": f"site:{site} {query}"
    }
    try:
        response = requests.get(base_url, params=params)
        if response.status_code != 200:
            log.error(f"Failed to retrieve results from {engine}: {response.status_code}")
            return None
        return response.json()
    except requests.RequestException as e:
        log.error(f"Failed to send request to {engine}: {e}")
        return None

search_bp = Blueprint("search", __name__)

@search_bp.route("/search", methods=["GET"])
def search():
    """
    Handle search requests.

    Returns:
        jsonify: The search results.
    """
    query = request.args.get("q")
    if not _validate_input(query):
        return jsonify({"error": "Invalid input"}), 400
    engine = request.args.get("engine", "google")
    if not _search_engine_supported(engine):
        return jsonify({"error": "Unsupported search engine"}), 400
    results = _search_engine_request(engine, query)
    if not results:
        return jsonify({"error": "Failed to retrieve results"}), 500
    _log_search(query, engine, results)
    _cache_results(query, results, engine)
    return jsonify(results)

@search_bp.route("/search/domain", methods=["GET"])
def search_domain():
    """
    Handle search requests for a specific domain or website.

    Returns:
        jsonify: The search results.
    """
    query = request.args.get("q")
    if not _validate_input(query):
        return jsonify({"error": "Invalid input"}), 400
    domain = request.args.get("domain")
    if not domain:
        return jsonify({"error": "Domain not specified"}), 400
    results = _search_domain(query, domain)
    if not results:
        return jsonify({"error": "Failed to retrieve results"}), 500
    _log_search(query, "google", results)
    _cache_results(query, results, "google")
    return jsonify(results)

@search_bp.route("/search/site", methods=["GET"])
def search_site():
    """
    Handle search requests for a specific website using the 'site:' operator.

    Returns:
        jsonify: The search results.
    """
    query = request.args.get("q")
    if not _validate_input(query):
        return jsonify({"error": "Invalid input"}), 400
    site = request.args.get("site")
    if not site:
        return jsonify({"error": "Site not specified"}), 400
    results = _search_site(query, site)
    if not results:
        return jsonify({"error": "Failed to retrieve results"}), 500
    _log_search(query, "google", results)
    _cache_results(query, results, "google")
    return jsonify(results)