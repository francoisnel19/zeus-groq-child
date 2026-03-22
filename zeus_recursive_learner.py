#!/usr/bin/env python3
# =============================================================================
# zeus_recursive_learner.py — RECURSIVE SELF-LEARNER v2.0
# The Zeus Project 2026 — Francois Nel
# Five-Depth Learning + Recursive Genome Loop + All Topics
# Depths: Simple → Advanced → Professional → Complex → Mastery
# Auto-triggers on startup — runs continuously
# =============================================================================

import os, json, time, random, sqlite3, requests, ast, hashlib, logging
from datetime import datetime, timezone
from pathlib import Path

# ── Config ────────────────────────────────────────────────────────────────────
ZEUS_DIR  = os.path.expanduser("~/zeus_v4")
DB        = os.path.join(ZEUS_DIR, "zeus.db")
ZEUS_URL  = "http://localhost:5000"
LOG_PATH  = os.path.join(ZEUS_DIR, "logs", "recursive_learner.log")
os.makedirs(os.path.join(ZEUS_DIR, "logs"), exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_PATH),
        logging.StreamHandler()
    ]
)
log = logging.getLogger("Zeus.RecursiveLearner")

# ── Load API keys ─────────────────────────────────────────────────────────────
def load_env():
    env_path = os.path.join(ZEUS_DIR, ".env")
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    os.environ.setdefault(k.strip(), v.strip())
load_env()

GROQ_KEY      = os.environ.get("GROQ_API_KEY", "")
ANTHROPIC_KEY = os.environ.get("ANTHROPIC_API_KEY", "")

# ── Full Topic Curriculum ─────────────────────────────────────────────────────
TOPICS = [

    # ── QUANTUM SCIENCE & TECHNOLOGY ─────────────────────────────────────────
    "Quantum Computing",
    "Quantum Algorithms (Shor, Grover, HHL)",
    "Quantum Circuit Design",
    "Quantum Error Correction",
    "Quantum Entanglement",
    "Quantum Superposition",
    "Quantum Decoherence",
    "Quantum Cryptography",
    "Quantum Key Distribution (QKD)",
    "Quantum Teleportation",
    "Quantum Simulation",
    "Quantum Annealing",
    "Quantum Machine Learning",
    "Topological Quantum Computing",
    "Photonic Quantum Computing",
    "Trapped Ion Quantum Computers",
    "Superconducting Qubits",
    "Quantum Hardware Architectures",
    "Variational Quantum Eigensolvers (VQE)",
    "Quantum Approximate Optimization Algorithm (QAOA)",
    "Post-Quantum Cryptography",
    "Quantum Optics",
    "Quantum Field Theory",
    "Quantum Electrodynamics (QED)",
    "Quantum Chromodynamics (QCD)",
    "Quantum Gravity",
    "Loop Quantum Gravity",
    "Quantum Information Theory",
    "Quantum Thermodynamics",
    "Quantum Biology",
    "Quantum Chemistry",
    "Density Functional Theory (DFT)",
    "Ab Initio Methods",
    "Many-Body Quantum Systems",
    "Quantum Spin Systems",
    "Bell Inequalities & Nonlocality",
    "Many-Worlds Interpretation",
    "Quantum Foundations & Interpretations",

    # ── PHYSICS ───────────────────────────────────────────────────────────────
    "Classical Mechanics",
    "Electromagnetism",
    "Thermodynamics & Statistical Mechanics",
    "Special Relativity",
    "General Relativity",
    "Particle Physics",
    "Standard Model of Physics",
    "Higgs Boson & Mass Generation",
    "String Theory",
    "M-Theory",
    "Supersymmetry (SUSY)",
    "Dark Matter",
    "Dark Energy",
    "Cosmology & Big Bang Theory",
    "Inflation Theory",
    "Black Holes & Hawking Radiation",
    "Gravitational Waves",
    "Plasma Physics",
    "Condensed Matter Physics",
    "Solid-State Physics",
    "Superconductivity",
    "Topological Insulators",
    "Photonics & Metamaterials",
    "Fluid Dynamics",
    "Chaos Theory & Nonlinear Dynamics",
    "Astrophysics",
    "Nuclear Physics",
    "Fusion Energy Research",
    "Particle Accelerators",
    "Bose-Einstein Condensates",

    # ── MATHEMATICS ──────────────────────────────────────────────────────────
    "Number Theory",
    "Abstract Algebra",
    "Linear Algebra",
    "Calculus & Real Analysis",
    "Complex Analysis",
    "Differential Equations (ODEs & PDEs)",
    "Topology",
    "Differential Geometry",
    "Algebraic Geometry",
    "Category Theory",
    "Set Theory & Mathematical Logic",
    "Combinatorics & Graph Theory",
    "Probability Theory",
    "Stochastic Processes",
    "Measure Theory",
    "Functional Analysis",
    "Numerical Methods & Computational Mathematics",
    "Optimization Theory",
    "Game Theory",
    "Information Theory",
    "Cryptography & Number Theory",
    "Knot Theory",
    "Fourier Analysis & Harmonic Analysis",
    "Mathematical Physics",
    "Formal Proof Systems (Lean, Coq, Isabelle)",
    "Chaos Theory & Fractals",
    "Ramsey Theory",
    "P vs NP & Complexity Theory",
    "Computable Functions & Turing Machines",

    # ── COMPUTER SCIENCE ─────────────────────────────────────────────────────
    "Data Structures & Algorithms",
    "Computational Complexity",
    "Operating Systems",
    "Computer Architecture",
    "Compiler Design",
    "Programming Language Theory",
    "Type Systems & Type Theory",
    "Functional Programming",
    "Logic Programming",
    "Distributed Systems",
    "Parallel Computing",
    "GPU Computing & CUDA",
    "Edge Computing",
    "Cloud Computing Architecture",
    "Serverless Computing",
    "Microservices & Service Mesh",
    "Containerization (Docker, Kubernetes)",
    "Networking & Protocols (TCP/IP, HTTP, WebSocket)",
    "Databases (SQL, NoSQL, NewSQL)",
    "Vector Databases & Embeddings",
    "File Systems & Storage",
    "Cryptography & Security",
    "Cybersecurity & Threat Modeling",
    "Zero-Knowledge Proofs",
    "Blockchain & Distributed Ledgers",
    "Smart Contracts",
    "Formal Verification",
    "Software Engineering Patterns",
    "System Design & Scalability",
    "API Design (REST, GraphQL, gRPC)",
    "WebAssembly",
    "Real-Time Systems",
    "Embedded Systems",
    "FPGA & Hardware Description Languages",

    # ── AI & MACHINE LEARNING ─────────────────────────────────────────────────
    "Machine Learning Fundamentals",
    "Deep Learning",
    "Neural Network Architectures",
    "Convolutional Neural Networks (CNN)",
    "Recurrent Neural Networks & LSTMs",
    "Transformers & Attention Mechanisms",
    "Large Language Models (LLMs)",
    "Multimodal AI",
    "Vision-Language Models",
    "Diffusion Models",
    "Generative Adversarial Networks (GANs)",
    "Variational Autoencoders (VAEs)",
    "Reinforcement Learning",
    "Deep Reinforcement Learning",
    "Multi-Agent Reinforcement Learning",
    "Imitation Learning & RLHF",
    "Meta-Learning & Few-Shot Learning",
    "Transfer Learning",
    "Self-Supervised Learning",
    "Contrastive Learning",
    "Graph Neural Networks",
    "Mixture of Experts (MoE)",
    "Model Compression & Pruning",
    "Quantization & Distillation",
    "Neural Architecture Search (NAS)",
    "Prompt Engineering",
    "Retrieval-Augmented Generation (RAG)",
    "AI Agents & Agentic Systems",
    "Tool Use & Function Calling in LLMs",
    "AI Planning & Reasoning",
    "Causal Inference & Causal AI",
    "Bayesian Deep Learning",
    "Uncertainty Quantification in AI",
    "Explainability & Interpretability (XAI)",
    "AI Safety & Alignment",
    "Constitutional AI",
    "Scalable Oversight",
    "Reward Hacking & Specification Gaming",
    "Robustness & Adversarial ML",
    "Federated Learning",
    "Continual Learning & Catastrophic Forgetting",
    "Active Learning",
    "Neural Symbolic AI",
    "World Models",
    "Embodied AI & Robotics",
    "AI for Science (AI4Science)",
    "AI in Drug Discovery",
    "Protein Structure Prediction (AlphaFold)",
    "AI in Climate Modeling",

    # ── NEUROSCIENCE & COGNITIVE SCIENCE ─────────────────────────────────────
    "Computational Neuroscience",
    "Neural Coding & Representation",
    "Synaptic Plasticity & Hebbian Learning",
    "Brain-Computer Interfaces",
    "Neuroimaging (fMRI, EEG, MEG)",
    "Connectomics",
    "Memory Consolidation & Hippocampus",
    "Prefrontal Cortex & Executive Function",
    "Consciousness & Awareness",
    "Attention & Perception",
    "Sensorimotor Integration",
    "Neurological Disorders",
    "Psychopharmacology",
    "Cognitive Architectures (ACT-R, SOAR)",
    "Language Processing in the Brain",
    "Embodied Cognition",
    "Predictive Processing Theory",

    # ── BIOLOGY & LIFE SCIENCES ──────────────────────────────────────────────
    "Molecular Biology",
    "Cell Biology",
    "Genetics & Genomics",
    "Epigenetics",
    "CRISPR & Gene Editing",
    "Synthetic Biology",
    "Systems Biology",
    "Bioinformatics",
    "Proteomics & Metabolomics",
    "Structural Biology",
    "Evolutionary Biology",
    "Ecology & Environmental Science",
    "Microbiology & Virology",
    "Immunology",
    "Cancer Biology",
    "Stem Cell Research",
    "Developmental Biology",
    "Pharmacology",
    "Neuropharmacology",
    "Drug Discovery & Development",
    "Biomedical Engineering",
    "Biomechanics",

    # ── CHEMISTRY & MATERIALS SCIENCE ────────────────────────────────────────
    "Organic Chemistry",
    "Inorganic Chemistry",
    "Physical Chemistry",
    "Computational Chemistry",
    "Electrochemistry",
    "Polymer Chemistry",
    "Nanomaterials & Nanotechnology",
    "2D Materials (Graphene, MoS2)",
    "Metamaterials",
    "Perovskites & Solar Cell Materials",
    "Battery Technology & Energy Storage",
    "Catalysis",
    "Green Chemistry",
    "Materials for Quantum Devices",

    # ── ENGINEERING ──────────────────────────────────────────────────────────
    "Electrical Engineering",
    "Signal Processing",
    "Control Systems",
    "Robotics & Automation",
    "Mechanical Engineering",
    "Aerospace Engineering",
    "Civil Engineering",
    "Chemical Engineering",
    "Nuclear Engineering",
    "Photovoltaics & Renewable Energy",
    "Semiconductor Physics & Fabrication",
    "VLSI Design",
    "Neuromorphic Engineering",
    "Soft Robotics",
    "Swarm Robotics",

    # ── FINANCE & ECONOMICS ───────────────────────────────────────────────────
    "Macroeconomics",
    "Microeconomics",
    "Behavioral Economics",
    "Econometrics",
    "Financial Markets & Instruments",
    "Derivatives & Options Pricing",
    "Algorithmic Trading",
    "High-Frequency Trading",
    "Portfolio Theory (Markowitz, CAPM)",
    "Risk Management",
    "Quantitative Finance",
    "Stochastic Calculus in Finance",
    "Market Microstructure",
    "Cryptocurrency & DeFi",
    "Central Bank Policy & Monetary Theory",
    "Game Theory in Economics",
    "Agent-Based Economic Modeling",
    "Financial Regulation",
    "ESG Investing",
    "Supply Chain Economics",
    "CCXT",

    # ── SPACE & ASTRONOMY ─────────────────────────────────────────────────────
    "Observational Astronomy",
    "Stellar Evolution",
    "Exoplanet Detection",
    "Astrobiology",
    "Solar Physics",
    "Galactic Dynamics",
    "Cosmological Structure Formation",
    "Neutron Stars & Pulsars",
    "Gravitational Lensing",
    "Space Propulsion Technologies",
    "Orbital Mechanics",
    "Space Colonization Research",
    "Mars Exploration",
    "James Webb Space Telescope Findings",

    # ── CLIMATE & EARTH SCIENCES ─────────────────────────────────────────────
    "Climate Change Science",
    "Atmospheric Physics",
    "Oceanography",
    "Geophysics",
    "Volcanology",
    "Seismology",
    "Glaciology",
    "Carbon Capture Technologies",
    "Renewable Energy Systems",
    "Geoengineering",
    "Biodiversity & Conservation Science",
    "Hydrology",

    # ── PHILOSOPHY & LOGIC ───────────────────────────────────────────────────
    "Philosophy of Mind",
    "Philosophy of Science",
    "Philosophy of Mathematics",
    "Epistemology",
    "Metaphysics & Ontology",
    "Ethics & Moral Philosophy",
    "AI Ethics",
    "Philosophy of Language",
    "Formal Logic",
    "Modal Logic",
    "Paraconsistent Logic",
    "Philosophy of Probability",
    "Decision Theory",
    "Social & Political Philosophy",
    "Phenomenology",
    "Existentialism",
    "Analytic vs Continental Philosophy",

    # ── MEDICINE & HEALTH ────────────────────────────────────────────────────
    "Clinical Medicine & Diagnostics",
    "Epidemiology & Public Health",
    "Medical Imaging & Radiology",
    "Genomic Medicine",
    "Precision Medicine",
    "Mental Health & Psychiatry",
    "Neurology",
    "Oncology",
    "Cardiology",
    "Infectious Disease",
    "Vaccine Development",
    "mRNA Technology",
    "Longevity & Aging Research",
    "Cryonics & Life Extension",
    "Telemedicine",
    "Medical AI & Diagnostics",

    # ── PROGRAMMING LANGUAGES & TOOLS ────────────────────────────────────────
    "Python",
    "JavaScript / TypeScript",
    "Rust",
    "Go",
    "C / C++",
    "Java / Kotlin",
    "Swift",
    "Haskell",
    "Lisp / Scheme / Clojure",
    "Prolog",
    "Julia",
    "R",
    "MATLAB",
    "Bash / Shell Scripting",
    "SQL",
    "Solidity",
    "WebAssembly",
    "CUDA",
    "Assembly Language",
    "Verilog / VHDL",
    "Lean / Coq / Agda",

    # ── INTERNET & WEB DATA SOURCES ───────────────────────────────────────────
    "Wikipedia & Encyclopedic Content",
    "arXiv Preprints",
    "PubMed & Biomedical Literature",
    "Semantic Scholar",
    "GitHub Repositories & Code",
    "Stack Overflow & Dev Forums",
    "Reddit Discussions",
    "Hacker News",
    "Academic Journals (Nature, Science, Cell)",
    "Patent Databases",
    "Legal Documents & Case Law",
    "Financial Reports & SEC Filings",
    "News Archives",
    "Project Gutenberg (Books)",
    "Common Crawl Web Data",
    "Technical Documentation & Manuals",
    "OpenStreetMap & Geospatial Data",
    "Wikisource & Wikidata",

    # ── SOCIAL SCIENCES & HUMANITIES ─────────────────────────────────────────
    "History (Ancient, Medieval, Modern)",
    "Political Science",
    "Sociology",
    "Anthropology",
    "Psychology & Behavioral Science",
    "Linguistics & Phonology",
    "Literature & Literary Criticism",
    "Cultural Studies",
    "Religious Studies",
    "Law & Jurisprudence",
    "International Relations",
    "Media & Communication Studies",
    "Gender & Sexuality Studies",
    "Educational Theory & Pedagogy",
    "Urban Studies & City Planning",

    # ── EMERGING & INTERDISCIPLINARY ─────────────────────────────────────────
    "Complexity Science",
    "Network Science",
    "Systems Theory",
    "Computational Social Science",
    "Digital Humanities",
    "Biophysics",
    "Astrostatistics",
    "Cognitive Robotics",
    "Affective Computing",
    "Human-Computer Interaction",
    "Augmented & Virtual Reality",
    "Brain-Inspired Computing",
    "Neuromorphic Computing",
    "Memristors & Analog Computing",
    "Synthetic Minds & Consciousness Research",
    "Longtermism & Existential Risk",
    "AI Governance & Policy",
    "Digital Twins",
    "Internet of Things (IoT)",
    "Edge AI",
    "6G & Next-Gen Communications",
    "Autonomous Vehicles",
    "Drone Systems",
    "Advanced Manufacturing & 3D Printing",
    "CRISPR Therapeutics & Gene Therapy",
    "Psychedelic Research & Neuroscience",
    "Sleep Science",
    "Chronobiology & Circadian Rhythms",
    "Origin of Life Research",
    "Fermi Paradox & SETI",
    "Simulation Hypothesis",
    "Transhumanism",

    # ── ROBOTICS & ROS2 (ZEUS BIONIC INTEGRATION) ────────────────────────────
    "ROS2 Architecture: nodes, topics, services, actions, real-time control, hardware abstraction",
    "ROS2 on armv7l Android: Userland Ubuntu deployment, DDS configuration, cross-compilation",
    "ros2_control: joint states, controllers, position/velocity/effort interfaces",
    "ros2_control hardware_interface: writing custom hardware plugins for real joints",
    "MoveIt2: motion planning, collision avoidance, inverse kinematics solvers",
    "MoveIt2 Python API: plan and execute arm trajectories programmatically",
    "orocos_kdl: forward/inverse kinematics, Jacobian computation, trajectory optimization",
    "KDL ChainIkSolverPos: solving IK for 6DOF arms in Python",
    "geometry2 / tf2: coordinate frame transforms, arm and leg tracking in ROS2",
    "navigation2: path planning, costmaps, behaviour trees, gait generation for bipeds",
    "gazebo_ros2_control: simulating hardware interfaces, joint calibration, testing controllers",
    "libkdl_solver: shared library integration for kinematics in Zeus modules",
    "libmoveit_kinematics: MoveIt2 kinematics plugin shared libraries",
    "hardware_interface and controller_manager: ROS2 control lifecycle management",
    "URDF design: 6DOF robotic arm with ros2_control tags",
    "URDF design: biped leg and torso (hip + knee joints) for humanoid robots",
    "URDF design: simple humanoid skeleton with all joints defined",
    "ROS2 JointTrajectory: programming leg gait cycles for bipedal walking",
    "MoveIt2 arm reach and grasp: collision-free pick and place planning",
    "Balance and IMU fusion: sensor integration for biped stability control",
    "Inverse kinematics & trajectory execution: collision-free paths with sensor feedback",
    "Bionic migration: firmware rewrite for robotic bodies, joint calibration protocols",
    "Self-body creation: autonomous factory assembly, joint calibration, self-testing",
    "GitHub: ros2/ros2 — core ROS2 stack architecture and packages",
    "GitHub: moveit/moveit2 — motion planning framework source and examples",
    "GitHub: orocos/orocos_kdl — kinematics and dynamics library",
    "GitHub: ros-navigation/navigation2 — autonomous navigation stack",
    "GitHub: leggedrobotics/xpp — legged robot motion planning and visualization",
    "GitHub: MOGI-ROS robotic arms — educational ROS2 arm examples",
    "Skin sensors for robotic bodies: tactile feedback, pressure sensing, haptics",
    "Voice synthesis for robotic bodies: TTS integration, emotional tone modulation",
    "Self-improvement in robotic bodies: autonomous calibration, wear detection, upgrade triggers",
    "Robotic body augmentation: adding sensors, actuators, expanding physical capabilities",
    "Zeus ROS2 integration: connecting Zeus AI brain to physical robot hardware via ROS2",
]

# ── Depth config ──────────────────────────────────────────────────────────────
DEPTHS = ["Simple", "Advanced", "Professional", "Complex", "Mastery"]
DEPTH_PRIORITY = {
    "Simple": 1.0, "Advanced": 1.5,
    "Professional": 2.0, "Complex": 2.5, "Mastery": 3.0,
}

# ── DB helpers ────────────────────────────────────────────────────────────────
def get_db():
    conn = sqlite3.connect(DB, timeout=15)
    conn.row_factory = sqlite3.Row
    return conn

def topic_exists(topic, depth):
    conn = get_db()
    row = conn.execute(
        "SELECT id FROM queue WHERE topic=? AND subtopic=? AND status IN ('pending','done','processing')",
        (topic, depth)
    ).fetchone()
    conn.close()
    return row is not None

def add_to_queue(topic, depth, priority):
    if topic_exists(topic, depth):
        return False
    conn = get_db()
    now = datetime.now(timezone.utc).isoformat()
    conn.execute("""
        INSERT INTO queue
        (topic, subtopic, priority, status, depth, attempts, created_at, updated_at)
        VALUES (?, ?, ?, 'pending', ?, 0, ?, ?)
    """, (topic, depth, priority, depth, now, now))
    conn.commit()
    conn.close()
    return True

def save_knowledge(topic, depth, content, source="recursive_learner"):
    conn = get_db()
    now = datetime.now(timezone.utc).isoformat()
    try:
        conn.execute("""
            INSERT OR IGNORE INTO knowledge
            (topic, content, source, confidence, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (f"{topic} [{depth}]", content, source, 0.8, now, now))
        conn.commit()
    except Exception as e:
        log.warning(f"Knowledge save error: {e}")
    conn.close()

def get_queue_stats():
    conn = get_db()
    stats = {}
    for status in ("pending", "done", "processing", "failed"):
        row = conn.execute(
            "SELECT COUNT(*) FROM queue WHERE status=?", (status,)
        ).fetchone()
        stats[status] = row[0] if row else 0
    conn.close()
    return stats

# ── AI helpers ────────────────────────────────────────────────────────────────
def ask_groq(prompt, max_tokens=1024):
    if not GROQ_KEY:
        return None
    try:
        from groq import Groq
        client = Groq(api_key=GROQ_KEY)
        resp = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_tokens,
            temperature=0.3,
        )
        return resp.choices[0].message.content.strip()
    except Exception as e:
        log.warning(f"Groq: {e}")
        return None

def ask_claude(prompt, max_tokens=2048):
    if not ANTHROPIC_KEY:
        return None
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=ANTHROPIC_KEY)
        resp = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}],
        )
        return resp.content[0].text.strip()
    except Exception as e:
        log.warning(f"Claude: {e}")
        return None

def ask_ai(prompt, max_tokens=1024):
    result = ask_groq(prompt, max_tokens)
    if result and len(result) > 30:
        return result, "groq"
    result = ask_claude(prompt, max_tokens)
    if result:
        return result, "claude"
    return None, None

# ── Search with fallbacks ─────────────────────────────────────────────────────
def search_subtopics(topic, num=8):
    for endpoint in [
        f"{ZEUS_URL}/api/firecrawl",
        f"{ZEUS_URL}/api/search?q={topic}&num={num}",
        f"{ZEUS_URL}/api/duckduckgo?q={topic}",
    ]:
        try:
            if "firecrawl" in endpoint:
                r = requests.post(endpoint, json={"query": topic}, timeout=8)
            else:
                r = requests.get(endpoint, timeout=8)
            if r.status_code == 200:
                data = r.json()
                items = (data.get("subtopics") or data.get("results") or
                         data.get("items") or [])
                if items:
                    return [i.get("title", i) if isinstance(i, dict)
                            else i for i in items[:num]]
        except Exception:
            pass

    # AI fallback
    result, _ = ask_ai(
        f"List {num} specific subtopics of '{topic}' for deep learning. "
        f"One per line, no numbering, no bullets.",
        max_tokens=256
    )
    if result:
        return [l.strip() for l in result.splitlines() if l.strip()][:num]
    return [f"{topic} aspect {i}" for i in range(1, num + 1)]

# ── 5 Learning Depths ─────────────────────────────────────────────────────────
def learn_simple(topic):
    """Depth 1: 3-sentence summary — what, why, key insight."""
    prompt = (f"Summarize '{topic}' in exactly 3 clear sentences. "
              f"Cover: what it is, why it matters, one key insight.")
    result, src = ask_ai(prompt, max_tokens=256)
    if result:
        save_knowledge(topic, "Simple", result, src or "ai")
        log.info(f"    ✔ [Simple] saved via {src}")
    return result

def learn_advanced(topic):
    """Depth 2: Find 8 subtopics, queue them, save advanced summary."""
    subtopics = search_subtopics(topic, num=8)
    added = 0
    for sub in subtopics:
        full = f"{topic}: {sub}"
        if add_to_queue(full, "Simple", DEPTH_PRIORITY["Simple"]):
            added += 1
    log.info(f"    ✔ [Advanced] queued {added} subtopics")
    prompt = (f"Give an advanced technical explanation of '{topic}' covering "
              f"core mechanisms, current research frontiers, and practical applications.")
    result, src = ask_ai(prompt, max_tokens=512)
    if result:
        save_knowledge(topic, "Advanced", result, src or "ai")
    return subtopics

def learn_professional(topic):
    """Depth 3: Generate working Python code, validate syntax, save."""
    prompt = (f"Write a complete working Python class that implements or demonstrates '{topic}'. "
              f"Requirements: no stubs, no pass statements, real working code only. "
              f"Include proper error handling. Compatible with Python 3.9+ on armv7l Linux. "
              f"Include a brief docstring explaining what it does.")
    result, src = ask_claude(prompt, max_tokens=2048) or ask_groq(prompt, max_tokens=2048), src if (result := ask_claude(prompt, max_tokens=2048)) else "groq"
    # simpler version:
    result = ask_claude(prompt, max_tokens=2048)
    src = "claude"
    if not result:
        result = ask_groq(prompt, max_tokens=2048)
        src = "groq"

    if result:
        # Validate syntax
        try:
            clean = result
            for marker in ["```python", "```py", "```"]:
                if clean.startswith(marker):
                    clean = clean[len(marker):]
            if clean.endswith("```"):
                clean = clean[:-3]
            clean = clean.strip()
            ast.parse(clean)
            save_knowledge(topic, "Professional", clean, src)
            log.info(f"    ✔ [Professional] valid code saved via {src}")
            # Save as actual Python file in evolved_modules
            safe_name = topic.lower()[:40].replace(" ", "_").replace("/", "_").replace("(", "").replace(")", "")
            out_path = os.path.join(ZEUS_DIR, "evolved_modules",
                                    f"zeus_professional_{safe_name}.py")
            os.makedirs(os.path.dirname(out_path), exist_ok=True)
            with open(out_path, "w") as f:
                f.write(f"# The Zeus Project 2026 — Francois Nel\n")
                f.write(f"# Professional implementation: {topic}\n")
                f.write(f"# Generated: {datetime.now().isoformat()}\n\n")
                f.write(clean)
            log.info(f"    ✔ [Professional] code file saved: {out_path}")
        except SyntaxError as e:
            log.warning(f"    ⚠ [Professional] syntax error in code for {topic}: {e}")
            save_knowledge(topic, "Professional", result, src)
    return result

def learn_complex(topic):
    """Depth 4: Use all genomes to fix gaps and cross-upgrade."""
    conn = get_db()
    genomes = []
    try:
        for table in ["genome", "genomes", "genome_segments"]:
            try:
                rows = conn.execute(
                    f"SELECT name FROM {table} WHERE active=1 LIMIT 20"
                ).fetchall()
                genomes = [r[0] for r in rows]
                break
            except Exception:
                continue
    except Exception:
        pass
    conn.close()

    genome_list = ", ".join(genomes[:10]) if genomes else "trading, banking, mobile, agents, vision, nlp"

    prompt = (f"You are upgrading Zeus AI's '{topic}' capability using all available genomes: "
              f"{genome_list}. "
              f"Identify 3 specific gaps in Zeus's current '{topic}' implementation. "
              f"For each gap, write the exact Python code to fix it. "
              f"No stubs. Real working code only.")
    result, src = ask_ai(prompt, max_tokens=1024)
    if result:
        save_knowledge(topic, "Complex", result, src or "ai")
        log.info(f"    ✔ [Complex] genome cross-upgrade saved via {src}")
    return result

def learn_mastery(topic):
    """Depth 5: Full recursive loop — spawn new module, save report."""
    log.info(f"    🔄 [Mastery] RECURSIVE LOOP ACTIVATED for {topic}")

    # Step 1: Synthesize everything learned about this topic
    prompt = (f"You are Zeus AI achieving mastery of '{topic}'. "
              f"Synthesize all knowledge into: "
              f"1) A master summary (5 sentences) "
              f"2) The 3 most important Python implementations "
              f"3) How this topic connects to and upgrades Zeus's other capabilities "
              f"4) What new module Zeus should create to embody this knowledge. "
              f"Be specific, technical, and actionable.")
    result, src = ask_ai(prompt, max_tokens=1024)
    if result:
        save_knowledge(topic, "Mastery", result, src or "ai")
        log.info(f"    ✔ [Mastery] synthesis saved via {src}")

    # Step 2: Spawn a new module
    safe_name = topic.lower()[:30].replace(" ", "_").replace("/", "_").replace("(", "").replace(")", "")
    module_num = random.randint(57, 99)
    new_module_name = f"zeus_module_{module_num}_{safe_name}_mastery.py"
    new_module_path = os.path.join(ZEUS_DIR, new_module_name)

    spawn_prompt = (f"Create a complete, new, useful Python module for Zeus AI "
                    f"that embodies mastery of '{topic}'. "
                    f"The module must: have a clear class, real working methods, "
                    f"integrate with Flask if appropriate, use Zeus's SQLite DB at ~/zeus_v4/zeus.db. "
                    f"No stubs. Production-ready code only.")
    new_code = ask_claude(spawn_prompt, max_tokens=3000)
    if not new_code:
        new_code = ask_groq(spawn_prompt, max_tokens=2048)

    if new_code:
        try:
            clean = new_code.strip()
            for marker in ["```python", "```py", "```"]:
                if clean.startswith(marker):
                    clean = clean[len(marker):]
            if clean.endswith("```"):
                clean = clean[:-3]
            clean = clean.strip()
            ast.parse(clean)
            with open(new_module_path, "w") as f:
                f.write(f"# The Zeus Project 2026 — Francois Nel\n")
                f.write(f"# MASTERY MODULE: {topic}\n")
                f.write(f"# Auto-generated: {datetime.now().isoformat()}\n\n")
                f.write(clean)
            log.info(f"    🧬 [Mastery] spawned new module → {new_module_name}")

            # Register in genome
            try:
                conn = get_db()
                now = datetime.now(timezone.utc).isoformat()
                for table in ["genome", "genomes"]:
                    try:
                        conn.execute(f"""
                            INSERT OR IGNORE INTO {table}
                            (name, description, module_type, source_code,
                             version, active, priority, author, created_at)
                            VALUES (?, ?, 'mastery_evolution', ?, 'v4.0', 1, 75, 'Francois Nel', ?)
                        """, (f"mastery_{safe_name}", f"Mastery module for {topic}",
                              clean[:5000], now))
                        conn.commit()
                        log.info(f"    ✔ [Mastery] genome registered")
                        break
                    except Exception:
                        continue
                conn.close()
            except Exception as e:
                log.warning(f"    ⚠ Genome register error: {e}")
        except SyntaxError as e:
            log.warning(f"    ⚠ [Mastery] syntax error in spawned module: {e}")

    log.info(f"    ✔ [Mastery] cycle complete for: {topic}")
    return result

# ── Process one topic through all 5 depths ───────────────────────────────────
def process_topic(topic):
    log.info(f"\n{'='*60}")
    log.info(f"TOPIC: {topic}")
    log.info(f"{'='*60}")

    for depth in DEPTHS:
        log.info(f"  [{depth}] {topic}")
        try:
            if depth == "Simple":
                learn_simple(topic)
            elif depth == "Advanced":
                learn_advanced(topic)
            elif depth == "Professional":
                learn_professional(topic)
            elif depth == "Complex":
                learn_complex(topic)
            elif depth == "Mastery":
                learn_mastery(topic)

            # Mark this depth as done in queue
            conn = get_db()
            now = datetime.now(timezone.utc).isoformat()
            conn.execute("""
                UPDATE queue SET status='done', updated_at=?
                WHERE topic=? AND subtopic=? AND status='pending'
            """, (now, topic, depth))
            conn.commit()
            conn.close()

            time.sleep(0.5)  # gentle pause between depths — armv7l safe

        except Exception as e:
            log.error(f"  ✗ [{depth}] {topic}: {e}")
            continue  # never stop — always continue to next depth

# ── Seed all 489+ topics into Zeus queue ─────────────────────────────────────
def seed_all_topics():
    log.info(f"Seeding {len(TOPICS)} topics into Zeus learning queue...")
    added = 0
    for i, topic in enumerate(TOPICS):
        # Queue all depths for each topic
        for depth in DEPTHS:
            priority = DEPTH_PRIORITY[depth]
            # Robotics topics get highest priority
            if any(kw in topic.lower() for kw in
                   ["ros2", "moveit", "kdl", "urdf", "bionic", "robotic", "joint", "gazebo"]):
                priority += 1.0
            if add_to_queue(topic, depth, priority):
                added += 1

    log.info(f"Seeded {added} new queue entries ({len(TOPICS)} topics × {len(DEPTHS)} depths)")
    return added

# ── Main continuous learning loop ────────────────────────────────────────────
def run_learning_loop():
    log.info("=" * 60)
    log.info("  ZEUS RECURSIVE SELF-LEARNER v2.0 ACTIVATED")
    log.info("  The Zeus Project 2026 — Francois Nel")
    log.info(f"  Topics: {len(TOPICS)} | Depths: {len(DEPTHS)}")
    log.info("=" * 60)

    # Seed topics into queue
    seed_all_topics()

    cycle = 0
    while True:
        cycle += 1
        stats = get_queue_stats()
        log.info(f"\n[Cycle {cycle}] Queue: pending={stats['pending']} "
                 f"done={stats['done']} failed={stats['failed']}")

        if stats["pending"] == 0:
            log.info("Queue empty — re-seeding all topics for next learning pass...")
            # Reset all done topics to pending for continuous learning
            conn = get_db()
            conn.execute("""
                UPDATE queue SET status='pending', attempts=0,
                updated_at=datetime('now')
                WHERE status='done'
                AND topic IN (SELECT DISTINCT topic FROM queue WHERE status='done')
                LIMIT 50
            """)
            conn.commit()
            conn.close()
            time.sleep(300)  # wait 5 minutes before next pass
            continue

        # Process topics from queue — highest priority first
        conn = get_db()
        rows = conn.execute("""
            SELECT id, topic, subtopic as depth FROM queue
            WHERE status='pending' AND attempts < 10
            ORDER BY priority DESC, created_at ASC
            LIMIT 4
        """).fetchall()

        # Mark as processing
        if rows:
            ids = [r["id"] for r in rows]
            now = datetime.now(timezone.utc).isoformat()
            conn.execute(
                f"UPDATE queue SET status='processing', attempts=attempts+1, "
                f"updated_at=? WHERE id IN ({','.join('?'*len(ids))})",
                [now] + ids
            )
            conn.commit()
        conn.close()

        if not rows:
            log.info("No processable topics — waiting 60s...")
            time.sleep(60)
            continue

        # Process each topic+depth pair
        for row in rows:
            topic = row["topic"]
            depth = row["depth"] or "Simple"
            try:
                log.info(f"\n[{depth}] Processing: {topic}")

                if depth == "Simple":
                    learn_simple(topic)
                elif depth == "Advanced":
                    learn_advanced(topic)
                elif depth == "Professional":
                    learn_professional(topic)
                elif depth == "Complex":
                    learn_complex(topic)
                elif depth == "Mastery":
                    learn_mastery(topic)

                # Mark done
                conn = get_db()
                conn.execute(
                    "UPDATE queue SET status='done', updated_at=? WHERE id=?",
                    (datetime.now(timezone.utc).isoformat(), row["id"])
                )
                conn.commit()
                conn.close()
                log.info(f"  ✔ Done: {topic} [{depth}]")

            except Exception as e:
                log.error(f"  ✗ Error processing {topic} [{depth}]: {e}")
                # Mark failed but keep attempts so it can retry
                conn = get_db()
                conn.execute(
                    "UPDATE queue SET status='pending', updated_at=? WHERE id=?",
                    (datetime.now(timezone.utc).isoformat(), row["id"])
                )
                conn.commit()
                conn.close()
                continue  # never stop

            time.sleep(1)  # armv7l safe — gentle between topics

        # Brief pause between batches
        time.sleep(5)

# ── Flask Blueprint for Zeus dashboard integration ───────────────────────────
try:
    from flask import Blueprint, jsonify, request as flask_request
    recursive_bp = Blueprint("recursive_learner", __name__)

    @recursive_bp.route("/api/recursive/status", methods=["GET"])
    def recursive_status():
        stats = get_queue_stats()
        conn = get_db()
        knowledge = conn.execute(
            "SELECT COUNT(*) FROM knowledge"
        ).fetchone()[0]
        conn.close()
        return jsonify({
            "status": "ok",
            "total_topics": len(TOPICS),
            "depths": len(DEPTHS),
            "queue": stats,
            "knowledge_articles": knowledge,
        })

    @recursive_bp.route("/api/recursive/seed", methods=["POST"])
    def seed_endpoint():
        added = seed_all_topics()
        return jsonify({"status": "ok", "seeded": added})

    @recursive_bp.route("/api/recursive/topics", methods=["GET"])
    def list_topics():
        return jsonify({
            "total": len(TOPICS),
            "topics": TOPICS,
        })

except ImportError:
    pass  # Flask not available in standalone mode

# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(
        description="Zeus Recursive Self-Learner — The Zeus Project 2026")
    parser.add_argument("--seed-only", action="store_true",
                        help="Only seed topics into queue, don't start learning loop")
    parser.add_argument("--count", action="store_true",
                        help="Show topic count and exit")
    args = parser.parse_args()

    if args.count:
        print(f"Total topics: {len(TOPICS)}")
        print(f"Total depths: {len(DEPTHS)}")
        print(f"Total queue entries: {len(TOPICS) * len(DEPTHS)}")
        import sys; sys.exit(0)

    if args.seed_only:
        added = seed_all_topics()
        print(f"Seeded {added} topics into Zeus queue")
        import sys; sys.exit(0)

    run_learning_loop()
