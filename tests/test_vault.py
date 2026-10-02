from datetime import date
from pathlib import Path

from tools import vault as v

REPO = Path(__file__).resolve().parent.parent


def test_real_vault_is_healthy():
    """Every note has frontmatter, every relative link resolves, MEMORY.md stays short."""
    assert v.check() == []


def test_claude_md_imports_memory():
    text = (REPO / "CLAUDE.md").read_text()
    assert "@vault/_memory/MEMORY.md" in text
    assert (REPO / "vault/_memory/MEMORY.md").exists()


def test_journal_appends(tmp_path):
    p = v.journal("first", "Phase 2 work", vault=tmp_path, today=date(2026, 1, 2))
    v.journal("second", "Phase 2 work", vault=tmp_path, today=date(2026, 1, 2))
    text = p.read_text()
    assert p.name == "2026-01-02-phase-2-work.md"
    assert text.startswith("---\n") and "first" in text and "second" in text


def test_decide_numbers_sequentially(tmp_path):
    a = v.decide("A", "do a", "because", vault=tmp_path, today=date(2026, 1, 2))
    b = v.decide("B", "do b", "because", alternatives="c", vault=tmp_path, today=date(2026, 1, 2))
    assert (a, b) == ("D-001", "D-002")
    assert "**Alternatives:** c" in (tmp_path / "_memory/decisions.md").read_text()


def test_check_finds_broken_links_and_missing_frontmatter(tmp_path):
    (tmp_path / "_memory").mkdir()
    (tmp_path / "_memory/MEMORY.md").write_text("---\ntype: memory\n---\nok\n")
    (tmp_path / "a.md").write_text("no frontmatter [x](missing.md) [web](https://x.org) [s](#sec)\n"
                                   "```\n[ignored](in-code.md)\n```\n")
    problems = v.check(tmp_path)
    assert any("missing YAML frontmatter" in p for p in problems)
    assert any("broken link -> missing.md" in p for p in problems)
    assert not any("in-code.md" in p or "x.org" in p for p in problems)


def test_inbox_and_search(tmp_path):
    p = v.inbox("Some video", "user", "Monte Carlo on every set", vault=tmp_path, today=date(2026, 1, 2))
    assert "status: unprocessed" in p.read_text()
    assert any("Monte Carlo" in h for h in v.search("monte carlo", vault=tmp_path))
