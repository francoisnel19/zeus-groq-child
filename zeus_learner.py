"""
================================================================================
THE ZEUS PROJECT 2026
zeus_learner.py — Autonomous Learning Engine
Architect: Francois Nel · South Africa
================================================================================
- Pulls topics from queue by priority
- Google CSE → DDG → Firecrawl search + scrape
- Extracts clean knowledge → stores in knowledge table
- Scores confidence per article
- Self-expands: after each topic, asks LLM for 5 new related subtopics
- APScheduler: runs every 5 minutes (turbo 4x4 cycle, armv7l-safe)
================================================================================
"""
import os, sqlite3, json, logging, time, re, hashlib
from datetime import datetime, timezone
from flask import Blueprint, request, jsonify

log = logging.getLogger("Zeus.Learner")
ZEUS_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH  = os.path.join(ZEUS_DIR, "zeus.db")

learner_bp  = Blueprint("learner", __name__)
_scheduler  = None
_running    = False
_cycle_count = 0
_last_cycle  = None

def _db():
    c = sqlite3.connect(DB_PATH, timeout=15)
    c.row_factory = sqlite3.Row
    return c

# ── Queue management ──────────────────────────────────────────────
def add_topic(topic, subtopic="", priority=1.0, source="seed"):
    topic = topic.strip()
    if not topic: return False
    conn = _db()
    exists = conn.execute(
        "SELECT id FROM queue WHERE topic=? AND status=\'pending\'", (topic,)
    ).fetchone()
    if not exists:
        conn.execute("""
            INSERT INTO queue (topic, subtopic, priority, status, depth, attempts, created_at, updated_at)
            VALUES (?, ?, ?, \'pending\', \'Deep\', 0, ?, ?)
        """, (topic, subtopic, priority,
              datetime.now(timezone.utc).isoformat(),
              datetime.now(timezone.utc).isoformat()))
        conn.commit()
    conn.close()
    return not bool(exists)

def get_next_batch(batch_size=4):
    conn = _db()
    rows = conn.execute("""
        SELECT id, topic, subtopic, priority FROM queue
        WHERE status=\'pending\' AND attempts < 10
        ORDER BY priority DESC, id ASC
        LIMIT ?
    """, (batch_size,)).fetchall()
    ids = [r["id"] for r in rows]
    if ids:
        conn.execute(
            f"UPDATE queue SET status=\'processing\', updated_at=? WHERE id IN ({','.join('?'*len(ids))})",
            [datetime.now(timezone.utc).isoformat()] + ids
        )
        conn.commit()
    conn.close()
    return [dict(r) for r in rows]

def mark_done(queue_id, success=True):
    conn = _db()
    status = "done" if success else "failed"
    conn.execute(
        "UPDATE queue SET status=?, updated_at=? WHERE id=?",
        (status, datetime.now(timezone.utc).isoformat(), queue_id)
    )
    conn.commit(); conn.close()

def mark_retry(queue_id):
    conn = _db()
    conn.execute("""
        UPDATE queue SET status=\'pending\', attempts=attempts+1, updated_at=? WHERE id=?
    """, (datetime.now(timezone.utc).isoformat(), queue_id))
    conn.commit(); conn.close()

# ── Knowledge storage ─────────────────────────────────────────────
def store_knowledge(topic, content, source_url="", confidence=0.75):
    if not content or len(content.strip()) < 80:
        return 0
    conn = _db()
    # Check for existing
    existing = conn.execute(
        "SELECT id FROM knowledge WHERE topic=?", (topic,)
    ).fetchone()
    stored = 0
    chunks = [content[i:i+4000] for i in range(0, min(len(content), 40000), 4000)]
    for i, chunk in enumerate(chunks):
        t = topic if i == 0 else f"{topic} (part {i+1})"
        if existing and i == 0:
            conn.execute("""
                UPDATE knowledge SET content=?, summary=?, source=?,
                confidence_score=?, last_updated=? WHERE topic=?
            """, (chunk, chunk[:200], source_url, confidence,
                  datetime.now(timezone.utc).isoformat(), topic))
        else:
            conn.execute("""
                INSERT OR IGNORE INTO knowledge
                (topic, content, summary, source, depth, confidence_score,
                 confidence_tier, created_at, last_updated)
                VALUES (?, ?, ?, ?, \'Deep\', ?, ?, ?, ?)
            """, (t, chunk, chunk[:200], source_url, confidence,
                  "confident" if confidence >= 0.75 else "uncertain",
                  datetime.now(timezone.utc).isoformat(),
                  datetime.now(timezone.utc).isoformat()))
        stored += 1
    # Upsert into topics
    conn.execute("""
        INSERT OR IGNORE INTO topics (name, category, priority, learned, confidence_score, last_learned, created_at)
        VALUES (?, \'general\', 1.0, 1, ?, ?, ?)
    """, (topic, confidence, datetime.now(timezone.utc).isoformat(),
          datetime.now(timezone.utc).isoformat()))
    conn.execute("""
        UPDATE topics SET learned=1, confidence_score=?, last_learned=? WHERE name=?
    """, (confidence, datetime.now(timezone.utc).isoformat(), topic))
    conn.commit(); conn.close()
    return stored

# ── LLM: expand topics ────────────────────────────────────────────
def _expand_topics(topic, content_snippet, existing_topics):
    """Ask Groq/Claude for 5 related subtopics to learn next."""
    prompt = f"""You are Zeus, autonomous AI learning system (Francois Nel, The Zeus Project 2026).

You just learned about: "{topic}"

Content preview: {content_snippet[:400]}

Already in learning queue (do NOT suggest these): {", ".join(list(existing_topics)[:20])}

List exactly 5 specific subtopics or related topics Zeus should learn next to deepen understanding.
Format: one topic per line, no numbering, no explanation. Just the topic name.
Keep each under 60 characters. Be specific, not vague."""

    groq_key = os.environ.get("GROQ_API_KEY", "")
    if groq_key:
        try:
            from groq import Groq
            r = Groq(api_key=groq_key).chat.completions.create(
                model=os.environ.get("GROQ_MODEL", "llama3-70b-8192"),
                messages=[{"role":"user","content":prompt}],
                max_tokens=200, temperature=0.7
            )
            raw = r.choices[0].message.content
            topics = [t.strip().lstrip("-•*123456789. ") for t in raw.strip().split("\\n") if t.strip()]
            return [t for t in topics if 4 < len(t) < 80][:5]
        except Exception as e:
            log.warning(f"Groq expand failed: {e}")

    claude_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if claude_key:
        try:
            from anthropic import Anthropic
            r = Anthropic(api_key=claude_key).messages.create(
                model=os.environ.get("LLM_MODEL", "claude-sonnet-4-6"),
                max_tokens=200,
                system="Return only topic names, one per line.",
                messages=[{"role":"user","content":prompt}]
            )
            raw = r.content[0].text
            topics = [t.strip().lstrip("-•*123456789. ") for t in raw.strip().split("\\n") if t.strip()]
            return [t for t in topics if 4 < len(t) < 80][:5]
        except Exception as e:
            log.warning(f"Claude expand failed: {e}")

    return []

# ── Score confidence ──────────────────────────────────────────────
def _score_content(content, topic):
    if not content: return 0.2
    score = 0.5
    words = topic.lower().split()
    hits = sum(1 for w in words if w in content.lower())
    score += (hits / max(len(words), 1)) * 0.25
    if len(content) > 1000: score += 0.10
    if len(content) > 3000: score += 0.10
    if any(kw in content.lower() for kw in ["example","definition","how to","step","method"]):
        score += 0.05
    return min(score, 0.97)

# ── Get existing topic set (for dedup) ───────────────────────────
def _get_existing_topics():
    conn = _db()
    rows = conn.execute("SELECT topic FROM queue WHERE status IN (\'pending\',\'done\') UNION SELECT name FROM topics").fetchall()
    conn.close()
    return set(r[0] for r in rows)

# ── Core learning cycle ───────────────────────────────────────────
def _learn_topic(queue_item):
    from zeus_search import zeus_search, zeus_scrape_url
    topic    = queue_item["topic"]
    qid      = queue_item["id"]
    priority = queue_item.get("priority", 1.0)
    log.info(f"[Learner] Learning: {topic} (pri={priority:.1f})")

    try:
        # 1. Search
        results = zeus_search(topic, num=3, scrape_top=False)
        if not results:
            log.warning(f"No results for: {topic} — trying AI fallback")
            try:
                from groq import Groq
                groq_key = os.environ.get("GROQ_API_KEY","")
                if groq_key:
                    client = Groq(api_key=groq_key)
                    resp = client.chat.completions.create(
                        model="llama-3.1-8b-instant",
                        messages=[{"role":"user","content":
                            f"Explain '{topic}' in 3 clear paragraphs: "
                            f"what it is, why it matters, key concepts."}],
                        max_tokens=512, temperature=0.3
                    )
                    ai_text = resp.choices[0].message.content.strip()
                    if ai_text:
                        conn2 = _db()
                        now = datetime.now(timezone.utc).isoformat()
                        conn2.execute("""INSERT OR IGNORE INTO knowledge
                            (topic, content, source, confidence,
                             created_at, updated_at)
                            VALUES (?,?,?,?,?,?)""",
                            (topic, ai_text, "groq_fallback",
                             0.7, now, now))
                        conn2.commit(); conn2.close()
                        log.info(f"[Learner] AI fallback saved: {topic}")
                        mark_done(qid, success=True)
                        return True
            except Exception as e:
                log.warning(f"[Learner] AI fallback failed: {e}")
            mark_retry(qid); return False

        # 2. Get full content from top results
        content_parts = []
        top_url = ""
        for i, res in enumerate(results[:2]):
            url = res.get("url", "")
            snippet = res.get("snippet", "")
            if url and i == 0:
                top_url = url
                full = zeus_scrape_url(url)
                if full and len(full) > 200:
                    content_parts.append(full[:5000])
                elif snippet:
                    content_parts.append(snippet)
            elif snippet:
                content_parts.append(snippet)

        if not content_parts:
            mark_retry(qid); return False

        content = "\\n\\n".join(content_parts)
        confidence = _score_content(content, topic)

        # 3. Store knowledge
        stored = store_knowledge(topic, content, top_url, confidence)
        log.info(f"[Learner] Stored {stored} chunks for '{topic}' (conf={confidence:.2f})")

        # 4. Self-expand: generate new subtopics
        existing = _get_existing_topics()
        new_topics = _expand_topics(topic, content[:600], existing)
        added = 0
        for nt in new_topics:
            if nt not in existing:
                # Priority: slightly lower than parent, but above base
                new_pri = max(priority * 0.9, 0.8)
                if add_topic(nt, f"expanded from: {topic}", new_pri, "llm_expand"):
                    added += 1
                    log.info(f"[Learner] Queued new topic: {nt} (pri={new_pri:.2f})")

        mark_done(qid, success=True)
        log.info(f"[Learner] ✓ {topic} — {added} new topics queued")
        return True

    except Exception as e:
        log.error(f"[Learner] Failed {topic}: {e}")
        mark_retry(qid)
        return False

def run_cycle():
    """One full learning cycle — pulls batch and learns each topic."""
    global _running, _cycle_count, _last_cycle
    if _running:
        log.info("[Learner] Cycle already running — skipping")
        return
    _running = True
    _cycle_count += 1
    _last_cycle = datetime.now(timezone.utc).isoformat()
    log.info(f"[Learner] ═══ Cycle {_cycle_count} start ═══")
    try:
        batch = get_next_batch(batch_size=4)
        if not batch:
            log.info("[Learner] Queue empty — nothing to learn")
            return
        success = 0
        for item in batch:
            time.sleep(0.5)  # armv7l rate limit guard
            if _learn_topic(item):
                success += 1
        log.info(f"[Learner] ═══ Cycle {_cycle_count} done — {success}/{len(batch)} learned ═══")
    except Exception as e:
        log.error(f"[Learner] Cycle error: {e}")
    finally:
        _running = False

# ── Scheduler ─────────────────────────────────────────────────────
def start_scheduler():
    global _scheduler
    try:
        from apscheduler.schedulers.background import BackgroundScheduler
        _scheduler = BackgroundScheduler(daemon=True)
        _scheduler.add_job(run_cycle, "interval", minutes=5,
                           id="zeus_learn", replace_existing=True,
                           misfire_grace_time=60)
        _scheduler.start()
        log.info("[Learner] APScheduler started — cycle every 5 minutes")
        return True
    except Exception as e:
        log.error(f"[Learner] Scheduler start failed: {e}")
        return False

def stop_scheduler():
    global _scheduler
    if _scheduler and _scheduler.running:
        _scheduler.shutdown(wait=False)
        log.info("[Learner] Scheduler stopped")

# ── API Routes ────────────────────────────────────────────────────
@learner_bp.route("/api/learner/status")
def learner_status():
    conn = _db()
    pending  = conn.execute("SELECT COUNT(*) as c FROM queue WHERE status=\'pending\'").fetchone()["c"]
    done     = conn.execute("SELECT COUNT(*) as c FROM queue WHERE status=\'done\'").fetchone()["c"]
    failed   = conn.execute("SELECT COUNT(*) as c FROM queue WHERE status=\'failed\'").fetchone()["c"]
    total_k  = conn.execute("SELECT COUNT(*) as c FROM knowledge").fetchone()["c"]
    conn.close()
    return jsonify({"status":"ok","scheduler_running":bool(_scheduler and _scheduler.running),
                    "cycle_running":_running,"cycle_count":_cycle_count,"last_cycle":_last_cycle,
                    "queue":{"pending":pending,"done":done,"failed":failed},
                    "knowledge_articles":total_k})

@learner_bp.route("/api/learner/cycle", methods=["POST"])
def trigger_cycle():
    """Manually trigger one learning cycle."""
    import threading
    if _running:
        return jsonify({"status":"busy","message":"Cycle already running"})
    t = threading.Thread(target=run_cycle, daemon=True)
    t.start()
    return jsonify({"status":"ok","message":"Learning cycle triggered"})

@learner_bp.route("/api/learner/queue", methods=["GET"])
def learner_queue():
    conn = _db()
    rows = conn.execute("""
        SELECT topic, subtopic, priority, status, attempts, created_at
        FROM queue ORDER BY priority DESC, id ASC LIMIT 100
    """).fetchall()
    conn.close()
    return jsonify({"status":"ok","queue":[dict(r) for r in rows],"count":len(rows)})

@learner_bp.route("/api/learner/add", methods=["POST"])
def add_topic_api():
    d = request.get_json(silent=True) or {}
    topic = (d.get("topic") or "").strip()
    if not topic: return jsonify({"error":"topic required"}), 400
    added = add_topic(topic, d.get("subtopic",""), float(d.get("priority",1.5)), "api")
    return jsonify({"status":"ok","added":added,"topic":topic})

@learner_bp.route("/api/learner/queue/clear", methods=["DELETE"])
def clear_failed():
    conn = _db()
    conn.execute("DELETE FROM queue WHERE status=\'failed\'")
    conn.commit(); conn.close()
    return jsonify({"status":"ok"})

@learner_bp.route("/api/learner/scheduler/start", methods=["POST"])
def scheduler_start():
    ok = start_scheduler()
    return jsonify({"status":"ok" if ok else "error","running":ok})

@learner_bp.route("/api/learner/scheduler/stop", methods=["POST"])
def scheduler_stop():
    stop_scheduler()
    return jsonify({"status":"ok"})

def init_learner(app):
    app.register_blueprint(learner_bp)
    start_scheduler()
    log.info("[Learner] Autonomous learning engine initialised")
