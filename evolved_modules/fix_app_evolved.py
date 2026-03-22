# The Zeus Project 2026 — Francois Nel
# ZEUS EVOLVED MODULE: fix_app.py
# Evolution timestamp: 2026-03-22T08:09:23.470206
# Gaps addressed: 1
# Code hash: 84e7f47af5251d84
# ─────────────────────────────────────────────────────

# The Zeus Project 2026 — Francois Nel

import logging
import os
import re
import shutil
import ast

# GAP_FILLED: Implement logging for the fix_app module
def setup_logging():
    """
    Sets up logging for the fix_app module.
    
    This function configures the logging module to output logs to a file and to the console.
    The log level is set to DEBUG, and the format includes the timestamp, log level, and message.
    """
    logging.basicConfig(filename='fix_app.log', level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    console.setFormatter(formatter)
    logging.getLogger('').addHandler(console)

# GAP_FILLED: Implement function to remove corrupted cat block
def remove_corrupted_block(src):
    """
    Removes the corrupted cat block from the given source code.
    
    This function searches for the corruption marker in the source code and removes everything after it.
    If the corruption marker is not found, the original source code is returned.
    
    Args:
        src (str): The source code to remove the corrupted block from.
    
    Returns:
        str: The source code with the corrupted block removed.
    """
    cut_markers = [
        "# ── Direct module init (zeus wire fix)",
        "# Direct module init",
        "import logging\x00",
        "_wlog = logging",
    ]
    for marker in cut_markers:
        if marker in src:
            src = src[:src.index(marker)]
            logging.info(f"[ok] Removed corrupted block at: {marker[:40]}")
            break
    return src

# GAP_FILLED: Implement function to strip garbled unicode/doubled text
def strip_garbled_text(src):
    """
    Strips lines with garbled unicode/doubled text from the given source code.
    
    This function iterates over each line in the source code and checks for null bytes or obvious corruption.
    If a line is corrupted, it is skipped; otherwise, it is added to the clean lines list.
    
    Args:
        src (str): The source code to strip garbled text from.
    
    Returns:
        str: The source code with garbled text stripped.
    """
    clean_lines = []
    for line in src.splitlines():
        if "\x00" in line or line.count("──") > 2:
            continue
        clean_lines.append(line)
    return "\n".join(clean_lines)

# GAP_FILLED: Implement function to insert clean init block
def insert_init_block(src):
    """
    Inserts the clean init block into the given source code.
    
    This function checks if the clean init block is already present in the source code.
    If it is, the function only removes corruption; otherwise, it inserts the clean init block.
    
    Args:
        src (str): The source code to insert the clean init block into.
    
    Returns:
        str: The source code with the clean init block inserted.
    """
    INIT = '''
# ── Module init ──────────────────────────────────────────────────
import logging as _lg
_wl = _lg.getLogger("Zeus")
try:
    from zeus_chat import init_chat
    init_chat(app)
    _wl.info("[ok] Chat wired")
except Exception as _e:
    _wl.warning(f"Chat: {_e}")
try:
    from zeus_upload import init_upload
    init_upload(app)
    _wl.info("[ok] Upload wired")
except Exception as _e:
    _wl.warning(f"Upload: {_e}")
try:
    from zeus_executor import init_executor
    init_executor(app)
    _wl.info("[ok] Executor wired")
except Exception as _e:
    _wl.warning(f"Executor: {_e}")
try:
    from zeus_search import init_search
    init_search(app)
    _wl.info("[ok] Search wired")
except Exception as _e:
    _wl.warning(f"Search: {_e}")
try:
    from zeus_learner import init_learner
    init_learner(app)
    _wl.info("[ok] Learner wired")
except Exception as _e:
    _wl.warning(f"Learner: {_e}")
'''
    if 'if __name__ == "__main__"' in src:
        before, main_block = src.split('if __name__ == "__main__"', 1)
    else:
        before = src
        main_block = '\n    app.run(host="0.0.0.0", port=5000, debug=False, threaded=True)\n'
    if "from zeus_chat import init_chat" in before:
        logging.info("[->] Clean init already present — only removing corruption")
        new_src = before.rstrip() + '\n\nif __name__ == "__main__"' + main_block
    else:
        new_src = before.rstrip() + INIT + 'if __name__ == "__main__"' + main_block
    return new_src

# GAP_FILLED: Implement function to backup and write the fixed source code
def backup_and_write(src, filename):
    """
    Backs up the original source code and writes the fixed source code to the given filename.
    
    This function creates a backup of the original source code by appending ".fix_backup" to the filename.
    It then writes the fixed source code to the given filename.
    
    Args:
        src (str): The fixed source code to write.
        filename (str): The filename to write the fixed source code to.
    """
    shutil.copy2(filename, filename + ".fix_backup")
    logging.info("[ok] Backup: " + filename + ".fix_backup")
    with open(filename, "w", encoding="utf-8") as f:
        f.write(src)
    logging.info("[ok] " + filename + " written clean")
    logging.info("[ok] Size: " + str(len(src)) + " bytes")

# GAP_FILLED: Implement function to perform a quick syntax check
def syntax_check(src):
    """
    Performs a quick syntax check on the given source code.
    
    This function uses the ast module to parse the source code and check for syntax errors.
    If a syntax error is found, the function logs an error message and restores the backup.
    
    Args:
        src (str): The source code to perform a syntax check on.
    """
    try:
        ast.parse(src)
        logging.info("[ok] Syntax valid")
    except SyntaxError as e:
        logging.error("[!!] Syntax error: " + str(e))
        logging.info("Restoring backup...")
        shutil.copy2(filename + ".fix_backup", filename)

# GAP_FILLED: Implement the main function to fix the app.py file
def fix_app():
    """
    Fixes the app.py file by removing the corrupted cat block, stripping garbled unicode/doubled text, and inserting the clean init block.
    
    This function reads the app.py file, removes the corrupted cat block, strips garbled unicode/doubled text, and inserts the clean init block.
    It then backs up the original source code, writes the fixed source code, and performs a quick syntax check.
    """
    filename = os.path.expanduser("~/zeus_v4/app.py")
    src = open(filename, encoding="utf-8", errors="ignore").read()
    src = remove_corrupted_block(src)
    src = strip_garbled_text(src)
    src = insert_init_block(src)
    backup_and_write(src, filename)
    syntax_check(src)

setup_logging()
fix_app()