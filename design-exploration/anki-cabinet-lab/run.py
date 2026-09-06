#!/usr/bin/env python3
"""Run the lab or production add-on in a new, disposable, real Anki profile."""

import argparse
import glob
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time


LAB = Path(__file__).resolve().parent
APP = Path("/Applications/Anki.app/Contents")
PACKAGES = APP / "Resources/app_packages"
MARKER = ".CABINET_LAB_ONLY.json"


def compatible_python():
    candidates = [sys.executable] + sorted(glob.glob(str(
        Path.home() / ".local/share/uv/python/cpython-3.13*-macos-*/bin/python3.13"
    )))
    probe_env = os.environ.copy()
    probe_env["PYTHONDONTWRITEBYTECODE"] = "1"
    for candidate in dict.fromkeys(candidates):
        probe = subprocess.run(
            [candidate, "-c", "import sys; sys.path.insert(0, sys.argv[1]); "
             "import anki, aqt; print(anki.version)", str(PACKAGES)],
            capture_output=True, text=True, timeout=20, env=probe_env,
        )
        if probe.returncode == 0:
            return candidate, probe.stdout.strip()
    raise SystemExit("No compatible Python can import this Anki installation. "
                     "A local Python 3.13 is required; nothing was installed or changed.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--verify", action="store_true", help="Run native UI checks, screenshot, then exit")
    mode.add_argument("--open", action="store_true", help="Leave the isolated demo window open")
    mode.add_argument("--palette", action="store_true", help="Verify only the production palette dialog in isolated Anki")
    parser.add_argument("--production", action="store_true",
                        help="Test the repository's production addon/ in a fresh scratch profile")
    args = parser.parse_args()
    if args.palette and not args.production:
        parser.error("--palette requires --production")
    if not PACKAGES.is_dir():
        raise SystemExit("This runner requires /Applications/Anki.app; no fallback mock is used.")
    source = LAB.parents[1] / "addon" if args.production else LAB / "addon"
    package = "mistline_ui" if args.production else "cabinet_lab"
    output = LAB / "production-evidence" if args.production else LAB
    if not (source / "__init__.py").is_file():
        raise SystemExit(f"The requested add-on is not present: {source}")
    output.mkdir(exist_ok=True)
    interpreter, version = compatible_python()
    # Never accept a user-supplied base path: each invocation creates a new lab.
    scratch = Path(tempfile.mkdtemp(prefix="anki-cabinet-lab-")).resolve()
    (scratch / MARKER).write_text(json.dumps({
        "purpose": "Anki Cabinet isolated demo only", "created": time.time(),
        "source": str(source), "contains_user_collection": False,
    }, indent=2), encoding="utf-8")
    addon = scratch / "addons21" / package
    shutil.copytree(source, addon, ignore=shutil.ignore_patterns("__pycache__"))
    if args.production:
        # Only the freshly generated add-on copy receives this user config.
        (addon / "meta.json").write_text(json.dumps({"config": {
            "enabled": True, "layout": "cabinet", "color_theme": "catppuccin",
            "catppuccin_flavor": "latte", "catppuccin_accent": "blue",
            "style_reviewer": True,
        }}, indent=2), encoding="utf-8")
    env = os.environ.copy()
    env["PYTHONPATH"] = str(PACKAGES)
    env["ANKI_CABINET_LAB_BASE"] = str(scratch)
    env["ANKI_CABINET_LAB_MODE"] = "open" if args.open else "palette" if args.palette else "verify"
    env["ANKI_CABINET_LAB_OUTPUT"] = str(output)
    env["ANKI_CABINET_LAB_ADDON"] = package
    env["PYTHONUNBUFFERED"] = "1"
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    # Independent process and independent Anki IPC key (set in the harness).
    log_path = scratch / "runtime.log"
    command = [interpreter, str(LAB / "lab_harness.py")]
    print(f"Real Anki {version}; isolated data: {scratch}", flush=True)
    with log_path.open("w", encoding="utf-8") as log:
        process = subprocess.Popen(command, env=env, stdout=log, stderr=subprocess.STDOUT,
                                   cwd=str(LAB), start_new_session=True)
    print(f"Test process: {process.pid}; log: {log_path}", flush=True)
    if args.open:
        print("Demo window starting. The existing Anki profile/process is not used.")
        return
    try:
        code = process.wait(timeout=180)
    except subprocess.TimeoutExpired:
        # This is only the Popen child created above, never a process-name kill.
        process.terminate()
        code = 124
    print(log_path.read_text(encoding="utf-8"), end="")
    report = output / "runtime-report.json"
    if report.is_file():
        result = json.loads(report.read_text(encoding="utf-8"))
        if result.get("scratch") == str(scratch):
            print(f"Report: {report}")
            if not result.get("passed"):
                code = code or 1
        else:
            print("This run produced no fresh report; the earlier report is not evidence for this run.")
            code = code or 1
    else:
        code = code or 1
    raise SystemExit(code)


if __name__ == "__main__":
    main()
