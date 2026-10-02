"""Maintain the project knowledge vault (Claude's persistent memory).

Usage:
  python tools/vault.py journal "What happened / results / next" --title "phase-2 footprint"
  python tools/vault.py decide "Title" --decision "..." --why "..." [--alternatives "..."] [--status active]
  python tools/vault.py inbox "Title" --source "where it came from" --body "summary + assessment"
  python tools/vault.py search "regex"
  python tools/vault.py check            # links resolve, frontmatter present, MEMORY.md short

The vault is plain Markdown with YAML frontmatter and relative links, so it
opens directly in Obsidian and renders on GitHub.
"""
from __future__ import annotations

import argparse
import re
import sys
from datetime import date, datetime, timezone
from pathlib import Path

VAULT = Path(__file__).resolve().parent.parent / "vault"
MEMORY_MAX_LINES = 150
LINK_RE = re.compile(r"\[[^\]]*\]\(([^)\s]+)\)")


def _slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")[:60] or "note"


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")


def journal(body: str, title: str = "session", vault: Path = VAULT, today: date | None = None) -> Path:
    """Append an entry to today's journal note for `title` (created if missing)."""
    today = today or date.today()
    path = vault / "journal" / f"{today.isoformat()}-{_slug(title)}.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.write_text(f"---\ntype: journal\ndate: {today.isoformat()}\ntags: [journal]\n---\n"
                        f"# {title}\n")
    with path.open("a") as f:
        f.write(f"\n## {_now()}\n{body.strip()}\n")
    return path


def decide(title: str, decision: str, why: str, alternatives: str = "", status: str = "active",
           vault: Path = VAULT, today: date | None = None) -> str:
    """Append the next D-NNN entry to the decision log; returns its id."""
    today = today or date.today()
    path = vault / "_memory" / "decisions.md"
    text = path.read_text() if path.exists() else "---\ntype: decision-log\n---\n# Decision log\n"
    nums = [int(n) for n in re.findall(r"^## D-(\d{3})", text, flags=re.M)]
    did = f"D-{(max(nums) + 1) if nums else 1:03d}"
    entry = (f"\n## {did} — {title} ({today.isoformat()})\n- **Decision:** {decision}\n"
             f"- **Why:** {why}\n")
    if alternatives:
        entry += f"- **Alternatives:** {alternatives}\n"
    entry += f"- **Status:** {status}.\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip("\n") + "\n" + entry)
    return did


def inbox(title: str, source: str, body: str, vault: Path = VAULT, today: date | None = None) -> Path:
    today = today or date.today()
    path = vault / "inbox" / f"{today.isoformat()}-{_slug(title)}.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"---\ntype: source\nsource: {source}\nreceived: {today.isoformat()}\n"
                    f"status: unprocessed\ntags: [inbox]\n---\n# {title}\n\n{body.strip()}\n")
    return path


def search(pattern: str, vault: Path = VAULT) -> list[str]:
    rx = re.compile(pattern, re.I)
    hits = []
    for p in sorted(vault.rglob("*.md")):
        for i, line in enumerate(p.read_text().splitlines(), 1):
            if rx.search(line):
                hits.append(f"{p.relative_to(vault)}:{i}: {line.strip()}")
    return hits


def check(vault: Path = VAULT) -> list[str]:
    """Return a list of problems (empty = healthy)."""
    problems = []
    for p in sorted(vault.rglob("*.md")):
        if ".obsidian" in p.parts:
            continue
        text = p.read_text()
        rel = p.relative_to(vault)
        if not text.startswith("---\n") or "\n---\n" not in text[4:]:
            problems.append(f"{rel}: missing YAML frontmatter")
        in_code = False
        for line in text.splitlines():
            if line.strip().startswith("```"):
                in_code = not in_code
            if in_code:
                continue
            for target in LINK_RE.findall(line):
                if re.match(r"^[a-z]+:", target) or target.startswith("#"):
                    continue  # external URL or same-note anchor
                dest = (p.parent / target.split("#", 1)[0]).resolve()
                if not dest.exists():
                    problems.append(f"{rel}: broken link -> {target}")
    mem = vault / "_memory" / "MEMORY.md"
    if not mem.exists():
        problems.append("_memory/MEMORY.md missing")
    elif len(mem.read_text().splitlines()) > MEMORY_MAX_LINES:
        problems.append(f"_memory/MEMORY.md longer than {MEMORY_MAX_LINES} lines; move details to topic notes")
    return problems


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    j = sub.add_parser("journal"); j.add_argument("body"); j.add_argument("--title", default="session")
    d = sub.add_parser("decide"); d.add_argument("title"); d.add_argument("--decision", required=True)
    d.add_argument("--why", required=True); d.add_argument("--alternatives", default="")
    d.add_argument("--status", default="active")
    i = sub.add_parser("inbox"); i.add_argument("title"); i.add_argument("--source", required=True)
    i.add_argument("--body", required=True)
    s = sub.add_parser("search"); s.add_argument("pattern")
    sub.add_parser("check")
    a = ap.parse_args(argv)

    if a.cmd == "journal":
        print(journal(a.body, a.title))
    elif a.cmd == "decide":
        print(decide(a.title, a.decision, a.why, a.alternatives, a.status))
    elif a.cmd == "inbox":
        print(inbox(a.title, a.source, a.body))
    elif a.cmd == "search":
        print("\n".join(search(a.pattern)) or "(no matches)")
    elif a.cmd == "check":
        problems = check()
        print("\n".join(problems) or "vault OK")
        return 1 if problems else 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
