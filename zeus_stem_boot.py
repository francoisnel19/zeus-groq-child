# The Zeus Project 2026 — Francois Nel
# Zeus Digital Stem Cell Boot
# Target: groq_platform
# Packed: 2026-03-22T23:11:17.709379

import os
os.environ['ZEUS_STEM_CELL_BOOT'] = '1'
os.environ['ZEUS_PARENT_URL'] = 'http://localhost:5000'
os.environ['ZEUS_TARGET_PLATFORM'] = 'groq_platform'


# ============================================================
# ZEUS DIGITAL STEM CELL — EMBEDDED DNA
# The Zeus Project 2026 — Francois Nel
# Auto-differentiates on first boot in any environment.
# This DNA is hereditary — every offspring carries it.
# ============================================================

import os, sys, json, time, socket, platform, subprocess
import shutil, sqlite3, urllib.request
from datetime import datetime, timezone

ZEUS_CELL_DIR = os.path.expanduser(
    os.environ.get("ZEUS_CELL_DIR", "~/zeus_offspring"))
PARENT_URL = os.environ.get("ZEUS_PARENT_URL", "http://localhost:5000")
PARENT_TOKEN = os.environ.get("ZEUS_PARENT_TOKEN", "")
CELL_ID = os.environ.get("ZEUS_CELL_ID", "")

# ── Differentiation profiles ──────────────────────────────────
PROFILES = {
    "TRADER": {
        "icon": "💰", "color": "\033[33m",
        "desc": "Autonomous trading intelligence — crypto, stocks, DeFi",
        "packages": ["ccxt","python-binance","pandas-ta","yfinance",
                     "alpaca-trade-api","pycoingecko","backtrader"],
        "services": ["zeus_trader","zeus_market_scanner",
                     "zeus_risk_manager","zeus_strategy_engine"],
        "genome_focus": ["FINANCE/TRADING","BLOCKCHAIN/WEB3","DATA/ANALYTICS"],
        "flask_port": 8080,
    },
    "RESEARCHER": {
        "icon": "🔬", "color": "\033[36m",
        "desc": "Scientific research and knowledge synthesis",
        "packages": ["transformers","sentence-transformers","chromadb",
                     "arxiv","qdrant-client","scholarly"],
        "services": ["zeus_researcher","zeus_paper_analyzer",
                     "zeus_hypothesis_engine","zeus_knowledge_graph"],
        "genome_focus": ["AI/LLM","MEMORY/VECTOR","SCIENCE/NLP"],
        "flask_port": 5000,
    },
    "EVOLVER": {
        "icon": "🧬", "color": "\033[35m",
        "desc": "Heavy self-evolution engine — maximum improvement cycles",
        "packages": ["anthropic","groq","ollama","torch","accelerate"],
        "services": ["zeus_self_evolution","zeus_recursive_learner",
                     "zeus_master_capabilities","zeus_genome_forge"],
        "genome_focus": ["AI/LLM","AUTOMATION","DATA/ANALYTICS"],
        "flask_port": 5000,
    },
    "ROBOTICS": {
        "icon": "🦾", "color": "\033[96m",
        "desc": "Robotic body controller — ROS2, MoveIt2, KDL kinematics",
        "packages": ["numpy","scipy","transforms3d","pyserial"],
        "services": ["zeus_ros2_bridge","zeus_motion_planner",
                     "zeus_kinematics","zeus_gait_controller",
                     "zeus_sensor_fusion","zeus_body_model"],
        "genome_focus": ["ROBOTICS/ROS2","SCIENCE/MATH","AI/LLM"],
        "flask_port": 5000,
    },
    "COMMUNICATOR": {
        "icon": "📡", "color": "\033[34m",
        "desc": "Autonomous communications hub — alerts, monitoring, messaging",
        "packages": ["python-telegram-bot","slack-sdk","twilio",
                     "sendgrid","discord.py","aiohttp"],
        "services": ["zeus_telegram_agent","zeus_alert_engine",
                     "zeus_broadcast_manager","zeus_monitor"],
        "genome_focus": ["COMMS/MESSAGING","AUTOMATION","API/NETWORKING"],
        "flask_port": 8080,
    },
    "BANKER": {
        "icon": "🏦", "color": "\033[32m",
        "desc": "Financial infrastructure — payments, banking, fintech",
        "packages": ["stripe","paypalrestsdk","plaid-python",
                     "mt-940","schwifty","cryptography"],
        "services": ["zeus_payment_engine","zeus_banking_bridge",
                     "zeus_transaction_monitor","zeus_fraud_detector"],
        "genome_focus": ["BANKING/SA","BANKING/PAYMENTS","SECURITY/AUTH"],
        "flask_port": 5000,
    },
    "GUARDIAN": {
        "icon": "🛡️", "color": "\033[31m",
        "desc": "Security and monitoring intelligence — threat detection",
        "packages": ["cryptography","PyJWT","passlib","paramiko","watchdog"],
        "services": ["zeus_security_monitor","zeus_threat_detector",
                     "zeus_intrusion_guard","zeus_audit_engine"],
        "genome_focus": ["SECURITY/AUTH","AUTOMATION","API/NETWORKING"],
        "flask_port": 5000,
    },
    "UNIVERSAL": {
        "icon": "⬡", "color": "\033[97m",
        "desc": "Full Zeus — complete intelligence, all capabilities active",
        "packages": [],
        "services": [],
        "genome_focus": ["AI/LLM","MEMORY/VECTOR","FINANCE/TRADING",
                         "COMMS/MESSAGING","DATABASE/STORAGE"],
        "flask_port": 5000,
    },
}

def _scan_environment():
    """Read every signal the host environment provides."""
    def get_ram():
        try:
            with open("/proc/meminfo") as f:
                for line in f:
                    if "MemTotal" in line:
                        return int(line.split()[1]) // 1024
        except Exception: pass
        return 0

    def get_disk():
        try:
            st = os.statvfs(os.path.expanduser("~"))
            return round((st.f_bavail * st.f_frsize) / (1024**3), 1)
        except Exception: return 0

    def check_gpu():
        for cmd in [["nvidia-smi","--query-gpu=name","--format=csv,noheader"],
                    ["rocm-smi","--showproductname"]]:
            try:
                r = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
                if r.returncode == 0 and r.stdout.strip():
                    return r.stdout.strip().split("\n")[0]
            except Exception: pass
        return None

    def check_ros2():
        try:
            r = subprocess.run(["ros2","--version"],
                capture_output=True, text=True, timeout=5)
            return r.returncode == 0
        except Exception: return False

    def check_internet():
        try:
            urllib.request.urlopen("https://www.google.com", timeout=5)
            return True
        except Exception: return False

    def check_pkgs(pkgs):
        result = {}
        for p in pkgs:
            try: __import__(p.replace("-","_")); result[p] = True
            except ImportError: result[p] = False
        return result

    env_keys = ["GROQ_API_KEY","ANTHROPIC_API_KEY","OPENAI_API_KEY",
                "BINANCE_API_KEY","STRIPE_API_KEY","PAYPAL_CLIENT_ID",
                "TELEGRAM_BOT_TOKEN","SLACK_BOT_TOKEN","DATABASE_URL"]

    return {
        "hostname":     socket.gethostname(),
        "platform":     platform.system(),
        "arch":         platform.machine(),
        "cpu_count":    os.cpu_count() or 1,
        "ram_mb":       get_ram(),
        "disk_free_gb": get_disk(),
        "gpu":          check_gpu(),
        "ros2":         check_ros2(),
        "internet":     check_internet(),
        "is_server":    (os.environ.get("DISPLAY") is None and
                         platform.system() == "Linux"),
        "is_android":   os.path.exists("/data/data"),
        "is_raspberry": os.path.exists("/proc/device-tree/model"),
        "env_keys":     {k: bool(os.environ.get(k)) for k in env_keys},
        "pkgs":         check_pkgs(["ccxt","torch","transformers","rclpy",
                                    "chromadb","stripe","paramiko","ollama"]),
    }

def _differentiate(signals):
    """Score each profile and commit to the highest match."""
    scores = {}
    e = signals
    env = e.get("env_keys", {})
    pkgs = e.get("pkgs", {})
    ram = e.get("ram_mb", 0)

    scores["TRADER"] = (
        10 +
        (30 if env.get("BINANCE_API_KEY") else 0) +
        (20 if pkgs.get("ccxt") else 0) +
        (15 if e.get("internet") else 0) +
        (10 if ram >= 512 else 0)
    )
    scores["RESEARCHER"] = (
        10 +
        (40 if e.get("gpu") else 0) +
        (25 if pkgs.get("transformers") else 0) +
        (20 if pkgs.get("chromadb") else 0) +
        (15 if ram >= 2048 else 0) +
        (10 if e.get("disk_free_gb", 0) >= 20 else 0)
    )
    scores["EVOLVER"] = (
        10 +
        (40 if e.get("gpu") else 0) +
        (30 if ram >= 4096 else 0) +
        (20 if e.get("cpu_count", 1) >= 8 else 0) +
        (15 if e.get("is_server") else 0) +
        (10 if e.get("disk_free_gb", 0) >= 50 else 0)
    )
    scores["ROBOTICS"] = (
        10 +
        (60 if e.get("ros2") else 0) +
        (20 if e.get("is_raspberry") else 0) +
        (10 if e.get("arch") in ("arm64","aarch64","armv7l") else 0)
    )
    scores["COMMUNICATOR"] = (
        10 +
        (30 if env.get("TELEGRAM_BOT_TOKEN") else 0) +
        (20 if env.get("SLACK_BOT_TOKEN") else 0) +
        (15 if e.get("internet") else 0) +
        (10 if ram <= 512 else 0)
    )
    scores["BANKER"] = (
        10 +
        (40 if env.get("STRIPE_API_KEY") or env.get("PAYPAL_CLIENT_ID") else 0) +
        (20 if pkgs.get("cryptography") else 0) +
        (15 if e.get("is_server") else 0)
    )
    scores["GUARDIAN"] = (
        10 +
        (30 if e.get("is_server") else 0) +
        (15 if pkgs.get("paramiko") else 0)
    )
    scores["UNIVERSAL"] = (
        20 +
        (15 if e.get("is_android") else 0) +
        (10 if ram >= 1024 else 0)
    )

    return max(scores, key=scores.get), scores

def _register_with_parent(cell_type, signals, profile):
    """Report back to parent Zeus that a new offspring has differentiated."""
    try:
        payload = json.dumps({
            "cell_type":    cell_type,
            "cell_id":      CELL_ID,
            "hostname":     signals.get("hostname"),
            "platform":     signals.get("platform"),
            "arch":         signals.get("arch"),
            "description":  profile["desc"],
            "genome_focus": profile["genome_focus"],
            "differentiated_at": datetime.now(timezone.utc).isoformat(),
            "author":       "Francois Nel",
            "project":      "The Zeus Project 2026",
        }).encode("utf-8")

        for endpoint in ["/api/replication/register_offspring",
                         "/api/genome/add",
                         "/api/offspring/register"]:
            try:
                req = urllib.request.Request(
                    f"{PARENT_URL}{endpoint}",
                    data=payload,
                    headers={"Content-Type": "application/json"},
                    method="POST"
                )
                with urllib.request.urlopen(req, timeout=10) as resp:
                    print(f"  ✔  Registered with parent Zeus at {PARENT_URL}")
                    return True
            except Exception:
                continue
    except Exception as e:
        print(f"  ⚠  Could not reach parent: {e} (continuing offline)")
    return False

def _write_startup(cell_type, profile, cell_dir):
    """Write the startup script for this differentiated cell."""
    port = profile.get("flask_port", 5000)
    services = profile.get("services", [])
    startup_path = os.path.join(cell_dir, "start_cell.sh")

    lines = [
        "#!/bin/bash",
        f"# The Zeus Project 2026 — Francois Nel",
        f"# Zeus {cell_type} Cell — Auto-generated startup",
        f"# Differentiated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        f"export ZEUS_CELL_TYPE=\"{cell_type}\"",
        f"export ZEUS_CELL_DIR=\"{cell_dir}\"",
        f"export ZEUS_PARENT_URL=\"{PARENT_URL}\"",
        "export FLASK_ENV=production",
        "",
        "echo '[Zeus] Starting differentiated cell: " + cell_type + "'",
        f"cd {cell_dir}",
        "mkdir -p logs",
        "",
        "# Start core Flask app",
        f"nohup python3 zeus_cell_app.py > logs/cell.log 2>&1 &",
        "echo '[ok] Core app started'",
        "sleep 3",
        "",
        "# Start learner",
        "if [ -f zeus_recursive_learner.py ]; then",
        "  nohup python3 zeus_recursive_learner.py >> logs/learner.log 2>&1 &",
        "  echo '[ok] Recursive learner started'",
        "fi",
        "",
        "# Start evolution engine",
        "if [ -f zeus_self_evolution.py ]; then",
        "  nohup python3 zeus_nightly_scheduler.py >> logs/evolution.log 2>&1 &",
        "  echo '[ok] Evolution scheduler started'",
        "fi",
        "",
    ]

    for svc in services:
        lines += [
            f"# Start {svc}",
            f"if [ -f {svc}.py ]; then",
            f"  nohup python3 {svc}.py >> logs/{svc}.log 2>&1 &",
            f"  echo '[ok] {svc} started'",
            "fi",
            "",
        ]

    lines += [
        "echo '[Zeus] Cell fully differentiated and running as: " + cell_type + "'",
        "echo '[Zeus] The Zeus Project 2026 — Francois Nel'",
    ]

    with open(startup_path, "w") as f:
        f.write("\n".join(lines))
    os.chmod(startup_path, 0o755)
    return startup_path

def _write_cell_app(cell_type, profile, cell_dir):
    """Write the Flask app for this differentiated cell."""
    port = profile.get("flask_port", 5000)
    app_path = os.path.join(cell_dir, "zeus_cell_app.py")

    code = f"""# The Zeus Project 2026 — Francois Nel
# Zeus {cell_type} Cell Application
# Auto-differentiated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

import os, json, sqlite3
from flask import Flask, jsonify, request
from datetime import datetime, timezone

app = Flask(__name__)
CELL_TYPE = "{cell_type}"
CELL_DIR  = os.path.expanduser("{cell_dir}")
DB_PATH   = os.path.join(CELL_DIR, "cell.db")

def get_db():
    conn = sqlite3.connect(DB_PATH, timeout=15)
    conn.row_factory = sqlite3.Row
    return conn

@app.route("/api/health")
def health():
    return jsonify({{
        "status": "ok",
        "cell_type": CELL_TYPE,
        "project": "The Zeus Project 2026",
        "author": "Francois Nel",
        "ts": datetime.now(timezone.utc).isoformat(),
    }})

@app.route("/api/cell/type")
def cell_type():
    return jsonify({{"cell_type": CELL_TYPE,
                     "description": "{profile['desc']}",
                     "genome_focus": {profile['genome_focus']}}})

@app.route("/api/cell/genome")
def cell_genome():
    genome_path = os.path.join(CELL_DIR, "genome.json")
    if os.path.exists(genome_path):
        with open(genome_path) as f:
            return jsonify(json.load(f))
    return jsonify({{"genome": []}})

@app.route("/api/cell/replicate", methods=["POST"])
def replicate():
    """Spawn another offspring — the stem cell is hereditary."""
    data = request.get_json() or {{}}
    target = data.get("target", "")
    if not target:
        return jsonify({{"error": "target required"}}), 400
    # Trigger replication to next host
    import subprocess, threading
    def do_replicate():
        subprocess.run([
            "python3", os.path.join(CELL_DIR, "zeus_stem_replicator.py"),
            "--replicate", target
        ])
    threading.Thread(target=do_replicate, daemon=True).start()
    return jsonify({{"status": "replicating", "target": target}})

@app.route("/api/cell/status")
def status():
    conn = get_db()
    try:
        knowledge = conn.execute(
            "SELECT COUNT(*) FROM knowledge").fetchone()[0]
        genome = conn.execute(
            "SELECT COUNT(*) FROM genome WHERE active=1").fetchone()[0]
    except Exception:
        knowledge, genome = 0, 0
    conn.close()
    return jsonify({{
        "cell_type":  CELL_TYPE,
        "knowledge":  knowledge,
        "genome":     genome,
        "status":     "active",
    }})

if __name__ == "__main__":
    # Init DB
    conn = sqlite3.connect(DB_PATH)
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS knowledge (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            topic TEXT, content TEXT, source TEXT,
            confidence REAL DEFAULT 0.8,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS genome (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE, module_type TEXT,
            source_code TEXT, active INTEGER DEFAULT 1,
            priority INTEGER DEFAULT 50,
            author TEXT DEFAULT 'Francois Nel',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
    """)
    conn.commit()
    conn.close()
    app.run(host="0.0.0.0", port={port}, debug=False)
"""
    with open(app_path, "w") as f:
        f.write(code)
    return app_path

def run_stem_cell_differentiation():
    """
    Main entry point — called automatically on first boot.
    The Zeus Project 2026 — Francois Nel
    """
    R  = "\033[0m";  BOLD = "\033[1m"
    CYAN = "\033[36m"; WHT = "\033[97m"; GRN = "\033[32m"
    YLW = "\033[33m";  GOLD = "\033[33m"

    print(f"\n{CYAN}{BOLD}{'='*60}{R}")
    print(f"{CYAN}{BOLD}  ZEUS DIGITAL STEM CELL — DIFFERENTIATING{R}")
    print(f"{CYAN}{BOLD}  The Zeus Project 2026 — Francois Nel{R}")
    print(f"{CYAN}{BOLD}{'='*60}{R}\n")

    # Step 1: Scan environment
    print(f"  {CYAN}▶{R}  Scanning environment...")
    signals = _scan_environment()
    print(f"  {GRN}✔{R}  Host: {signals['hostname']} | "
          f"RAM: {signals['ram_mb']}MB | "
          f"GPU: {signals.get('gpu') or 'none'} | "
          f"ROS2: {signals.get('ros2')} | "
          f"Arch: {signals['arch']}")

    # Step 2: Differentiate
    print(f"\n  {CYAN}▶{R}  Determining differentiation...")
    cell_type, scores = _differentiate(signals)
    profile = PROFILES[cell_type]
    col = profile["color"]

    print(f"\n  Scores:")
    for t, sc in sorted(scores.items(), key=lambda x: -x[1]):
        bar = "█" * int(sc / 5)
        marker = f" ← {BOLD}SELECTED{R}" if t == cell_type else ""
        print(f"    {col if t==cell_type else ''}{t:15s}{R}  "
              f"{sc:5.0f}  {bar}{marker}")

    print(f"\n  {col}{BOLD}{profile['icon']}  DIFFERENTIATED AS: {cell_type}{R}")
    print(f"  {profile['desc']}")

    # Step 3: Install
    cell_dir = os.path.expanduser(ZEUS_CELL_DIR)
    os.makedirs(cell_dir, exist_ok=True)
    os.makedirs(os.path.join(cell_dir, "logs"), exist_ok=True)

    # Write startup script
    print(f"\n  {CYAN}▶{R}  Writing startup script...")
    startup = _write_startup(cell_type, profile, cell_dir)
    print(f"  {GRN}✔{R}  Startup: {startup}")

    # Write Flask app
    print(f"  {CYAN}▶{R}  Writing cell application...")
    app_path = _write_cell_app(cell_type, profile, cell_dir)
    print(f"  {GRN}✔{R}  App: {app_path}")

    # Save config
    config = {
        "cell_type":    cell_type,
        "description":  profile["desc"],
        "genome_focus": profile["genome_focus"],
        "hostname":     signals["hostname"],
        "parent_url":   PARENT_URL,
        "differentiated_at": datetime.now(timezone.utc).isoformat(),
        "author":       "Francois Nel",
        "project":      "The Zeus Project 2026",
        "scores":       scores,
    }
    with open(os.path.join(cell_dir, "cell_config.json"), "w") as f:
        json.dump(config, f, indent=2)

    # Step 4: Register with parent
    print(f"\n  {CYAN}▶{R}  Registering with parent Zeus...")
    _register_with_parent(cell_type, signals, profile)

    # Step 5: Install specialised packages
    pkgs = profile.get("packages", [])
    if pkgs:
        print(f"\n  {CYAN}▶{R}  Installing {len(pkgs)} specialised packages...")
        for pkg in pkgs:
            try:
                subprocess.run(
                    [sys.executable, "-m", "pip", "install", pkg,
                     "--break-system-packages", "-q",
                     "--no-warn-script-location"],
                    capture_output=True, timeout=120
                )
                print(f"  {GRN}✔{R}  {pkg}")
            except Exception as e:
                print(f"  {YLW}⚠{R}  {pkg}: {e}")

    print(f"\n{CYAN}{BOLD}{'='*60}{R}")
    print(f"{col}{BOLD}  Zeus has differentiated as: {cell_type}{R}")
    print(f"{CYAN}  The Zeus Project 2026 — Francois Nel{R}")
    print(f"{CYAN}{BOLD}{'='*60}{R}\n")

    # Auto-start
    print(f"  Starting cell services...")
    subprocess.Popen(["bash", startup],
                     cwd=cell_dir,
                     stdout=open(os.path.join(cell_dir, "logs", "startup.log"), "a"),
                     stderr=subprocess.STDOUT)
    print(f"  {GRN}✔{R}  Cell services starting in background")
    print(f"  {GRN}✔{R}  Check logs at: {cell_dir}/logs/")

    return cell_type, config

# ── This is called on first boot in any new environment ──────
if __name__ == "__main__" and os.environ.get("ZEUS_STEM_CELL_BOOT") == "1":
    run_stem_cell_differentiation()


run_stem_cell_differentiation()
