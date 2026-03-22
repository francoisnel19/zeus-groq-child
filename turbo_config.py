"""
THE ZEUS PROJECT 2026
turbo_config.py — Zeus v4.0 Turbo Learning Configuration
Architect: Francois Nel · South Africa
"""
TURBO = {
    "cycle_interval_minutes":  5,
    "cycle_interval_seconds":  300,
    "topics_per_cycle":        4,
    "subtopics_per_topic":     4,
    "queue_batch_size":        4,
    "max_workers":             2,   # armv7l safe — max 2 threads
    "concurrent_requests":     2,
    "swarm_batch_size":        4,
    "nodes_per_cycle":         4,
    "max_depth_per_topic":     3,
    "min_article_length":      200,
    "priority_user_demand":    2.0,
    "priority_low_confidence": 1.5,
    "priority_new_topic":      1.0,
    "scrape_delay_seconds":    0.5,
    "armv7l_thread_limit":     2,     # Hard cap for 32-bit ARM
    "armv7l_timeout_ms":       500,   # Max per function on armv7l
}
CYCLE_INTERVAL   = TURBO["cycle_interval_minutes"]
TOPICS_PER_CYCLE = TURBO["topics_per_cycle"]
SUBTOPICS_COUNT  = TURBO["subtopics_per_topic"]
MAX_WORKERS      = TURBO["max_workers"]
BATCH_SIZE       = TURBO["queue_batch_size"]
