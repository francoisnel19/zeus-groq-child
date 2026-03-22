#!/usr/bin/env python3
# ============================================================
#  ZEUS SELF-EVOLUTION ENGINE — M57
#  The Zeus Project 2026 — Francois Nel
#  Autonomous Internal Audit + Gap Detection + Gap Filling
#  + Permanent Capability Registration
# ============================================================

import os, sys, ast, json, sqlite3, hashlib, time, traceback, importlib.util
from datetime import datetime
from pathlib import Path
import anthropic
from groq import Groq
try:
    import requests as _requests
except ImportError:
    import urllib.request as _requests
    _requests = None

# ── CONFIG ────────────────────────────────────────────────────────────────────
ZEUS_DIR     = os.path.expanduser("~/zeus_v4")
DB_PATH      = os.path.join(ZEUS_DIR, "zeus.db")
MODULES_DIR = ZEUS_DIR  # patched — scan root
ENV_PATH     = os.path.join(ZEUS_DIR, ".env")
LOG_PATH     = os.path.join(ZEUS_DIR, "logs", "self_evolution.log")
EVOLVED_DIR  = os.path.join(ZEUS_DIR, "evolved_modules")
REPORT_PATH  = os.path.join(ZEUS_DIR, "logs", "evolution_report.json")

AUTHORSHIP = "# The Zeus Project 2026 — Francois Nel\n"

os.makedirs(os.path.join(ZEUS_DIR, "logs"), exist_ok=True)
os.makedirs(EVOLVED_DIR, exist_ok=True)

# ── ENV LOADER ────────────────────────────────────────────────────────────────
def load_env():
    if os.path.exists(ENV_PATH):
        with open(ENV_PATH) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    os.environ.setdefault(k.strip(), v.strip())

load_env()

ANTHROPIC_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
GROQ_KEY      = os.environ.get("GROQ_API_KEY", "")
BLACKBOX_KEY  = os.environ.get("BLACKBOX_API_KEY", "")

# Blackbox.ai API endpoint
BLACKBOX_URL  = "https://api.blackbox.ai/api/chat"
BLACKBOX_CODE_MODEL = "blackboxai"          # general + code
BLACKBOX_FAST_MODEL = "blackboxai/gemini-flash"  # fast analysis

# ── LOGGER ────────────────────────────────────────────────────────────────────
def log(msg, level="INFO"):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] [{level}] {msg}"
    print(line)
    try:
        with open(LOG_PATH, "a") as f:
            f.write(line + "\n")
    except:
        pass

# ── BLACKBOX AI CLIENT ────────────────────────────────────────────────────────
class BlackboxAI:
    """
    Blackbox.ai client — code-specialist layer.
    Acts as the middle tier: Groq (fast) → Blackbox (code) → Claude (synthesis).
    The Zeus Project 2026 — Francois Nel
    """

    def __init__(self, api_key=""):
        self.api_key  = api_key
        self.enabled  = bool(api_key)
        self.session_id = hashlib.md5(f"zeus_{time.time()}".encode()).hexdigest()[:16]

    def chat(self, prompt, model=None, max_tokens=4096, code_mode=True):
        """Send a prompt to Blackbox.ai and return the response text."""
        if not self.enabled:
            return None

        model = model or (BLACKBOX_CODE_MODEL if code_mode else BLACKBOX_FAST_MODEL)

        payload = {
            "messages": [{"role": "user", "content": prompt}],
            "model":    model,
            "max_tokens": max_tokens,
            "stream":   False,
            "agentMode": {"mode": True, "id": "BlackboxAI", "name": "Blackbox AI"} if code_mode else {},
            "codeModelMode": code_mode,
            "id":        self.session_id,
            "userId":    "zeus_v4",
            "isMicMode": False,
        }

        headers = {
            "Content-Type": "application/json",
            "User-Agent":   "Zeus/4.0 (The Zeus Project 2026)",
        }
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        try:
            import requests
            resp = requests.post(BLACKBOX_URL, json=payload, headers=headers, timeout=60)
            if resp.status_code == 200:
                data = resp.json()
                # Handle various response formats
                if isinstance(data, dict):
                    text = (data.get("choices", [{}])[0].get("message", {}).get("content")
                            or data.get("response")
                            or data.get("text")
                            or data.get("message")
                            or "")
                    return text.strip() if text else None
                elif isinstance(data, str):
                    return data.strip()
            else:
                log(f"Blackbox HTTP {resp.status_code}: {resp.text[:100]}", "WARN")
                return None
        except ImportError:
            # Fallback using urllib
            try:
                import urllib.request, urllib.error
                req_data = json.dumps(payload).encode('utf-8')
                req = urllib.request.Request(BLACKBOX_URL, data=req_data, headers=headers, method='POST')
                with urllib.request.urlopen(req, timeout=60) as resp:
                    data = json.loads(resp.read().decode('utf-8'))
                    if isinstance(data, dict):
                        text = (data.get("choices", [{}])[0].get("message", {}).get("content")
                                or data.get("response") or data.get("text") or "")
                        return text.strip() if text else None
            except Exception as e:
                log(f"Blackbox urllib error: {e}", "WARN")
                return None
        except Exception as e:
            log(f"Blackbox error: {e}", "WARN")
            return None

    def analyze_code(self, prompt):
        """Use Blackbox for fast code analysis."""
        return self.chat(prompt, model=BLACKBOX_FAST_MODEL, code_mode=False)

    def generate_code(self, prompt):
        """Use Blackbox for code generation — its strongest suit."""
        return self.chat(prompt, model=BLACKBOX_CODE_MODEL, code_mode=True)

# ── DB HELPERS ────────────────────────────────────────────────────────────────
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def ensure_evolution_tables():
    conn = get_db()
    c = conn.cursor()

    # Capability registry — permanent record of everything Zeus can do
    c.execute("""
        CREATE TABLE IF NOT EXISTS capability_registry (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            module_id   TEXT NOT NULL,
            module_name TEXT NOT NULL,
            capability  TEXT NOT NULL,
            description TEXT,
            code_hash   TEXT,
            source      TEXT DEFAULT 'audit',
            version     INTEGER DEFAULT 1,
            active      INTEGER DEFAULT 1,
            created_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at  DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Gap registry — tracks every gap found and its resolution
    c.execute("""
        CREATE TABLE IF NOT EXISTS gap_registry (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            module_id    TEXT NOT NULL,
            module_name  TEXT NOT NULL,
            gap_type     TEXT NOT NULL,
            gap_desc     TEXT NOT NULL,
            severity     TEXT DEFAULT 'medium',
            status       TEXT DEFAULT 'detected',
            fix_applied  TEXT,
            fix_hash     TEXT,
            genome_id    INTEGER,
            created_at   DATETIME DEFAULT CURRENT_TIMESTAMP,
            resolved_at  DATETIME
        )
    """)

    # Evolution log — every self-improvement cycle
    c.execute("""
        CREATE TABLE IF NOT EXISTS evolution_log (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            cycle           INTEGER NOT NULL,
            phase           TEXT NOT NULL,
            modules_scanned INTEGER DEFAULT 0,
            gaps_found      INTEGER DEFAULT 0,
            gaps_filled     INTEGER DEFAULT 0,
            capabilities_added INTEGER DEFAULT 0,
            genome_segments INTEGER DEFAULT 0,
            summary         TEXT,
            created_at      DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Evolved capabilities — the actual improved code/functions
    c.execute("""
        CREATE TABLE IF NOT EXISTS evolved_capabilities (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            module_id    TEXT NOT NULL,
            function_name TEXT NOT NULL,
            original_code TEXT,
            evolved_code  TEXT NOT NULL,
            improvement   TEXT,
            code_hash     TEXT UNIQUE,
            deployed      INTEGER DEFAULT 0,
            validated     INTEGER DEFAULT 0,
            created_at    DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()
    log("Evolution tables ensured.")

# ── PHASE 1: INTERNAL AUDIT ───────────────────────────────────────────────────
class ZeusAuditor:
    """Scans all Zeus modules and builds a complete capability map."""

    def __init__(self):
        self.capability_map = {}
        self.module_files   = {}
        self.genome_data    = []

    def scan_modules(self):
        log("=== PHASE 1: INTERNAL AUDIT ===")
        log(f"Scanning module directory: {MODULES_DIR}")

        if not os.path.exists(MODULES_DIR):
            log(f"Modules dir not found, scanning ZEUS_DIR: {ZEUS_DIR}", "WARN")
            scan_path = ZEUS_DIR  # scan root directly
        else:
            scan_path = ZEUS_DIR  # patched

        py_files = []
        for root, dirs, files in os.walk(scan_path):
            dirs[:] = [d for d in dirs if d not in ['__pycache__', '.git', 'venv', 'evolved_modules']]
            EXCLUDE = {
                '8_zeus_dashboard.py', 'zeus_final_dashboard.py',
                'zeus_forge2_dashboard.py', 'turbo_config.py',
                '6_zeus_seed.py', 'fix_app.py',
            }
            files = [f for f in files if f not in EXCLUDE]
            EXCLUDE = {
                '8_zeus_dashboard.py', 'zeus_final_dashboard.py',
                'zeus_forge2_dashboard.py', 'turbo_config.py',
                '6_zeus_seed.py', 'fix_app.py',
            }
            files = [f for f in files if f not in EXCLUDE]
            # Skip known installer/config scripts — not stubs
            EXCLUDE = {
                '8_zeus_dashboard.py', 'zeus_final_dashboard.py',
                'zeus_forge2_dashboard.py', 'turbo_config.py',
                '6_zeus_seed.py', 'fix_app.py',
            }
            files = [f for f in files if f not in EXCLUDE]
            for f in files:
                if f.endswith('.py'):
                    py_files.append(os.path.join(root, f))

        log(f"Found {len(py_files)} Python files to audit.")

        for fpath in sorted(py_files):
            self._audit_file(fpath)

        log(f"Audit complete. Mapped {len(self.capability_map)} modules.")
        return self.capability_map

    def _audit_file(self, fpath):
        fname = os.path.basename(fpath)
        rel   = os.path.relpath(fpath, ZEUS_DIR)

        try:
            with open(fpath, 'r', encoding='utf-8', errors='ignore') as f:
                source = f.read()

            tree = ast.parse(source)

            module_info = {
                "file":        rel,
                "path":        fpath,
                "size_bytes":  len(source.encode()),
                "line_count":  len(source.splitlines()),
                "functions":   [],
                "classes":     [],
                "imports":     [],
                "routes":      [],
                "docstring":   ast.get_docstring(tree) or "",
                "source":      source,
                "gaps":        [],
                "capabilities": [],
            }

            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    func_info = {
                        "name":      node.name,
                        "args":      [a.arg for a in node.args.args],
                        "docstring": ast.get_docstring(node) or "",
                        "lineno":    node.lineno,
                        "decorators": [ast.unparse(d) if hasattr(ast, 'unparse') else str(d) for d in node.decorator_list],
                    }
                    module_info["functions"].append(func_info)

                    # Detect Flask routes
                    for dec in func_info["decorators"]:
                        if "route" in dec or "app." in dec or "blueprint" in dec.lower():
                            module_info["routes"].append(node.name)

                elif isinstance(node, ast.ClassDef):
                    class_info = {
                        "name":      node.name,
                        "methods":   [],
                        "docstring": ast.get_docstring(node) or "",
                        "lineno":    node.lineno,
                    }
                    for item in node.body:
                        if isinstance(item, ast.FunctionDef):
                            class_info["methods"].append(item.name)
                    module_info["classes"].append(class_info)

                elif isinstance(node, (ast.Import, ast.ImportFrom)):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            module_info["imports"].append(alias.name)
                    else:
                        mod = node.module or ""
                        for alias in node.names:
                            module_info["imports"].append(f"{mod}.{alias.name}")

            # Detect capability tags from comments/docstrings
            for line in source.splitlines():
                line_stripped = line.strip()
                if line_stripped.startswith("# CAP:") or line_stripped.startswith("# CAPABILITY:"):
                    cap = line_stripped.split(":", 1)[1].strip()
                    module_info["capabilities"].append(cap)

            self.module_files[fname] = module_info
            self.capability_map[rel]  = module_info

        except SyntaxError as e:
            log(f"Syntax error in {fname}: {e}", "WARN")
            self.module_files[fname] = {"file": rel, "path": fpath, "error": str(e), "source": ""}
        except Exception as e:
            log(f"Failed to audit {fname}: {e}", "ERROR")

    def scan_genomes(self):
        log("Scanning genome registry...")
        try:
            conn = get_db()
            c = conn.cursor()

            # Try common genome table names
            for table in ['genomes', 'genome', 'genome_segments', 'genome_registry']:
                try:
                    c.execute(f"SELECT * FROM {table} LIMIT 500")
                    rows = c.fetchall()
                    self.genome_data = [dict(r) for r in rows]
                    log(f"Found {len(self.genome_data)} genome segments in table '{table}'.")
                    break
                except:
                    continue

            conn.close()
        except Exception as e:
            log(f"Genome scan error: {e}", "WARN")

        return self.genome_data

    def save_capabilities_to_db(self):
        log("Saving capability map to database...")
        conn = get_db()
        c = conn.cursor()
        count = 0

        for rel_path, info in self.capability_map.items():
            module_id = rel_path.replace("/", "_").replace(".py", "")
            module_name = os.path.basename(rel_path).replace(".py", "")

            # Register each function as a capability
            for func in info.get("functions", []):
                cap_name = func["name"]
                cap_desc = func.get("docstring", "") or f"Function in {module_name}"
                code_hash = hashlib.md5(f"{module_id}:{cap_name}".encode()).hexdigest()

                try:
                    c.execute("""
                        INSERT OR IGNORE INTO capability_registry
                        (module_id, module_name, capability, description, code_hash, source)
                        VALUES (?, ?, ?, ?, ?, 'audit')
                    """, (module_id, module_name, cap_name, cap_desc, code_hash))
                    count += 1
                except:
                    pass

            # Register each class as a capability
            for cls in info.get("classes", []):
                cap_name = f"class:{cls['name']}"
                cap_desc = cls.get("docstring", "") or f"Class in {module_name}"
                code_hash = hashlib.md5(f"{module_id}:{cap_name}".encode()).hexdigest()
                try:
                    c.execute("""
                        INSERT OR IGNORE INTO capability_registry
                        (module_id, module_name, capability, description, code_hash, source)
                        VALUES (?, ?, ?, ?, ?, 'audit')
                    """, (module_id, module_name, cap_name, cap_desc, code_hash))
                    count += 1
                except:
                    pass

        conn.commit()
        conn.close()
        log(f"Registered {count} capabilities to capability_registry.")


# ── PHASE 2: GAP ANALYSIS ─────────────────────────────────────────────────────
class GapAnalyzer:
    """Uses Claude + Groq to identify gaps in each module."""

    def __init__(self, capability_map, genome_data):
        self.capability_map = capability_map
        self.genome_data    = genome_data
        self.gaps           = {}

        self.claude   = anthropic.Anthropic(api_key=ANTHROPIC_KEY) if ANTHROPIC_KEY else None
        self.groq     = Groq(api_key=GROQ_KEY) if GROQ_KEY else None
        self.blackbox = BlackboxAI(api_key=BLACKBOX_KEY)

        # Log which engines are active
        engines = []
        if self.groq:    engines.append("Groq")
        if self.blackbox.enabled: engines.append("Blackbox.ai")
        if self.claude:  engines.append("Claude")
        log(f"AI Chain active: {' → '.join(engines) if engines else 'NONE'}")

    def _ask_ai(self, prompt, use_groq_first=False):
        """
        3-Engine AI chain:
        Groq (fast analysis) → Blackbox.ai (code specialist) → Claude (highest quality)
        The Zeus Project 2026 — Francois Nel
        """
        # TIER 1: Groq — fastest, good for analysis
        if self.groq and use_groq_first:
            try:
                resp = self.groq.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=2048,
                    temperature=0.3,
                )
                result = resp.choices[0].message.content.strip()
                if result and len(result) > 50:
                    return result, "groq"
            except Exception as e:
                log(f"Groq tier failed: {e}", "WARN")

        # TIER 2: Blackbox.ai — code specialist, middle tier
        if self.blackbox.enabled:
            try:
                result = self.blackbox.analyze_code(prompt)
                if result and len(result) > 50:
                    return result, "blackbox"
            except Exception as e:
                log(f"Blackbox tier failed: {e}", "WARN")

        # TIER 3: Claude — highest quality, final fallback
        if self.claude:
            try:
                resp = self.claude.messages.create(
                    model="claude-sonnet-4-20250514",
                    max_tokens=2048,
                    messages=[{"role": "user", "content": prompt}],
                )
                return resp.content[0].text.strip(), "claude"
            except Exception as e:
                log(f"Claude tier failed: {e}", "WARN")

        return None, None

    def analyze_module(self, rel_path, module_info):
        """Analyze a single module for gaps."""
        fname = os.path.basename(rel_path)

        # Build module summary for AI
        functions = [f["name"] for f in module_info.get("functions", [])]
        classes   = [c["name"] for c in module_info.get("classes", [])]
        imports   = module_info.get("imports", [])[:20]
        routes    = module_info.get("routes", [])
        docstring = module_info.get("docstring", "")[:300]
        line_count = module_info.get("line_count", 0)
        source_snippet = module_info.get("source", "")[:1500]

        if not functions and not classes:
            log(f"Stub module detected (no functions): {fname} — flagging for evolution")
            # Don't skip — return a gap so it gets filled
            return [{"gap_type": "missing_implementation",
                     "gap_desc": f"{fname} is an empty stub — needs full implementation",
                     "severity": "critical",
                     "suggested_fix": "Implement all core functions for this module",
                     "new_function_name": "implement_module"}]

        prompt = f"""You are analyzing a module from Zeus v4.0 — an autonomous self-evolving AI system.
The Zeus Project 2026 — Francois Nel.

MODULE: {fname}
DOCSTRING: {docstring}
LINES: {line_count}
FUNCTIONS: {', '.join(functions) if functions else 'none'}
CLASSES: {', '.join(classes) if classes else 'none'}
IMPORTS: {', '.join(imports) if imports else 'none'}
ROUTES: {', '.join(routes) if routes else 'none'}

SOURCE SNIPPET:
{source_snippet}

Your task: Identify ALL gaps, missing capabilities, incomplete implementations, and improvement opportunities in this module.

Respond ONLY with a JSON array of gap objects, no markdown, no explanation, just pure JSON:
[
  {{
    "gap_type": "missing_function|incomplete_implementation|missing_error_handling|missing_validation|missing_logging|missing_capability|performance|security|integration",
    "gap_desc": "clear description of the gap",
    "severity": "critical|high|medium|low",
    "suggested_fix": "brief description of how to fix it",
    "new_function_name": "optional: name of function to add"
  }}
]

Be thorough. Find every real gap. Return empty array [] if module is complete."""

        response, source = self._ask_ai(prompt, use_groq_first=True)

        if not response:
            log(f"No AI response for {fname}", "WARN")
            return []

        try:
            # Strip any markdown if present
            response = response.strip()
            if response.startswith("```"):
                response = response.split("```")[1]
                if response.startswith("json"):
                    response = response[4:]
            response = response.strip()

            gaps = json.loads(response)
            if isinstance(gaps, list):
                log(f"  {fname}: {len(gaps)} gaps found via {source}")
                return gaps
        except json.JSONDecodeError:
            log(f"JSON parse error for {fname} response", "WARN")

        return []

    def analyze_all(self):
        log("=== PHASE 2: GAP ANALYSIS ===")
        total_gaps = 0

        # Also analyze genomes for improvement opportunities
        genome_summary = ""
        if self.genome_data:
            genome_names = [g.get('name', g.get('segment_name', str(g.get('id', '')))) for g in self.genome_data[:30]]
            genome_summary = f"Active genomes: {', '.join(genome_names)}"
            log(f"Genome context: {len(self.genome_data)} segments loaded.")

        for rel_path, module_info in self.capability_map.items():
            if module_info.get("error"):
                continue

            fname = os.path.basename(rel_path)
            log(f"Analyzing: {fname}")

            gaps = self.analyze_module(rel_path, module_info)
            self.gaps[rel_path] = gaps
            total_gaps += len(gaps)

            # Save gaps to DB
            if gaps:
                self._save_gaps_to_db(rel_path, module_info, gaps)

            time.sleep(0.3)  # Rate limit protection

        log(f"Gap analysis complete. Total gaps found: {total_gaps}")
        return self.gaps

    def _save_gaps_to_db(self, rel_path, module_info, gaps):
        conn = get_db()
        c = conn.cursor()
        module_id   = rel_path.replace("/", "_").replace(".py", "")
        module_name = os.path.basename(rel_path).replace(".py", "")

        for gap in gaps:
            try:
                c.execute("""
                    INSERT INTO gap_registry
                    (module_id, module_name, gap_type, gap_desc, severity, status)
                    VALUES (?, ?, ?, ?, ?, 'detected')
                """, (
                    module_id,
                    module_name,
                    gap.get("gap_type", "unknown"),
                    gap.get("gap_desc", ""),
                    gap.get("severity", "medium"),
                ))
            except Exception as e:
                pass

        conn.commit()
        conn.close()


# ── PHASE 3: GAP FILLING ──────────────────────────────────────────────────────
class GapFiller:
    """Generates code to fill identified gaps and evolves each module."""

    def __init__(self, capability_map, gaps, genome_data):
        self.capability_map = capability_map
        self.gaps           = gaps
        self.genome_data    = genome_data
        self.filled         = {}

        self.claude   = anthropic.Anthropic(api_key=ANTHROPIC_KEY) if ANTHROPIC_KEY else None
        self.groq     = Groq(api_key=GROQ_KEY) if GROQ_KEY else None
        self.blackbox = BlackboxAI(api_key=BLACKBOX_KEY)

    def _ask_ai(self, prompt):
        """
        Code generation chain (quality-first):
        Claude (best quality) → Blackbox.ai (code specialist) → Groq (fallback)
        The Zeus Project 2026 — Francois Nel
        """
        # TIER 1: Claude — highest quality code generation
        if self.claude:
            try:
                resp = self.claude.messages.create(
                    model="claude-sonnet-4-20250514",
                    max_tokens=4096,
                    messages=[{"role": "user", "content": prompt}],
                )
                result = resp.content[0].text.strip()
                if result and len(result) > 100:
                    return result, "claude"
            except Exception as e:
                log(f"Claude code gen failed: {e}", "WARN")

        # TIER 2: Blackbox.ai — code specialist fallback
        if self.blackbox.enabled:
            try:
                result = self.blackbox.generate_code(prompt)
                if result and len(result) > 100:
                    return result, "blackbox"
            except Exception as e:
                log(f"Blackbox code gen failed: {e}", "WARN")

        # TIER 3: Groq — fast fallback
        if self.groq:
            try:
                resp = self.groq.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=4096,
                    temperature=0.2,
                )
                return resp.choices[0].message.content.strip(), "groq"
            except Exception as e:
                log(f"Groq code gen failed: {e}", "WARN")

        return None, None

    def fill_module_gaps(self, rel_path, module_info, gaps):
        """Generate improvement code for a module's gaps."""
        if not gaps:
            return None

        fname  = os.path.basename(rel_path)
        source = module_info.get("source", "")

        # Focus on critical and high severity gaps first
        priority_gaps = [g for g in gaps if g.get("severity") in ("critical", "high")]
        other_gaps    = [g for g in gaps if g.get("severity") not in ("critical", "high")]
        ordered_gaps  = priority_gaps + other_gaps

        gaps_desc = "\n".join([
            f"- [{g.get('severity','?').upper()}] {g.get('gap_type')}: {g.get('gap_desc')} | Fix: {g.get('suggested_fix','')}"
            for g in ordered_gaps[:10]  # Process up to 10 gaps per module
        ])

        prompt = f"""You are Zeus's self-evolution engine — The Zeus Project 2026 — Francois Nel.
You are improving Zeus module: {fname}

CURRENT MODULE SOURCE:
{source[:3000]}

IDENTIFIED GAPS TO FIX:
{gaps_desc}

Generate Python code that fills ALL these gaps. Rules:
1. Start with the authorship header: # The Zeus Project 2026 — Francois Nel
2. Write complete, working Python functions/classes
3. Include proper error handling, logging, and docstrings
4. Code must be compatible with Python 3.9+ on armv7l 32-bit Linux
5. Use only standard library + anthropic + groq + flask + sqlite3 + requests
6. Each new function must have a docstring explaining what gap it fills
7. Add # GAP_FILLED: <gap_description> comment above each fix
8. Make Zeus MORE capable, MORE autonomous, MORE alive

Return ONLY the Python code additions — no markdown, no backticks, just pure Python.
The code will be appended to the existing module."""

        response, ai_source = self._ask_ai(prompt)
        if not response:
            return None

        # Clean response
        response = response.strip()
        for marker in ["```python", "```py", "```"]:
            if response.startswith(marker):
                response = response[len(marker):]
                break
        if response.endswith("```"):
            response = response[:-3]
        response = response.strip()

        # Validate syntax
        try:
            ast.parse(response)
            log(f"  ✓ Valid code generated for {fname} via {ai_source} ({len(response)} chars)")
            return response
        except SyntaxError as e:
            log(f"  ✗ Syntax error in generated code for {fname}: {e}", "WARN")
            return None

    def fill_all_gaps(self):
        log("=== PHASE 3: GAP FILLING ===")
        total_filled = 0

        for rel_path, gaps in self.gaps.items():
            if not gaps:
                continue

            module_info = self.capability_map.get(rel_path, {})
            fname = os.path.basename(rel_path)

            # Resume mode — skip modules already evolved
            if os.environ.get("ZEUS_EVOLUTION_RESUME") == "1":
                evolved_path = os.path.join(EVOLVED_DIR, fname.replace(".py","_evolved.py"))
                if os.path.exists(evolved_path):
                    log(f"  SKIP (already evolved): {fname}")
                    continue

            if os.environ.get("ZEUS_EVOLUTION_RESUME") == "1":
                evolved_path = os.path.join(EVOLVED_DIR, fname.replace(".py","_evolved.py"))
                if os.path.exists(evolved_path):
                    log(f"  SKIP (already evolved): {fname}")
                    continue
            if os.environ.get("ZEUS_EVOLUTION_RESUME") == "1":
                evolved_path = os.path.join(EVOLVED_DIR, fname.replace(".py","_evolved.py"))
                if os.path.exists(evolved_path):
                    log(f"  SKIP (already evolved): {fname}")
                    continue
            log(f"Filling {len(gaps)} gaps in: {fname}")
            new_code = self.fill_module_gaps(rel_path, module_info, gaps)

            if new_code:
                self.filled[rel_path] = {
                    "module_info": module_info,
                    "new_code":    new_code,
                    "gaps_count":  len(gaps),
                }
                self._save_evolved_code(rel_path, module_info, new_code, gaps)
                self._apply_to_module(rel_path, module_info, new_code)
                total_filled += len(gaps)

            time.sleep(0.5)

        log(f"Gap filling complete. Filled gaps in {len(self.filled)} modules.")
        return self.filled

    def _save_evolved_code(self, rel_path, module_info, new_code, gaps):
        """Save evolved code to evolved_modules directory and DB."""
        fname     = os.path.basename(rel_path)
        base_name = fname.replace(".py", "")
        out_path  = os.path.join(EVOLVED_DIR, f"{base_name}_evolved.py")
        code_hash = hashlib.sha256(new_code.encode()).hexdigest()[:16]

        # Save evolved file
        header = f"""{AUTHORSHIP}# ZEUS EVOLVED MODULE: {fname}
# Evolution timestamp: {datetime.now().isoformat()}
# Gaps addressed: {len(gaps)}
# Code hash: {code_hash}
# ─────────────────────────────────────────────────────

"""
        with open(out_path, 'w') as f:
            f.write(header + new_code)

        # Save to DB
        conn = get_db()
        c = conn.cursor()
        module_id = rel_path.replace("/", "_").replace(".py", "")

        try:
            c.execute("""
                INSERT OR IGNORE INTO evolved_capabilities
                (module_id, function_name, evolved_code, improvement, code_hash, deployed, validated)
                VALUES (?, ?, ?, ?, ?, 0, 0)
            """, (
                module_id,
                f"evolution_{base_name}",
                new_code,
                f"Filled {len(gaps)} gaps: {', '.join(g.get('gap_type','?') for g in gaps[:5])}",
                code_hash,
            ))
        except:
            pass

        conn.commit()
        conn.close()

    def _apply_to_module(self, rel_path, module_info, new_code):
        """Append evolved code to the original module file."""
        original_path = module_info.get("path", "")
        if not original_path or not os.path.exists(original_path):
            log(f"  Cannot apply to {rel_path} — file not found", "WARN")
            return

        try:
            evolution_block = f"""

# ══════════════════════════════════════════════════════════════════════
# ZEUS SELF-EVOLUTION INJECTION — {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
{AUTHORSHIP}# ══════════════════════════════════════════════════════════════════════

{new_code}

# ══════════════════════════════════════════════════════════════════════
# END EVOLUTION INJECTION
# ══════════════════════════════════════════════════════════════════════
"""
            with open(original_path, 'a') as f:
                f.write(evolution_block)

            log(f"  ✓ Evolution applied to {os.path.basename(original_path)}")

        except Exception as e:
            log(f"  ✗ Failed to apply evolution to {rel_path}: {e}", "ERROR")


# ── PHASE 4: GENOME REGISTRATION ─────────────────────────────────────────────
class GenomeRegistrar:
    """Registers all improvements as permanent genome segments."""

    def __init__(self, filled_modules, gaps):
        self.filled  = filled_modules
        self.gaps    = gaps

    def _get_genome_table(self):
        """Find the genome table name."""
        conn = get_db()
        c = conn.cursor()
        for table in ['genomes', 'genome', 'genome_segments', 'genome_registry']:
            try:
                c.execute(f"SELECT COUNT(*) FROM {table}")
                conn.close()
                return table
            except:
                continue
        conn.close()
        return None

    def register_all(self):
        log("=== PHASE 4: GENOME REGISTRATION ===")
        genome_table = self._get_genome_table()

        if not genome_table:
            log("No genome table found — creating genome_segments table.", "WARN")
            conn = get_db()
            c = conn.cursor()
            c.execute("""
                CREATE TABLE IF NOT EXISTS genome_segments (
                    id           INTEGER PRIMARY KEY AUTOINCREMENT,
                    name         TEXT UNIQUE NOT NULL,
                    segment_type TEXT DEFAULT 'evolution',
                    content      TEXT,
                    hash         TEXT,
                    source_file  TEXT,
                    active       INTEGER DEFAULT 1,
                    created_at   DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()
            conn.close()
            genome_table = "genome_segments"

        conn     = get_db()
        c        = conn.cursor()
        count    = 0
        cap_count = 0

        for rel_path, data in self.filled.items():
            fname     = os.path.basename(rel_path)
            base_name = fname.replace(".py", "")
            new_code  = data["new_code"]
            gaps      = self.gaps.get(rel_path, [])
            seg_name  = f"evolution_{base_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            seg_hash  = hashlib.sha256(new_code.encode()).hexdigest()

            # Register as genome segment
            try:
                c.execute(f"""
                    INSERT OR IGNORE INTO {genome_table}
                    (name, segment_type, content, hash, source_file, active)
                    VALUES (?, 'self_evolution', ?, ?, ?, 1)
                """, (seg_name, new_code, seg_hash, rel_path))
                count += 1
            except Exception as e:
                # Try minimal insert
                try:
                    cols = self._get_table_columns(genome_table)
                    log(f"Genome table columns: {cols}", "WARN")
                    # Try with just name and content
                    c.execute(f"INSERT OR IGNORE INTO {genome_table} (name) VALUES (?)", (seg_name,))
                    count += 1
                except Exception as e2:
                    log(f"Genome insert failed for {fname}: {e2}", "ERROR")

            # Register new capabilities from the evolution
            module_id   = rel_path.replace("/", "_").replace(".py", "")
            module_name = base_name

            try:
                evolved_tree = ast.parse(new_code)
                for node in ast.walk(evolved_tree):
                    if isinstance(node, ast.FunctionDef):
                        cap_hash = hashlib.md5(f"evolved:{module_id}:{node.name}".encode()).hexdigest()
                        c.execute("""
                            INSERT OR IGNORE INTO capability_registry
                            (module_id, module_name, capability, description, code_hash, source)
                            VALUES (?, ?, ?, ?, ?, 'self_evolution')
                        """, (
                            module_id,
                            module_name,
                            node.name,
                            ast.get_docstring(node) or f"Self-evolved function filling gap in {module_name}",
                            cap_hash,
                        ))
                        cap_count += 1
            except:
                pass

            # Update gap registry to resolved
            c.execute("""
                UPDATE gap_registry
                SET status = 'resolved', resolved_at = CURRENT_TIMESTAMP
                WHERE module_id = ? AND status = 'detected'
            """, (module_id,))

        conn.commit()
        conn.close()
        log(f"Registered {count} evolution genome segments.")
        log(f"Registered {cap_count} new evolved capabilities.")
        return count, cap_count

    def _get_table_columns(self, table):
        conn = get_db()
        c = conn.cursor()
        c.execute(f"PRAGMA table_info({table})")
        cols = [row[1] for row in c.fetchall()]
        conn.close()
        return cols


# ── PHASE 5: CAPABILITY SYNTHESIS ────────────────────────────────────────────
class CapabilitySynthesizer:
    """
    Final phase: synthesizes all gaps, genomes, and improvements
    into a unified capability upgrade — makes Zeus MORE than he was.
    """

    def __init__(self, capability_map, gaps, genome_data, filled):
        self.capability_map = capability_map
        self.gaps           = gaps
        self.genome_data    = genome_data
        self.filled         = filled
        self.claude   = anthropic.Anthropic(api_key=ANTHROPIC_KEY) if ANTHROPIC_KEY else None
        self.groq     = Groq(api_key=GROQ_KEY) if GROQ_KEY else None
        self.blackbox = BlackboxAI(api_key=BLACKBOX_KEY)

    def _ask_ai(self, prompt):
        """
        Synthesis chain — Claude leads, Blackbox backs up, Groq catches.
        The Zeus Project 2026 — Francois Nel
        """
        if self.claude:
            try:
                resp = self.claude.messages.create(
                    model="claude-sonnet-4-20250514",
                    max_tokens=4096,
                    messages=[{"role": "user", "content": prompt}],
                )
                result = resp.content[0].text.strip()
                if result: return result
            except Exception as e:
                log(f"Claude synthesis error: {e}", "WARN")

        if self.blackbox.enabled:
            try:
                result = self.blackbox.generate_code(prompt)
                if result: return result
            except Exception as e:
                log(f"Blackbox synthesis error: {e}", "WARN")

        if self.groq:
            try:
                resp = self.groq.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=4096,
                )
                return resp.choices[0].message.content.strip()
            except:
                pass
        return None

    def generate_master_capability_module(self):
        """Generate a new master capability module that synthesizes all improvements."""
        log("=== PHASE 5: CAPABILITY SYNTHESIS ===")

        # Build summary of everything
        total_functions = sum(len(m.get("functions", [])) for m in self.capability_map.values())
        total_classes   = sum(len(m.get("classes", [])) for m in self.capability_map.values())
        total_gaps      = sum(len(g) for g in self.gaps.values())
        total_filled    = len(self.filled)
        genome_count    = len(self.genome_data)

        genome_names = []
        for g in self.genome_data[:20]:
            name = g.get('name') or g.get('segment_name') or g.get('sdk_name') or str(g.get('id', ''))
            if name:
                genome_names.append(name)

        module_names = [os.path.basename(p).replace('.py','') for p in list(self.capability_map.keys())[:30]]

        prompt = f"""You are Zeus's master synthesis engine — The Zeus Project 2026 — Francois Nel.

Zeus v4.0 has just completed a full self-audit and gap-filling cycle:
- Modules audited: {len(self.capability_map)}
- Total functions mapped: {total_functions}
- Total classes mapped: {total_classes}  
- Total gaps found: {total_gaps}
- Modules evolved: {total_filled}
- Active genome segments: {genome_count}
- Genome names: {', '.join(genome_names[:15])}
- Module names: {', '.join(module_names[:20])}

Generate a new Python master capability module called zeus_master_capabilities.py that:

1. Starts with: # The Zeus Project 2026 — Francois Nel
2. Creates a ZeusMasterCapabilities class that:
   - Has a complete capability registry with all Zeus's core abilities
   - Can query what Zeus can and cannot do
   - Has a self_assess() method that evaluates Zeus's current capability level
   - Has a identify_next_evolution() method that determines what Zeus should learn/build next
   - Has a synthesize_genome_knowledge() method that combines all genome knowledge
   - Has a broadcast_capability_update() method that notifies all modules of new capabilities
   - Has a register_new_capability(name, description, code) method
   - Has a get_capability_score() method returning 0-100 completeness score
3. Includes integration with Flask to expose /api/capabilities, /api/evolution/status, /api/gaps endpoints
4. Includes autonomous_evolution_loop() that runs every 6 hours and triggers self-improvement
5. Uses Zeus's existing SQLite DB at {DB_PATH}
6. Must work on armv7l 32-bit Python 3.9+

Make Zeus MORE capable, MORE autonomous, MORE alive than before.
Return ONLY pure Python code, no markdown."""

        response = self._ask_ai(prompt)
        if not response:
            log("No synthesis response from AI", "WARN")
            return

        # Clean
        response = response.strip()
        for marker in ["```python", "```py", "```"]:
            if response.startswith(marker):
                response = response[len(marker):]
                break
        if response.endswith("```"):
            response = response[:-3]
        response = response.strip()

        # Validate
        try:
            ast.parse(response)
            log("✓ Master capability module syntax valid.")
        except SyntaxError as e:
            log(f"✗ Syntax error in master module: {e}", "WARN")
            return

        # Save master module
        master_path = os.path.join(ZEUS_DIR, "zeus_master_capabilities.py")
        with open(master_path, 'w') as f:
            f.write(f"{AUTHORSHIP}# ZEUS MASTER CAPABILITIES MODULE\n")
            f.write(f"# Generated: {datetime.now().isoformat()}\n")
            f.write(f"# Evolution cycle complete\n\n")
            f.write(response)

        log(f"✓ Master capability module saved: {master_path}")

        # Register as genome
        self._register_master_genome(response, master_path)

    def _register_master_genome(self, code, path):
        """Register master capabilities as highest-priority genome segment."""
        conn = get_db()
        c = conn.cursor()
        seg_hash = hashlib.sha256(code.encode()).hexdigest()
        seg_name = f"master_capabilities_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        for table in ['genomes', 'genome', 'genome_segments', 'genome_registry']:
            try:
                c.execute(f"""
                    INSERT OR IGNORE INTO {table}
                    (name, segment_type, content, hash, source_file, active)
                    VALUES (?, 'master_capability', ?, ?, ?, 1)
                """, (seg_name, code, seg_hash, path))
                conn.commit()
                log(f"✓ Master genome registered in table '{table}'.")
                break
            except:
                continue

        conn.close()


# ── EVOLUTION REPORT ──────────────────────────────────────────────────────────
def generate_report(auditor, analyzer, filler, registrar_counts, start_time):
    log("=== GENERATING EVOLUTION REPORT ===")

    total_gaps   = sum(len(g) for g in analyzer.gaps.values())
    total_filled = len(filler.filled)
    duration     = time.time() - start_time

    report = {
        "evolution_cycle":    datetime.now().isoformat(),
        "author":             "Francois Nel — The Zeus Project 2026",
        "duration_seconds":   round(duration, 2),
        "modules_audited":    len(auditor.capability_map),
        "total_functions":    sum(len(m.get("functions", [])) for m in auditor.capability_map.values()),
        "total_classes":      sum(len(m.get("classes", [])) for m in auditor.capability_map.values()),
        "genome_segments":    len(auditor.genome_data),
        "gaps_found":         total_gaps,
        "modules_evolved":    total_filled,
        "genome_registered":  registrar_counts[0],
        "capabilities_added": registrar_counts[1],
        "gap_breakdown": {},
        "evolved_modules":    list(filler.filled.keys()),
    }

    # Gap severity breakdown
    for rel_path, gaps in analyzer.gaps.items():
        for gap in gaps:
            sev = gap.get("severity", "unknown")
            report["gap_breakdown"][sev] = report["gap_breakdown"].get(sev, 0) + 1

    # Save report
    with open(REPORT_PATH, 'w') as f:
        json.dump(report, f, indent=2)

    # Save to DB
    conn = get_db()
    c = conn.cursor()
    try:
        cycle_num = int(time.time())
        c.execute("""
            INSERT INTO evolution_log
            (cycle, phase, modules_scanned, gaps_found, gaps_filled, capabilities_added, genome_segments, summary)
            VALUES (?, 'complete', ?, ?, ?, ?, ?, ?)
        """, (
            cycle_num,
            report["modules_audited"],
            total_gaps,
            total_filled,
            registrar_counts[1],
            registrar_counts[0],
            json.dumps(report),
        ))
        conn.commit()
    except Exception as e:
        log(f"Failed to save evolution log: {e}", "WARN")
    conn.close()

    log(f"\n{'='*60}")
    log(f"  ZEUS SELF-EVOLUTION COMPLETE")
    log(f"{'='*60}")
    log(f"  Modules audited:      {report['modules_audited']}")
    log(f"  Functions mapped:     {report['total_functions']}")
    log(f"  Genome segments:      {report['genome_segments']}")
    log(f"  Gaps found:           {total_gaps}")
    log(f"  Modules evolved:      {total_filled}")
    log(f"  Genome segments added:{registrar_counts[0]}")
    log(f"  Capabilities added:   {registrar_counts[1]}")
    log(f"  Duration:             {round(duration,1)}s")
    log(f"  Report:               {REPORT_PATH}")
    log(f"{'='*60}")
    log(f"  The Zeus Project 2026 — Francois Nel")
    log(f"{'='*60}\n")

    return report


# ── FLASK INTEGRATION ROUTES ──────────────────────────────────────────────────
FLASK_ROUTES = '''
# ── ZEUS SELF-EVOLUTION ROUTES (add to your Flask app) ──────────────────────
# The Zeus Project 2026 — Francois Nel
# AI Chain: Groq → Blackbox.ai → Claude (analysis)
#           Claude → Blackbox.ai → Groq (code generation)

from zeus_self_evolution import (
    ZeusAuditor, GapAnalyzer, GapFiller,
    GenomeRegistrar, CapabilitySynthesizer,
    ensure_evolution_tables, generate_report
)
import threading

@app.route('/api/evolution/start', methods=['POST'])
def start_evolution():
    """Trigger a full self-evolution cycle."""
    def run_evolution():
        # Apply flags to environment
    import os
    if args.skip_claude:
        os.environ["ANTHROPIC_API_KEY"] = ""
        print("[INFO] Claude disabled — Groq only mode")
    if args.force_groq:
        print("[INFO] Force-Groq mode active")
    if args.resume:
        os.environ["ZEUS_EVOLUTION_RESUME"] = "1"
        print("[INFO] Resume mode — already-evolved modules will be skipped")

    import os as _os
    if hasattr(args, 'local') and args.local:
        _os.environ["ANTHROPIC_API_KEY"] = ""
        _os.environ["GROQ_API_KEY"] = ""
        print("[INFO] LOCAL MODE — zero API tokens")
    if hasattr(args, 'skip_claude') and args.skip_claude:
        _os.environ["ANTHROPIC_API_KEY"] = ""
        print("[INFO] Claude disabled")
    if hasattr(args, 'force_groq') and args.force_groq:
        print("[INFO] Force-Groq mode")
    if hasattr(args, 'resume') and args.resume:
        _os.environ["ZEUS_EVOLUTION_RESUME"] = "1"
        print("[INFO] Resume mode")
    run_full_evolution()
    thread = threading.Thread(target=run_evolution, daemon=True)
    thread.start()
    return jsonify({"status": "evolution_started", "message": "Zeus is evolving..."})

@app.route('/api/evolution/status', methods=['GET'])
def evolution_status():
    """Get current evolution status."""
    try:
        conn = get_db()
        c = conn.cursor()
        c.execute("SELECT * FROM evolution_log ORDER BY created_at DESC LIMIT 1")
        row = c.fetchone()
        conn.close()
        if row:
            return jsonify(dict(row))
        return jsonify({"status": "no_evolution_run_yet"})
    except:
        return jsonify({"status": "error"})

@app.route('/api/capabilities', methods=['GET'])
def list_capabilities():
    """List all registered capabilities."""
    try:
        conn = get_db()
        c = conn.cursor()
        c.execute("SELECT module_name, capability, description, source FROM capability_registry ORDER BY module_name LIMIT 500")
        rows = [dict(r) for r in c.fetchall()]
        conn.close()
        return jsonify({"total": len(rows), "capabilities": rows})
    except Exception as e:
        return jsonify({"error": str(e)})

@app.route('/api/gaps', methods=['GET'])
def list_gaps():
    """List all detected and resolved gaps."""
    try:
        conn = get_db()
        c = conn.cursor()
        c.execute("SELECT * FROM gap_registry ORDER BY severity DESC, created_at DESC LIMIT 200")
        rows = [dict(r) for r in c.fetchall()]
        conn.close()
        return jsonify({"total": len(rows), "gaps": rows})
    except Exception as e:
        return jsonify({"error": str(e)})
'''


# ── MAIN EVOLUTION RUNNER ─────────────────────────────────────────────────────
def run_full_evolution():
    """Execute the complete Zeus self-evolution pipeline."""
    start_time = time.time()

    log("\n" + "="*60)
    log("  ZEUS SELF-EVOLUTION ENGINE ACTIVATED")
    log("  The Zeus Project 2026 — Francois Nel")
    log("="*60 + "\n")

    if not ANTHROPIC_KEY and not GROQ_KEY and not BLACKBOX_KEY:
        log("ERROR: No API keys found. Check ~/zeus_v4/.env", "ERROR")
        log("Required: ANTHROPIC_API_KEY and/or GROQ_API_KEY and/or BLACKBOX_API_KEY", "ERROR")
        return

    # Log active engines
    engines = []
    if GROQ_KEY:      engines.append("Groq")
    if BLACKBOX_KEY:  engines.append("Blackbox.ai")
    if ANTHROPIC_KEY: engines.append("Claude")
    log(f"Active AI engines: {' + '.join(engines)}")
    log(f"Chain (analysis):  Groq → Blackbox.ai → Claude")
    log(f"Chain (code gen):  Claude → Blackbox.ai → Groq")

    # Ensure DB tables exist
    ensure_evolution_tables()

    # PHASE 1: AUDIT
    auditor = ZeusAuditor()
    auditor.scan_modules()
    auditor.scan_genomes()
    auditor.save_capabilities_to_db()

    if not auditor.capability_map:
        log("No modules found to audit. Check ZEUS_DIR path.", "ERROR")
        return

    # PHASE 2: GAP ANALYSIS
    analyzer = GapAnalyzer(auditor.capability_map, auditor.genome_data)
    analyzer.analyze_all()

    # PHASE 3: GAP FILLING
    filler = GapFiller(auditor.capability_map, analyzer.gaps, auditor.genome_data)
    filler.fill_all_gaps()

    # PHASE 4: GENOME REGISTRATION
    registrar = GenomeRegistrar(filler.filled, analyzer.gaps)
    counts    = registrar.register_all()

    # PHASE 5: CAPABILITY SYNTHESIS
    synthesizer = CapabilitySynthesizer(
        auditor.capability_map,
        analyzer.gaps,
        auditor.genome_data,
        filler.filled
    )
    synthesizer.generate_master_capability_module()

    # REPORT
    generate_report(auditor, analyzer, filler, counts, start_time)

    # Save Flask routes hint
    routes_path = os.path.join(ZEUS_DIR, "evolution_routes.py")
    with open(routes_path, 'w') as f:
        f.write(f"{AUTHORSHIP}# Evolution API Routes\n{FLASK_ROUTES}")
    log(f"Flask routes saved to: {routes_path}")

    log("Zeus self-evolution cycle complete. He is more than he was.")


# ── ENTRY POINT ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Zeus Self-Evolution Engine — The Zeus Project 2026 — Francois Nel"
    )
    parser.add_argument("--audit-only",  action="store_true", help="Only audit, no gap filling")
    parser.add_argument("--module",      type=str,            help="Evolve a specific module only")
    parser.add_argument("--report-only", action="store_true", help="Show last evolution report")
    parser.add_argument("--skip-claude", action="store_true", help="Skip Claude, use Groq only")
    parser.add_argument("--force-groq", action="store_true", help="Force Groq as primary engine")
    parser.add_argument("--resume", action="store_true", help="Skip already-evolved modules")
    args = parser.parse_args()

    if args.report_only:
        if os.path.exists(REPORT_PATH):
            with open(REPORT_PATH) as f:
                print(json.dumps(json.load(f), indent=2))
        else:
            print("No evolution report found. Run evolution first.")
        sys.exit(0)

    if args.audit_only:
        ensure_evolution_tables()
        auditor = ZeusAuditor()
        auditor.scan_modules()
        auditor.scan_genomes()
        auditor.save_capabilities_to_db()
        print(f"\nAudit complete:")
        print(f"  Modules: {len(auditor.capability_map)}")
        print(f"  Genomes: {len(auditor.genome_data)}")
        total_funcs = sum(len(m.get('functions',[])) for m in auditor.capability_map.values())
        print(f"  Functions: {total_funcs}")
        sys.exit(0)

    # Apply flags to environment
    import os
    if args.skip_claude:
        os.environ["ANTHROPIC_API_KEY"] = ""
        print("[INFO] Claude disabled — Groq only mode")
    if args.force_groq:
        print("[INFO] Force-Groq mode active")
    if args.resume:
        os.environ["ZEUS_EVOLUTION_RESUME"] = "1"
        print("[INFO] Resume mode — already-evolved modules will be skipped")

    run_full_evolution()
