#!/usr/bin/env python3
"""Local-only unattended verification driver for Cadence (Level 10).

Runs:
1. Health check against API & Web
2. `make verify` (ruff + tsc + pytest)
3. `rules_report.json` parity check against `make -s report`
4. Two-browser Playwright E2E suite (`e2e/`)
Writes a summary report to `docs/test/report/latest-test-report.md`.
"""

from __future__ import annotations

import os
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REPORT_PATH = ROOT / "docs" / "test" / "report" / "latest-test-report.md"


def wait_for_url(url: str, timeout_sec: int = 30) -> bool:
    deadline = time.monotonic() + timeout_sec
    while time.monotonic() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=3) as resp:
                if resp.status == 200:
                    return True
        except Exception:
            time.sleep(1)
    return False


def run_step(name: str, cmd: list[str], cwd: Path = ROOT) -> tuple[str, bool, float, str]:
    t0 = time.monotonic()
    proc = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    dt = time.monotonic() - t0
    ok = proc.returncode == 0
    output = (proc.stdout + "\n" + proc.stderr).strip()
    return name, ok, dt, output


def main() -> int:
    api_url = os.environ.get("E2E_API_URL", "http://localhost:8000")
    web_url = os.environ.get("E2E_BASE_URL", "http://localhost:3000")

    api_ok = wait_for_url(f"{api_url}/api/health", timeout_sec=15)
    web_ok = wait_for_url(f"{web_url}/api/health", timeout_sec=15)

    results: list[tuple[str, bool, float, str]] = [
        ("API Health Check", api_ok, 0.0, f"{api_url}/api/health"),
        ("Web Health Check", web_ok, 0.0, f"{web_url}/api/health"),
        run_step("make verify (ruff + tsc + pytest)", ["make", "verify"]),
        run_step(
            "rules_report.json parity",
            [
                "bash",
                "-c",
                "docker compose run --rm -T api python -c \""
                "from sqlalchemy import text; from app.db import SessionLocal; "
                "from app.cli.seed import seed_database; "
                "db = SessionLocal(); "
                "db.execute(text('TRUNCATE TABLE meeting_summaries, meeting_ratings, "
                "meeting_attendees, todos, issues, meetings, milestones, rocks, scores, "
                "measurables, memberships, users, teams, companies RESTART IDENTITY CASCADE')); "
                "db.commit(); seed_database(db); db.close()\" && "
                "diff -u rules_report.json <(make -s report)",
            ],
        ),
    ]
    if api_ok and web_ok and (ROOT / "e2e" / "node_modules").exists():
        results.append(run_step("Playwright 2-Browser E2E", ["npm", "test"], cwd=ROOT / "e2e"))

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Latest Local Verification Report",
        "",
        "| Check | Status | Duration |",
        "| --- | --- | ---: |",
    ]
    all_passed = True
    for name, ok, dt, _ in results:
        status = "PASS" if ok else "FAIL"
        if not ok:
            all_passed = False
        lines.append(f"| {name} | **{status}** | {dt:.2f}s |")

    REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(REPORT_PATH.read_text(encoding="utf-8"))
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
