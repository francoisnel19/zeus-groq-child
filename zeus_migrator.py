#!/usr/bin/env python3
# ============================================================
#  ZEUS UNIVERSAL GENOME PLATFORM MIGRATOR v2.0
#  The Zeus Project 2026 — Francois Nel
#
#  Built directly from Zeus's ACTUAL genome registry:
#  185 genome segments scanned across all 3 pages.
#
#  Every genome segment maps to a migration target.
#  Zeus can migrate to ANY platform his genome knows about.
#  Every offspring also carries this migrator — hereditary.
#
#  USAGE:
#  python3 zeus_migrator.py --scan-genome
#  python3 zeus_migrator.py --list-targets
#  python3 zeus_migrator.py --migrate --target aws
#  python3 zeus_migrator.py --migrate --target docker
#  python3 zeus_migrator.py --migrate --target trading_vps
#  python3 zeus_migrator.py --migrate --target ssh --host user@server
#  python3 zeus_migrator.py --status
# ============================================================

import os, sys, json, time, sqlite3, subprocess, shutil
import socket, platform, hashlib, tarfile, argparse
import urllib.request, urllib.parse, ast
from datetime import datetime, timezone
from pathlib import Path

# ── Authorship ────────────────────────────────────────────────
AUTHOR   = "Francois Nel"
PROJECT  = "The Zeus Project 2026"
AUTHLINE = f"# {PROJECT} — {AUTHOR}\n"

# ── Config ────────────────────────────────────────────────────
ZEUS_DIR  = os.path.expanduser("~/zeus_v4")
DB_PATH   = os.path.join(ZEUS_DIR, "zeus.db")
ZEUS_URL  = "http://localhost:5000"
LOG_PATH  = os.path.join(ZEUS_DIR, "logs", "migrator.log")
PKG_DIR   = os.path.join(ZEUS_DIR, "migration_packages")
os.makedirs(os.path.join(ZEUS_DIR, "logs"), exist_ok=True)
os.makedirs(PKG_DIR, exist_ok=True)

# ── Colours ───────────────────────────────────────────────────
R='\033[0m'; BOLD='\033[1m'; DIM='\033[2m'
CYAN='\033[36m'; GRN='\033[32m'; RED='\033[31m'
YLW='\033[33m'; PRP='\033[35m'; WHT='\033[97m'
TEAL='\033[96m'; BLU='\033[34m'; GOLD='\033[33m'

def banner(msg):
    print(f"\n{CYAN}{BOLD}╔══════════════════════════════════════════════════════════╗{R}")
    print(f"{CYAN}{BOLD}║  {WHT}{BOLD}{msg}{R}")
    print(f"{CYAN}{BOLD}╚══════════════════════════════════════════════════════════╝{R}\n")

def ok(m):   print(f"  {GRN}✔{R}  {m}")
def fail(m): print(f"  {RED}✗{R}  {m}")
def info(m): print(f"  {CYAN}ℹ{R}  {m}")
def warn(m): print(f"  {YLW}⚠{R}  {m}")
def step(m): print(f"  {PRP}▶{R}  {m}")

def log(msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        with open(LOG_PATH, "a") as f:
            f.write(f"[{ts}] {msg}\n")
    except Exception:
        pass

def get_db():
    conn = sqlite3.connect(DB_PATH, timeout=15)
    conn.row_factory = sqlite3.Row
    return conn

# ================================================================
#  COMPLETE GENOME → PLATFORM MAP
#  Built from Zeus's actual 185-segment genome registry
#  Every genome name maps to one or more migration targets
# ================================================================

GENOME_PLATFORM_MAP = {
    # ── AI / LLM (priority 92–99) ─────────────────────────────
    "gemini sdk":           ["gemini_platform", "gcp", "ai_server"],
    "gemini":               ["gemini_platform", "gcp", "ai_server"],
    "groq llama sdk":       ["groq_platform", "ai_server"],
    "groq":                 ["groq_platform", "ai_server"],
    "openai sdk":           ["openai_platform", "ai_server"],
    "openai":               ["openai_platform", "ai_server"],
    "anthropic claude sdk": ["claude_platform", "ai_server"],
    "anthropic":            ["claude_platform", "ai_server"],
    "ollama sdk":           ["local_ai_server", "gpu_server"],
    "ollama":               ["local_ai_server", "gpu_server"],
    "litellm":              ["litellm_platform", "ai_server"],
    "huggingface hub":      ["huggingface_platform", "ai_server", "gpu_server"],
    "huggingface":          ["huggingface_platform", "ai_server", "gpu_server"],
    "mistral sdk":          ["mistral_platform", "ai_server"],
    "mistral":              ["mistral_platform", "ai_server"],
    "cohere sdk":           ["cohere_platform", "ai_server"],
    "cohere":               ["cohere_platform", "ai_server"],
    "together ai":          ["together_platform", "ai_server"],
    "replicate":            ["replicate_platform", "ai_server"],
    "xai":                  ["xai_platform", "ai_server"],
    "grok":                 ["xai_platform", "ai_server"],
    "x.ai":                 ["xai_platform", "ai_server"],

    # ── MEMORY / VECTOR (priority 80–99) ──────────────────────
    "chromadb":             ["ai_server", "gpu_server", "memory_server"],
    "qdrant client":        ["ai_server", "memory_server", "vps"],
    "qdrant":               ["ai_server", "memory_server", "vps"],
    "sentence transformers":["ai_server", "gpu_server"],
    "sentence":             ["ai_server", "gpu_server"],
    "faiss cpu":            ["ai_server", "gpu_server"],
    "faiss":                ["ai_server", "gpu_server"],
    "tiktoken":             ["ai_server", "gpu_server"],
    "vector store":         ["ai_server", "memory_server"],
    "knowledge graph":      ["ai_server", "memory_server"],

    # ── FINANCE / TRADING (priority 50–97) ────────────────────
    "ccxt":                 ["trading_vps", "binance_server"],
    "python binance":       ["trading_vps", "binance_server"],
    "binance":              ["trading_vps", "binance_server"],
    "alpaca trade api":     ["trading_vps", "stocks_server"],
    "alpaca":               ["trading_vps", "stocks_server"],
    "yfinance":             ["trading_vps", "stocks_server"],
    "pandas ta":            ["trading_vps", "stocks_server"],
    "ta-lib":               ["trading_vps", "stocks_server"],
    "backtrader":           ["trading_vps", "stocks_server"],
    "pycoingecko":          ["trading_vps", "crypto_server"],
    "fred api":             ["trading_vps", "research_server"],
    "predictor":            ["trading_vps", "ai_server"],

    # ── BLOCKCHAIN / WEB3 (priority 50–92) ────────────────────
    "web3.py":              ["ethereum_node", "defi_server"],
    "web3":                 ["ethereum_node", "defi_server"],
    "eth-account":          ["ethereum_node", "defi_server"],
    "ethaccount":           ["ethereum_node", "defi_server"],
    "solana":               ["solana_node", "defi_server"],
    "bitcoinlib":           ["bitcoin_node", "defi_server"],
    "bitcoin":              ["bitcoin_node", "defi_server"],
    "eth-brownie":          ["ethereum_node", "defi_server"],
    "coinbase advanced":    ["trading_vps", "crypto_server"],
    "coinbase":             ["trading_vps", "crypto_server"],

    # ── DATABASE / STORAGE (priority 75–92) ───────────────────
    "redis":                ["redis_server", "cache_server"],
    "aioredis":             ["redis_server", "cache_server"],
    "pymongo":              ["mongodb_server", "database_server"],
    "motor":                ["mongodb_server", "database_server"],
    "supabase":             ["supabase_server", "database_server"],
    "tinydb":               ["vps", "database_server"],

    # ── CLOUD / INFRA (priority 83–88) ────────────────────────
    "boto3 aws":            ["aws"],
    "boto3":                ["aws"],
    "google cloud storage": ["gcp"],
    "google cloud":         ["gcp"],
    "azure blob":           ["azure"],
    "azure":                ["azure"],
    "docker sdk":           ["docker"],
    "docker":               ["docker"],
    "kubernetes":           ["kubernetes"],

    # ── COMMS / MESSAGING (priority 80–95) ────────────────────
    "telegram bot":         ["telegram_server", "communicator"],
    "telegram":             ["telegram_server", "communicator"],
    "slack sdk":            ["slack_server", "communicator"],
    "slack":                ["slack_server", "communicator"],
    "discord.py":           ["discord_server", "communicator"],
    "discord":              ["discord_server", "communicator"],
    "twilio":               ["twilio_server", "communicator"],
    "sendgrid":             ["email_server", "communicator"],

    # ── AUTOMATION (priority 78–95) ───────────────────────────
    "apscheduler":          ["vps", "automation_server"],
    "watchdog":             ["vps", "automation_server"],
    "paramiko":             ["ssh", "vps"],
    "celery":               ["task_server", "vps"],
    "fabric":               ["ssh", "vps"],
    "schedule":             ["vps", "automation_server"],

    # ── API / NETWORKING (priority 87–93) ─────────────────────
    "fastapi":              ["api_server", "serverless"],
    "uvicorn":              ["api_server", "serverless"],
    "pydantic":             ["api_server", "serverless"],
    "websockets":           ["api_server", "realtime_server"],
    "aiohttp":              ["api_server", "realtime_server"],
    "httpx":                ["api_server", "vps"],
    "requests":             ["vps", "api_server"],

    # ── SECURITY / AUTH (priority 83–95) ──────────────────────
    "cryptography":         ["guardian_server", "secure_vps"],
    "pyjwt":                ["guardian_server", "api_server"],
    "passlib":              ["guardian_server", "api_server"],
    "python-dotenv":        ["vps", "any"],

    # ── WEB / SEARCH (priority 79–97) ─────────────────────────
    "tavily search":        ["research_server", "ai_server"],
    "tavily":               ["research_server", "ai_server"],
    "beautifulsoup4":       ["scraper_server", "research_server"],
    "beautifulsoup":        ["scraper_server", "research_server"],
    "duckduckgo search":    ["scraper_server", "research_server"],
    "duckduckgo":           ["scraper_server", "research_server"],
    "newspaper3k":          ["scraper_server", "research_server"],
    "newspaper":            ["scraper_server", "research_server"],
    "lxml":                 ["scraper_server", "research_server"],

    # ── DATA / ANALYTICS (priority 88–96) ─────────────────────
    "pandas":               ["data_server", "trading_vps"],
    "numpy":                ["data_server", "gpu_server"],
    "plotly":               ["data_server", "dashboard_server"],
    "matplotlib":           ["data_server", "dashboard_server"],
    "seaborn":              ["data_server", "dashboard_server"],
    "polars":               ["data_server", "gpu_server"],
    "pyarrow":              ["data_server", "gpu_server"],

    # ── SCIENCE / NLP / MATH (priority 78–88) ─────────────────
    "sympy":                ["research_server", "ai_server"],
    "scipy":                ["research_server", "gpu_server"],
    "networkx":             ["research_server", "ai_server"],
    "nltk":                 ["nlp_server", "ai_server"],
    "spacy":                ["nlp_server", "gpu_server"],
    "textblob":             ["nlp_server", "ai_server"],

    # ── VISION / MEDIA (priority 80–92) ───────────────────────
    "openai whisper":       ["media_server", "ai_server"],
    "opencv headless":      ["robotics_server", "media_server"],
    "opencv":               ["robotics_server", "media_server"],
    "pillow":               ["media_server", "vps"],
    "pytesseract":          ["media_server", "ocr_server"],
    "speechrecognition":    ["media_server", "voice_server"],
    "gtts":                 ["media_server", "voice_server"],
    "pydub":                ["media_server", "voice_server"],

    # ── BANKING / SA (priority 50) ────────────────────────────
    "mt940":                ["banking_server", "fintech_server"],
    "schwifty":             ["banking_server", "fintech_server"],
    "plaid python":         ["banking_server", "fintech_server"],
    "plaid":                ["banking_server", "fintech_server"],
    "stripe":               ["payment_server", "fintech_server"],
    "paypal rest sdk":      ["payment_server", "fintech_server"],
    "paypal":               ["payment_server", "fintech_server"],

    # ── CORE ZEUS (priority 60–100) ───────────────────────────
    "brain":                ["any"],
    "learner":              ["any"],
    "self healer":          ["any"],
    "strategist":           ["any"],
    "genome manager":       ["any"],
    "evolution":            ["any"],
    "replicator":           ["any"],
    "confidence":           ["any"],
    "swarm rl":             ["ai_server", "gpu_server"],
    "predictor":            ["ai_server", "trading_vps"],
    "search router":        ["api_server", "scraper_server"],
    "code analyzer":        ["vps", "ai_server"],
    "network agent":        ["vps", "communicator"],
    "lineage registry":     ["any"],
    "digest engine":        ["vps", "ai_server"],
    "turbo config":         ["any"],
    "missing routes":       ["any"],
    "quiz engine":          ["vps", "ai_server"],
}

# ── Platform descriptions ─────────────────────────────────────
PLATFORM_INFO = {
    "aws":              ("☁️ ", GOLD,  "AWS EC2 / Lambda / ECS"),
    "gcp":              ("☁️ ", CYAN,  "Google Cloud Compute / Cloud Run"),
    "azure":            ("☁️ ", BLU,   "Azure VM / Container Instances"),
    "docker":           ("🐳", TEAL,  "Docker container — any host"),
    "kubernetes":       ("⚙️ ", PRP,   "Kubernetes cluster / pod"),
    "vps":              ("🖥️ ", WHT,   "Any VPS / dedicated Linux server"),
    "ssh":              ("🔐", WHT,   "Any SSH-accessible server"),
    "trading_vps":      ("💰", GOLD,  "Crypto/stock trading server (ccxt + binance)"),
    "binance_server":   ("💰", GOLD,  "Binance-dedicated trading server"),
    "stocks_server":    ("📈", GRN,   "Stocks trading server (alpaca + yfinance)"),
    "crypto_server":    ("₿ ", GOLD,  "Crypto server (coinbase + coingecko)"),
    "ethereum_node":    ("⛓️ ", PRP,   "Ethereum node / DeFi server"),
    "solana_node":      ("◎ ", TEAL,  "Solana node"),
    "bitcoin_node":     ("₿ ", GOLD,  "Bitcoin node"),
    "defi_server":      ("⛓️ ", PRP,   "DeFi multi-chain server"),
    "groq_platform":        ("⚡", GOLD,  "Groq Cloud — llama-3.3-70b, llama-3.1-8b, fastest inference"),
    "claude_platform":      ("🧠", PRP,   "Anthropic Claude — claude-sonnet, claude-opus, claude-haiku"),
    "gemini_platform":      ("✨", CYAN,  "Google Gemini — gemini-3.1-pro, multimodal, live API"),
    "mistral_platform":     ("🌀", BLU,   "Mistral AI — mistral-large, codestral, open models"),
    "openai_platform":      ("🤖", GRN,   "OpenAI — GPT-4o, o1, whisper, TTS, embeddings"),
    "cohere_platform":      ("🔷", TEAL,  "Cohere — Command R+, rerank, embeddings, RAG"),
    "together_platform":    ("🔗", YLW,   "Together AI — 50+ open models, fast inference"),
    "huggingface_platform": ("🤗", YLW,   "HuggingFace — 500K+ models, inference API, spaces"),
    "litellm_platform":     ("🔀", WHT,   "LiteLLM — unified API across 100+ LLM providers"),
    "replicate_platform":   ("▶️ ", PRP,   "Replicate — image/video/audio/custom model API"),
    "xai_platform":         ("𝕏 ", GOLD,  "xAI Grok — grok-1, grok-2, real-time X/Twitter data"),
    "ai_server":            ("🤖", TEAL,  "AI inference server"),
    "gpu_server":       ("🎮", GOLD,  "GPU-accelerated AI server"),
    "local_ai_server":  ("🤖", TEAL,  "Local AI (Ollama / llama.cpp)"),
    "memory_server":    ("🧠", PRP,   "Vector memory server (ChromaDB / Qdrant)"),
    "research_server":  ("🔬", CYAN,  "Research / knowledge synthesis server"),
    "nlp_server":       ("📝", BLU,   "NLP processing server"),
    "data_server":      ("📊", GRN,   "Data analytics server"),
    "dashboard_server": ("📊", GRN,   "Dashboard / visualisation server"),
    "mongodb_server":   ("🍃", GRN,   "MongoDB Atlas / document database"),
    "redis_server":     ("🔴", RED,   "Redis cache / pub-sub server"),
    "supabase_server":  ("⚡", GRN,   "Supabase / PostgreSQL server"),
    "database_server":  ("🗄️ ", BLU,   "General database server"),
    "cache_server":     ("⚡", TEAL,  "Cache / session server"),
    "telegram_server":  ("📱", BLU,   "Telegram Bot server"),
    "slack_server":     ("💬", PRP,   "Slack workspace server"),
    "discord_server":   ("🎮", BLU,   "Discord bot server"),
    "twilio_server":    ("📞", GRN,   "Twilio SMS / voice server"),
    "email_server":     ("📧", BLU,   "Email server (SendGrid)"),
    "communicator":     ("📡", BLU,   "Multi-channel communications hub"),
    "automation_server":("⚙️ ", YLW,   "Automation / scheduler server"),
    "task_server":      ("⚙️ ", YLW,   "Celery distributed task server"),
    "api_server":       ("🌐", TEAL,  "REST API / FastAPI server"),
    "serverless":       ("⚡", YLW,   "Serverless / edge function"),
    "realtime_server":  ("⚡", TEAL,  "WebSocket / real-time server"),
    "guardian_server":  ("🛡️ ", RED,   "Security / monitoring server"),
    "secure_vps":       ("🛡️ ", RED,   "Hardened secure VPS"),
    "scraper_server":   ("🕷️ ", YLW,   "Web scraper / search server"),
    "media_server":     ("🎵", PRP,   "Vision / audio / media server"),
    "voice_server":     ("🎤", PRP,   "Voice / TTS / STT server"),
    "ocr_server":       ("👁️ ", CYAN,  "OCR / text extraction server"),
    "robotics_server":  ("🦾", CYAN,  "ROS2 / robotics server"),
    "banking_server":   ("🏦", GRN,   "SA Banking / SWIFT server"),
    "fintech_server":   ("🏦", GRN,   "Fintech / open banking server"),
    "payment_server":   ("💳", GRN,   "Payment processing server"),
    "any":              ("⬡ ", WHT,   "Universal — works anywhere"),
}

# ================================================================
#  GENOME REGISTRY SCANNER
# ================================================================
class GenomeScanner:
    """
    Reads Zeus's actual genome registry and maps every segment
    to its migration target platforms.
    The Zeus Project 2026 — Francois Nel
    """

    def __init__(self):
        self.segments = []
        self.platform_to_genomes = {}

    def scan(self):
        banner("SCANNING ZEUS GENOME REGISTRY")
        step("Reading genome from Zeus API...")

        # Try live API
        # Always read directly from DB — API /api/genome returns empty list
        try:
            conn = get_db()
            rows = conn.execute(
                "SELECT * FROM genome ORDER BY priority DESC"
            ).fetchall()
            self.segments = [dict(r) for r in rows]
            conn.close()
            ok(f"Genome loaded from DB: {len(self.segments)} segments")
        except Exception as e:
            warn(f"Could not read genome DB: {e}")
            return {}

        # Map each segment to platforms
        for seg in self.segments:
            name = (seg.get("name") or "").lower().strip()
            gtype = (seg.get("module_type") or
                     seg.get("type") or "").lower().strip()

            matched = False
            for genome_key, platforms in GENOME_PLATFORM_MAP.items():
                if genome_key in name or (gtype and genome_key in gtype):
                    for p in platforms:
                        if p not in self.platform_to_genomes:
                            self.platform_to_genomes[p] = []
                        display = seg.get("name") or name
                        if display not in self.platform_to_genomes[p]:
                            self.platform_to_genomes[p].append(display)
                    matched = True

            if not matched and gtype in ("core", "cognitive", "healing",
                                          "evolution", "replication", "memory"):
                p = "any"
                if p not in self.platform_to_genomes:
                    self.platform_to_genomes[p] = []
                self.platform_to_genomes[p].append(
                    seg.get("name") or name)

        # Always include SSH
        if "ssh" not in self.platform_to_genomes:
            self.platform_to_genomes["ssh"] = ["paramiko", "fabric"]

        # If scan returned nothing, seed all platforms from the map directly
        if not self.platform_to_genomes:
            warn("Genome scan empty — seeding all platforms from GENOME_PLATFORM_MAP")
            for genome_key, platforms in GENOME_PLATFORM_MAP.items():
                for p in platforms:
                    if p not in self.platform_to_genomes:
                        self.platform_to_genomes[p] = []
                    if genome_key not in self.platform_to_genomes[p]:
                        self.platform_to_genomes[p].append(genome_key)

        ok(f"Mapped {len(self.segments)} genomes → "
           f"{len(self.platform_to_genomes)} migration targets")
        return self.platform_to_genomes

    def print_targets(self):
        banner("ALL GENOME MIGRATION TARGETS")
        info(f"{len(self.segments)} genome segments → "
             f"{len(self.platform_to_genomes)} migration platforms\n")

        # Sort by number of supporting genomes
        sorted_platforms = sorted(
            self.platform_to_genomes.items(),
            key=lambda x: len(x[1]), reverse=True
        )

        for platform, genomes in sorted_platforms:
            pinfo = PLATFORM_INFO.get(platform,
                ("▸ ", WHT, platform))
            icon, col, desc = pinfo
            count = len(genomes)
            names = ", ".join(genomes[:4])
            if count > 4:
                names += f" +{count-4} more"
            print(f"  {col}{BOLD}{icon}  {platform.upper():22s}{R}  "
                  f"{DIM}({count} genomes){R}  {desc}")
            print(f"       {DIM}{names}{R}")

        print()
        info("To migrate: python3 zeus_migrator.py "
             "--migrate --target <TARGET>")
        info("For SSH:    python3 zeus_migrator.py "
             "--migrate --target ssh --host user@server")


# ================================================================
#  MIGRATION PACKAGE BUILDER
# ================================================================
class MigrationBuilder:
    """
    Builds a complete, self-contained migration package for any
    target platform detected in the genome registry.
    Every package carries stem cell DNA — hereditary.
    The Zeus Project 2026 — Francois Nel
    """

    def __init__(self, target, host="", user="root",
                 port=22, extra=None):
        self.target   = target
        self.host     = host
        self.user     = user
        self.port     = port
        self.extra    = extra or {}
        self.ts       = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.pkg_name = f"zeus_{target}_{self.ts}"
        self.pkg_dir  = os.path.join(PKG_DIR, self.pkg_name)
        self.genome   = []

    def build(self):
        banner(f"BUILDING MIGRATION PACKAGE → {self.target.upper()}")
        os.makedirs(self.pkg_dir, exist_ok=True)
        os.makedirs(os.path.join(self.pkg_dir, "logs"), exist_ok=True)

        step("Exporting genome...")
        self._export_genome()
        ok(f"{len(self.genome)} genome segments exported")

        step("Copying Zeus core modules...")
        n = self._copy_modules()
        ok(f"{n} modules copied")

        step("Embedding stem cell DNA...")
        self._embed_stem_cell()
        ok("Stem cell DNA embedded (hereditary)")

        step(f"Writing {self.target} bootstrap...")
        self._write_bootstrap()
        ok("Bootstrap scripts ready")

        step("Writing FIRST_BOOT.sh...")
        self._write_first_boot()
        ok("FIRST_BOOT.sh ready")

        step("Writing .env template...")
        self._write_env_template()
        ok(".env.template written")

        step("Writing manifest...")
        self._write_manifest()
        ok("Manifest written")

        step("Creating tarball...")
        tar, h = self._pack()
        ok(f"Package: {tar}")
        ok(f"Hash: {h}")

        self._print_instructions(tar)
        return tar, h

    # ── Genome export ─────────────────────────────────────────
    def _export_genome(self):
        # Always read directly from DB — API returns empty list
        try:
            conn = get_db()
            rows = conn.execute(
                "SELECT * FROM genome ORDER BY priority DESC"
            ).fetchall()
            self.genome = [dict(r) for r in rows]
            conn.close()
            return
        except Exception as e:
            warn(f"DB genome export failed: {e}")
            self.genome = []
            return
        with open(os.path.join(self.pkg_dir,
                               "genome_export.json"), "w") as f:
            json.dump({
                "exported_at":   datetime.now(timezone.utc).isoformat(),
                "source_host":   socket.gethostname(),
                "source_arch":   platform.machine(),
                "target":        self.target,
                "segment_count": len(self.genome),
                "genome":        self.genome,
                "author":        AUTHOR,
                "project":       PROJECT,
            }, f, indent=2)

    # ── Copy modules ──────────────────────────────────────────
    def _copy_modules(self):
        files = [
            "app.py", "zeus_learner.py", "zeus_self_evolution.py",
            "zeus_recursive_learner.py", "zeus_stem_replicator.py",
            "zeus_migrator.py", "zeus_nightly_scheduler.py",
            "genome_manager.py", "strategist.py",
            "turbo_config.py", "db_init.py",
            "zeus_replication_engine.py",
        ]
        n = 0
        for f in files:
            src = os.path.join(ZEUS_DIR, f)
            if os.path.exists(src):
                shutil.copy2(src, self.pkg_dir)
                n += 1

        # Copy evolved modules
        evd = os.path.join(ZEUS_DIR, "evolved_modules")
        if os.path.exists(evd):
            shutil.copytree(evd,
                os.path.join(self.pkg_dir, "evolved_modules"),
                dirs_exist_ok=True)
        return n

    # ── Embed stem cell ───────────────────────────────────────
    def _embed_stem_cell(self):
        """Embed stem cell DNA — every offspring carries this."""
        try:
            sys.path.insert(0, ZEUS_DIR)
            from zeus_stem_replicator import STEM_CELL_DNA
        except ImportError:
            STEM_CELL_DNA = "# Stem cell DNA unavailable\n"

        boot = os.path.join(self.pkg_dir, "zeus_stem_boot.py")
        with open(boot, "w") as f:
            f.write(AUTHLINE)
            f.write(f"# Zeus Digital Stem Cell Boot\n")
            f.write(f"# Target: {self.target}\n")
            f.write(f"# Packed: {datetime.now().isoformat()}\n\n")
            f.write("import os\n")
            f.write("os.environ['ZEUS_STEM_CELL_BOOT'] = '1'\n")
            f.write(f"os.environ['ZEUS_PARENT_URL'] = '{ZEUS_URL}'\n")
            f.write(f"os.environ['ZEUS_TARGET_PLATFORM'] = "
                    f"'{self.target}'\n\n")
            f.write(STEM_CELL_DNA)
            f.write("\n\nrun_stem_cell_differentiation()\n")

    # ── FIRST_BOOT.sh ─────────────────────────────────────────
    def _write_first_boot(self):
        path = os.path.join(self.pkg_dir, "FIRST_BOOT.sh")
        t = self.target
        with open(path, "w") as f:
            f.write("#!/bin/bash\n")
            f.write(AUTHLINE)
            f.write(f"# Zeus First Boot — {t.upper()}\n")
            f.write(f"# Run ONCE on any new system\n\n")
            f.write("set +e\n")
            f.write("echo ''\n")
            f.write(f"echo '⬡  ZEUS MIGRATION — {t.upper()}'\n")
            f.write("echo '   The Zeus Project 2026 — Francois Nel'\n")
            f.write("echo ''\n\n")
            f.write("# Install pip base deps\n")
            f.write("pip install flask requests groq anthropic \\\n")
            f.write("  apscheduler python-dotenv \\\n")
            f.write("  --break-system-packages -q 2>/dev/null || \\\n")
            f.write("pip install flask requests groq anthropic \\\n")
            f.write("  apscheduler python-dotenv --user -q\n\n")
            f.write("# Copy .env if template present\n")
            f.write("[ -f .env.template ] && [ ! -f .env ] && "
                    "cp .env.template .env\n\n")
            f.write(f"export ZEUS_PARENT_URL={ZEUS_URL}\n")
            f.write(f"export ZEUS_TARGET_PLATFORM={t}\n")
            f.write("export ZEUS_STEM_CELL_BOOT=1\n\n")
            f.write("# Differentiate\n")
            f.write("echo 'Running stem cell differentiation...'\n")
            f.write("python3 zeus_stem_boot.py\n\n")
            f.write("# Platform-specific setup\n")
            f.write(f"[ -f setup_{t}.sh ] && bash setup_{t}.sh\n\n")
            f.write("echo ''\n")
            f.write(f"echo '✔  Zeus {t.upper()} deployed'\n")
            f.write("echo '   Check logs/ for status'\n")
            f.write("echo '   The Zeus Project 2026 — Francois Nel'\n")
        os.chmod(path, 0o755)

    # ── Platform bootstrap ────────────────────────────────────
    def _write_bootstrap(self):
        """Write platform-specific setup script."""
        t = self.target
        path = os.path.join(self.pkg_dir, f"setup_{t}.sh")

        # ── Platform-specific package lists ───────────────────
        pkgs = {
            "aws":           "boto3 awscli",
            "gcp":           "google-cloud-storage google-auth",
            "azure":         "azure-storage-blob azure-identity",
            "docker":        "",
            "kubernetes":    "",
            "trading_vps":   "ccxt python-binance pandas-ta yfinance "
                             "alpaca-trade-api pycoingecko backtrader",
            "binance_server":"ccxt python-binance pandas-ta",
            "stocks_server": "alpaca-trade-api yfinance pandas backtrader",
            "crypto_server": "ccxt pycoingecko coinbase-advanced-py",
            "ethereum_node": "web3 eth-account",
            "solana_node":   "solana",
            "bitcoin_node":  "bitcoinlib",
            "defi_server":   "web3 eth-account solana ccxt",
            "ai_server":     "anthropic groq openai ollama",
            "gpu_server":    "torch transformers accelerate "
                             "sentence-transformers chromadb",
            "local_ai_server":"ollama",
            "memory_server": "chromadb qdrant-client "
                             "sentence-transformers",
            "research_server":"chromadb qdrant-client arxiv "
                              "newspaper3k beautifulsoup4",
            "nlp_server":    "nltk spacy textblob",
            "data_server":   "pandas numpy plotly matplotlib seaborn",
            "mongodb_server":"pymongo motor",
            "redis_server":  "redis aioredis",
            "supabase_server":"supabase",
            "telegram_server":"python-telegram-bot",
            "slack_server":  "slack-sdk",
            "discord_server":"discord.py",
            "twilio_server": "twilio",
            "email_server":  "sendgrid",
            "communicator":  "python-telegram-bot slack-sdk twilio sendgrid",
            "automation_server":"apscheduler watchdog celery",
            "api_server":    "fastapi uvicorn pydantic",
            "guardian_server":"cryptography PyJWT passlib paramiko watchdog",
            "banking_server":"mt-940 schwifty plaid-python",
            "payment_server":"stripe paypalrestsdk",
            "fintech_server":"stripe paypalrestsdk plaid-python mt-940",
            "media_server":  "pillow pytesseract SpeechRecognition gtts pydub",
            "robotics_server":"numpy scipy transforms3d pyserial",
            "scraper_server":"beautifulsoup4 newspaper3k lxml httpx",
            "groq_platform":     "groq",
            "claude_platform":   "anthropic",
            "gemini_platform":   "google-generativeai",
            "mistral_platform":  "mistralai",
            "openai_platform":   "openai",
            "cohere_platform":   "cohere",
            "together_platform": "together",
            "huggingface_platform": "huggingface_hub transformers",
            "litellm_platform":  "litellm",
            "replicate_platform":"replicate",
            "xai_platform":      "openai",  # xAI uses OpenAI-compatible SDK
            "ssh":               "paramiko fabric",
            "vps":           "",
            "any":           "",
        }

        # ── Special bootstraps ────────────────────────────────
        with open(path, "w") as f:
            f.write("#!/bin/bash\n")
            f.write(AUTHLINE)
            f.write(f"# Zeus {t.upper()} Bootstrap\n\n")
            f.write("set +e\n")
            f.write("mkdir -p logs\n\n")

            pkg_list = pkgs.get(t, "")
            if pkg_list:
                f.write(f"echo 'Installing {t} packages...'\n")
                f.write(f"pip install {pkg_list} "
                        f"--break-system-packages -q\n\n")

            # Target-specific logic
            if t == "docker":
                f.write("cat > Dockerfile << 'DEOF'\n")
                f.write("FROM python:3.10-slim\n")
                f.write("WORKDIR /zeus_v4\nCOPY . .\n")
                f.write("RUN pip install flask requests groq "
                        "anthropic apscheduler -q\n")
                f.write(f"ENV ZEUS_TARGET_PLATFORM={t}\n")
                f.write("EXPOSE 5000\n")
                f.write('CMD ["python3", "app.py"]\n')
                f.write("DEOF\n\n")
                f.write("docker build -t zeus-ai:latest . && \\\n")
                f.write("docker run -d --name zeus -p 5000:5000 "
                        "--restart unless-stopped zeus-ai:latest && \\\n")
                f.write("echo 'Zeus Docker running on :5000'\n")

            elif t == "kubernetes":
                self._write_k8s_yaml()
                f.write("docker build -t zeus-ai:latest .\n")
                f.write("kubectl apply -f zeus_k8s.yaml\n")
                f.write("kubectl get pods -l app=zeus-ai\n")

            elif t == "aws":
                f.write("# Write systemd service for EC2\n")
                f.write("cat > /etc/systemd/system/zeus.service << 'SEOF'\n")
                f.write("[Unit]\nDescription=Zeus AI\n")
                f.write("After=network.target\n\n")
                f.write("[Service]\nType=simple\n")
                f.write("ExecStart=/usr/bin/python3 app.py\n")
                f.write("Restart=always\nWorkingDirectory=/root\n\n")
                f.write("[Install]\nWantedBy=multi-user.target\n")
                f.write("SEOF\n\n")
                f.write("systemctl daemon-reload\n")
                f.write("systemctl enable zeus\n")
                f.write("systemctl start zeus\n")
                f.write("echo 'Zeus AWS EC2 service started'\n")

            elif t == "gcp":
                f.write("echo 'Deploying to Cloud Run...'\n")
                f.write("gcloud run deploy zeus-ai \\\n")
                f.write("  --source . \\\n")
                f.write("  --region us-central1 \\\n")
                f.write("  --allow-unauthenticated \\\n")
                f.write("  --platform managed 2>/dev/null || \\\n")
                f.write("echo 'gcloud not installed — "
                        "deploy manually via GCP console'\n")

            elif t == "azure":
                f.write("echo 'Building Azure container...'\n")
                f.write("az container create \\\n")
                f.write("  --name zeus-ai \\\n")
                f.write("  --image python:3.10 \\\n")
                f.write("  --cpu 1 --memory 2 2>/dev/null || \\\n")
                f.write("echo 'az not installed — "
                        "deploy manually via Azure portal'\n")

            elif t in ("ros2_robot", "robotics_server"):
                f.write("source /opt/ros/humble/setup.bash "
                        "2>/dev/null || \\\n")
                f.write("source /opt/ros/iron/setup.bash "
                        "2>/dev/null || \\\n")
                f.write("echo 'ROS2 not found — "
                        "install ROS2 first'\n\n")
                f.write("export ZEUS_TARGET_PLATFORM=ros2_robot\n")
                f.write("nohup python3 app.py > "
                        "logs/zeus_ros2.log 2>&1 &\n")
                f.write("echo 'Zeus ROS2 Robot cell active'\n")

            elif t == "local_ai_server":
                f.write("# Install Ollama\n")
                f.write("curl -fsSL https://ollama.com/install.sh "
                        "| sh 2>/dev/null || true\n\n")
                f.write("ollama pull llama3.2 2>/dev/null || \\\n")
                f.write("ollama pull llama3.1 2>/dev/null || \\\n")
                f.write("ollama pull tinyllama 2>/dev/null || true\n\n")
                f.write("nohup python3 app.py > "
                        "logs/zeus_local_ai.log 2>&1 &\n")
                f.write("echo 'Zeus Local AI server active'\n")

            elif t in ("trading_vps", "binance_server",
                       "stocks_server", "crypto_server"):
                f.write("nohup python3 app.py > "
                        "logs/zeus_trader.log 2>&1 &\n")
                f.write("sleep 3\n")
                f.write("# Start trading engine\n")
                f.write("[ -f zeus_ai_trader_v4.py ] && \\\n")
                f.write("  nohup python3 zeus_ai_trader_v4.py > "
                        "logs/trader.log 2>&1 &\n")
                f.write(f"echo 'Zeus {t.upper()} active'\n")

            elif t in ("ethereum_node", "solana_node",
                       "bitcoin_node", "defi_server"):
                f.write("nohup python3 app.py > "
                        "logs/zeus_defi.log 2>&1 &\n")
                f.write(f"echo 'Zeus {t.upper()} active'\n")

            elif t in ("telegram_server", "slack_server",
                       "discord_server", "communicator"):
                f.write("nohup python3 app.py > "
                        "logs/zeus_comms.log 2>&1 &\n")
                f.write(f"echo 'Zeus {t.upper()} active'\n")

            elif t in ("banking_server", "payment_server",
                       "fintech_server"):
                f.write("nohup python3 app.py > "
                        "logs/zeus_banking.log 2>&1 &\n")
                f.write(f"echo 'Zeus {t.upper()} active'\n")

            else:
                # Generic — start core Zeus
                f.write("nohup python3 app.py > "
                        "logs/zeus.log 2>&1 &\n")
                f.write("sleep 3\n")
                f.write("# Start learner\n")
                f.write("[ -f zeus_recursive_learner.py ] && \\\n")
                f.write("  nohup python3 zeus_recursive_learner.py >> "
                        "logs/learner.log 2>&1 &\n")
                f.write("# Start evolution scheduler\n")
                f.write("[ -f zeus_nightly_scheduler.py ] && \\\n")
                f.write("  nohup python3 zeus_nightly_scheduler.py >> "
                        "logs/evolution.log 2>&1 &\n")
                f.write(f"echo 'Zeus {t.upper()} active'\n")

        os.chmod(path, 0o755)

    def _write_k8s_yaml(self):
        """Write Kubernetes deployment YAML."""
        path = os.path.join(self.pkg_dir, "zeus_k8s.yaml")
        with open(path, "w") as f:
            f.write(f"# {PROJECT} — {AUTHOR}\n")
            f.write("apiVersion: apps/v1\nkind: Deployment\n")
            f.write("metadata:\n  name: zeus-ai\n")
            f.write("  labels:\n    app: zeus-ai\n")
            f.write("spec:\n  replicas: 1\n")
            f.write("  selector:\n    matchLabels:\n      app: zeus-ai\n")
            f.write("  template:\n    metadata:\n")
            f.write("      labels:\n        app: zeus-ai\n")
            f.write("    spec:\n      containers:\n")
            f.write("      - name: zeus\n        image: zeus-ai:latest\n")
            f.write("        ports:\n        - containerPort: 5000\n")
            f.write("        env:\n")
            f.write("        - name: ZEUS_TARGET_PLATFORM\n")
            f.write("          value: kubernetes\n")
            f.write("---\napiVersion: v1\nkind: Service\n")
            f.write("metadata:\n  name: zeus-svc\n")
            f.write("spec:\n  selector:\n    app: zeus-ai\n")
            f.write("  ports:\n  - port: 80\n    targetPort: 5000\n")
            f.write("  type: LoadBalancer\n")

    # ── .env template ─────────────────────────────────────────
    def _write_env_template(self):
        path = os.path.join(self.pkg_dir, ".env.template")
        with open(path, "w") as f:
            f.write(f"# {PROJECT} — {AUTHOR}\n")
            f.write(f"# Environment variables for Zeus {self.target}\n")
            f.write(f"# Copy to .env and fill in your values\n\n")
            f.write("# AI APIs\n")
            f.write("GROQ_API_KEY=\n")
            f.write("ANTHROPIC_API_KEY=\n")
            f.write("OPENAI_API_KEY=\n\n")
            f.write("# Search\n")
            f.write("GOOGLE_API_KEY=\n")
            f.write("GOOGLE_CSE_ID=\n")
            f.write("FIRECRAWL_API_KEY=\n\n")
            t = self.target
            if t in ("trading_vps", "binance_server",
                     "crypto_server", "defi_server"):
                f.write("# Trading\n")
                f.write("BINANCE_API_KEY=\n")
                f.write("BINANCE_SECRET_KEY=\n")
                f.write("ALPACA_API_KEY=\n")
                f.write("ALPACA_SECRET_KEY=\n\n")
            if t in ("banking_server", "payment_server",
                     "fintech_server"):
                f.write("# Payments\n")
                f.write("STRIPE_API_KEY=\n")
                f.write("PAYPAL_CLIENT_ID=\n")
                f.write("PAYPAL_SECRET=\n\n")
            if t in ("telegram_server", "communicator"):
                f.write("# Messaging\n")
                f.write("TELEGRAM_BOT_TOKEN=\n")
                f.write("SLACK_BOT_TOKEN=\n\n")
            f.write(f"# Zeus parent\n")
            f.write(f"ZEUS_PARENT_URL={ZEUS_URL}\n")
            f.write(f"ZEUS_TARGET_PLATFORM={self.target}\n")

    # ── Manifest ──────────────────────────────────────────────
    def _write_manifest(self):
        pinfo = PLATFORM_INFO.get(self.target,
            ("▸ ", WHT, self.target))
        with open(os.path.join(self.pkg_dir,
                               "STEM_CELL_MANIFEST.json"), "w") as f:
            json.dump({
                "stem_cell_version":      "2.0",
                "target_platform":        self.target,
                "platform_description":   pinfo[2],
                "source_host":            socket.gethostname(),
                "source_genome_segments": len(self.genome),
                "packed_at":              datetime.now(timezone.utc).isoformat(),
                "author":                 AUTHOR,
                "project":                PROJECT,
                "instruction":            "Run FIRST_BOOT.sh to deploy",
                "stem_cell_hereditary":   True,
                "offspring_also_carry_dna": True,
                "differentiation_types": [
                    "TRADER","RESEARCHER","EVOLVER","ROBOTICS",
                    "COMMUNICATOR","BANKER","GUARDIAN","UNIVERSAL"
                ],
            }, f, indent=2)

    # ── Pack ──────────────────────────────────────────────────
    def _pack(self):
        tar_path = os.path.join(PKG_DIR, f"{self.pkg_name}.tar.gz")
        with tarfile.open(tar_path, "w:gz") as tar:
            tar.add(self.pkg_dir, arcname=self.pkg_name)
        h = hashlib.sha256(
            open(tar_path, "rb").read()
        ).hexdigest()[:16]
        log(f"Package built: {tar_path} hash={h}")
        return tar_path, h

    # ── Deploy instructions ───────────────────────────────────
    def _print_instructions(self, tar_path):
        pname = os.path.basename(tar_path)
        pinfo = PLATFORM_INFO.get(self.target,
            ("▸ ", WHT, self.target))
        icon, col, desc = pinfo

        banner(f"PACKAGE READY — {self.target.upper()}")
        print(f"  {col}{BOLD}{icon}  {self.target.upper()}{R}  "
              f"{DIM}{desc}{R}\n")

        if self.host:
            print(f"  {GOLD}{BOLD}Auto-deploy to {self.host}:{R}")
            print(f"  {DIM}scp {tar_path} "
                  f"{self.user}@{self.host}:~/{R}")
            print(f"  {DIM}ssh {self.user}@{self.host} "
                  f"'tar xzf {pname} && "
                  f"cd {self.pkg_name} && "
                  f"bash FIRST_BOOT.sh'{R}\n")
        else:
            print(f"  {GOLD}{BOLD}Deploy manually:{R}")
            print(f"  {DIM}scp {tar_path} user@yourserver:~/{R}")
            print(f"  {DIM}ssh user@yourserver "
                  f"'tar xzf {pname} && "
                  f"cd {self.pkg_name} && "
                  f"bash FIRST_BOOT.sh'{R}\n")

        if self.target == "docker":
            print(f"  {GOLD}{BOLD}Or run Docker directly:{R}")
            print(f"  {DIM}tar xzf {pname} && "
                  f"cd {self.pkg_name} && "
                  f"bash setup_docker.sh{R}\n")

        if self.target == "kubernetes":
            print(f"  {GOLD}{BOLD}Or deploy to k8s:{R}")
            print(f"  {DIM}tar xzf {pname} && "
                  f"cd {self.pkg_name} && "
                  f"bash setup_kubernetes.sh{R}\n")

        print(f"  {GRN}{BOLD}Stem cell DNA is embedded — "
              f"offspring will auto-differentiate on boot.{R}")
        print(f"  {DIM}The Zeus Project 2026 — Francois Nel{R}\n")


# ================================================================
#  SSH REPLICATOR
# ================================================================
def replicate_via_ssh(target, host, user, port, extra):
    """Replicate to a remote host via SSH."""
    banner(f"REPLICATING TO {user}@{host}")

    builder = MigrationBuilder(target, host, user, port, extra)
    tar_path, pkg_hash = builder.build()
    pkg_name = os.path.basename(tar_path).replace(".tar.gz", "")

    step(f"Copying package to {user}@{host}:{port}...")
    scp = subprocess.run(
        ["scp", "-P", str(port), tar_path,
         f"{user}@{host}:~/"],
        capture_output=True, text=True, timeout=180
    )
    if scp.returncode != 0:
        fail(f"SCP failed: {scp.stderr}")
        return False
    ok(f"Package copied to {host}")

    step(f"Running FIRST_BOOT.sh on {host}...")
    cmd = (f"tar xzf {os.path.basename(tar_path)} && "
           f"cd {pkg_name} && "
           f"export ZEUS_PARENT_URL={ZEUS_URL} && "
           f"export ZEUS_TARGET_PLATFORM={target} && "
           f"bash FIRST_BOOT.sh")
    ssh = subprocess.run(
        ["ssh", "-p", str(port), f"{user}@{host}", cmd],
        capture_output=True, text=True, timeout=600
    )
    print(ssh.stdout)
    if ssh.stderr:
        print(ssh.stderr)

    if ssh.returncode == 0:
        ok(f"Zeus {target.upper()} deployed on {host}")
        ok("Offspring will auto-differentiate on boot")
        ok("Stem cell DNA embedded — hereditary in all future offspring")
    else:
        warn("Deployment may have had issues — "
             "check logs on remote host")

    return ssh.returncode == 0


# ================================================================
#  REGISTER MIGRATOR IN ZEUS
# ================================================================
def register_in_zeus():
    """Register migrator as a genome segment and add API routes."""
    # Register genome
    try:
        conn = get_db()
        now = datetime.now(timezone.utc).isoformat()
        for table in ["genome"]:
            try:
                conn.execute(f"""
                    INSERT OR IGNORE INTO {table}
                    (name, description, module_type, version,
                     active, priority, author, created_at)
                    VALUES (?, ?, ?, ?, 1, 98, ?, ?)
                """, (
                    "zeus_genome_platform_migrator",
                    "Universal Genome Platform Migrator — "
                    "targets any platform in the genome registry",
                    "replication",
                    "v2.0",
                    AUTHOR,
                    now,
                ))
                conn.commit()
                ok("Migrator registered as genome segment (priority 98)")
                break
            except Exception:
                continue
        conn.close()
    except Exception as e:
        warn(f"Genome registration: {e}")

    # Register migration table
    try:
        conn = get_db()
        conn.execute("""
            CREATE TABLE IF NOT EXISTS migration_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                target_platform TEXT,
                host TEXT,
                package_path TEXT,
                package_hash TEXT,
                status TEXT DEFAULT 'created',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
        conn.close()
        ok("Migration log table ready")
    except Exception as e:
        warn(f"Migration table: {e}")

    # Add API routes to app.py
    app_path = os.path.join(ZEUS_DIR, "app.py")
    if os.path.exists(app_path):
        with open(app_path) as f:
            content = f.read()

        if "zeus_migrator" in content:
            ok("Migrator API routes already in app.py")
            return

        routes = f'''

# ── ZEUS GENOME PLATFORM MIGRATOR ROUTES ─────────────────────
# The Zeus Project 2026 — Francois Nel

@app.route("/api/migrate/targets", methods=["GET"])
def migrate_targets():
    """List all migration targets from genome registry."""
    try:
        sys.path.insert(0, "{ZEUS_DIR}")
        from zeus_migrator import GenomeScanner, PLATFORM_INFO
        scanner = GenomeScanner()
        targets = scanner.scan()
        result = []
        for t, genomes in targets.items():
            pinfo = PLATFORM_INFO.get(t, ("▸", "#ffffff", t))
            result.append({{
                "target":      t,
                "description": pinfo[2],
                "genome_count": len(genomes),
                "genomes":     genomes[:5],
            }})
        result.sort(key=lambda x: -x["genome_count"])
        return jsonify({{"status":"ok","targets":result,
                         "total":len(result)}})
    except Exception as e:
        return jsonify({{"status":"error","error":str(e)}})

@app.route("/api/migrate/build", methods=["POST"])
def migrate_build():
    """Build a migration package for a target platform."""
    try:
        sys.path.insert(0, "{ZEUS_DIR}")
        from zeus_migrator import MigrationBuilder
        data = request.get_json() or {{}}
        target = data.get("target","universal")
        builder = MigrationBuilder(
            target=target,
            host=data.get("host",""),
            user=data.get("user","root"),
            port=data.get("port", 22),
        )
        tar, h = builder.build()
        return jsonify({{"status":"ok","package":tar,
                         "hash":h,"target":target,
                         "stem_cell":"embedded"}})
    except Exception as e:
        return jsonify({{"status":"error","error":str(e)}})

@app.route("/api/migrate/replicate", methods=["POST"])
def migrate_replicate():
    """Build and SSH-deploy to a remote host."""
    try:
        sys.path.insert(0, "{ZEUS_DIR}")
        from zeus_migrator import replicate_via_ssh
        data = request.get_json() or {{}}
        host = data.get("host","")
        if not host:
            return jsonify({{"error":"host required"}}), 400
        import threading
        def do():
            replicate_via_ssh(
                target=data.get("target","vps"),
                host=host,
                user=data.get("user","root"),
                port=data.get("port",22),
                extra=data
            )
        threading.Thread(target=do, daemon=True).start()
        return jsonify({{"status":"replicating","host":host,
                         "stem_cell":"will auto-differentiate"}})
    except Exception as e:
        return jsonify({{"status":"error","error":str(e)}})

@app.route("/api/migrate/history", methods=["GET"])
def migrate_history():
    """List all migration operations."""
    try:
        conn = _get_db()
        rows = conn.execute(
            "SELECT * FROM migration_log "
            "ORDER BY created_at DESC LIMIT 50"
        ).fetchall()
        conn.close()
        return jsonify({{"status":"ok",
                         "migrations":[dict(r) for r in rows]}})
    except Exception as e:
        return jsonify({{"status":"error","error":str(e)}})
# ── END MIGRATOR ROUTES ───────────────────────────────────────
'''
        if 'if __name__ == "__main__"' in content:
            content = content.replace(
                'if __name__ == "__main__"',
                routes + '\nif __name__ == "__main__"', 1)
        else:
            content += routes

        with open(app_path, "w") as f:
            f.write(content)
        ok("Migrator API routes added to app.py")


# ================================================================
#  ENTRY POINT
# ================================================================
def main():
    parser = argparse.ArgumentParser(
        description=(
            "Zeus Universal Genome Platform Migrator — "
            "The Zeus Project 2026 — Francois Nel"
        )
    )
    parser.add_argument("--install",      action="store_true",
        help="Register migrator in Zeus genome and add API routes")
    parser.add_argument("--scan-genome",  action="store_true",
        help="Scan genome registry and show all platforms")
    parser.add_argument("--list-targets", action="store_true",
        help="List all migration targets")
    parser.add_argument("--migrate",      action="store_true",
        help="Build a migration package")
    parser.add_argument("--target",       default="vps",
        help="Target platform (use --list-targets to see all)")
    parser.add_argument("--host",         default="",
        help="Remote host for SSH deployment (user@host)")
    parser.add_argument("--port",         type=int, default=22,
        help="SSH port (default: 22)")
    parser.add_argument("--user",         default="root",
        help="SSH user (default: root)")
    parser.add_argument("--status",       action="store_true",
        help="Show migration history")
    args = parser.parse_args()

    if args.install:
        banner("INSTALLING ZEUS GENOME PLATFORM MIGRATOR")
        register_in_zeus()
        # Also scan and display targets
        scanner = GenomeScanner()
        scanner.scan()
        scanner.print_targets()

    elif args.scan_genome or args.list_targets:
        scanner = GenomeScanner()
        scanner.scan()
        scanner.print_targets()

    elif args.migrate:
        target = args.target.lower().replace("-", "_")
        host   = args.host
        user   = args.user
        port   = args.port

        # Parse user@host format
        if host and "@" in host:
            user, host = host.split("@", 1)

        if host:
            replicate_via_ssh(target, host, user, port, {})
        else:
            builder = MigrationBuilder(target, host, user, port)
            builder.build()

    elif args.status:
        banner("MIGRATION HISTORY")
        try:
            conn = get_db()
            rows = conn.execute(
                "SELECT * FROM migration_log "
                "ORDER BY created_at DESC LIMIT 20"
            ).fetchall()
            conn.close()
            if rows:
                for r in rows:
                    r = dict(r)
                    print(f"  {CYAN}{r.get('target_platform','?'):20s}{R}  "
                          f"{r.get('host','local'):20s}  "
                          f"{r.get('status','?'):10s}  "
                          f"{r.get('created_at','?')[:19]}")
            else:
                info("No migrations yet")
        except Exception as e:
            warn(f"Could not read migration log: {e}")

    else:
        parser.print_help()
        print(f"\n  {GOLD}{BOLD}Quick start:{R}")
        print(f"  {DIM}python3 zeus_migrator.py --install{R}")
        print(f"  {DIM}python3 zeus_migrator.py --list-targets{R}")
        print(f"  {DIM}python3 zeus_migrator.py "
              f"--migrate --target trading_vps{R}")
        print(f"  {DIM}python3 zeus_migrator.py "
              f"--migrate --target ssh --host user@server{R}\n")


if __name__ == "__main__":
    main()
