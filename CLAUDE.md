# Instructions for Claude (auto-loaded every session)

This repo has a persistent knowledge vault at `vault/`, which Claude maintains. It is the
project's long-term memory: anything not written there is lost when the context window is
compacted or the session ends.

## Always loaded
@vault/_memory/MEMORY.md

## Vault protocol (mandatory)
1. **At the start of a task**, read the memory above. Open `vault/00-INDEX.md` and the notes
   relevant to the task before re-researching anything. Do not re-derive facts that are already
   recorded.
2. **While working**, write knowledge down as soon as you learn it, not at the end:
   - new facts and research → the relevant topic note (with sources and a confidence tag:
     [doc] [paper] [inferred] [assumption])
   - material the user gives you (transcripts, links, ideas) → `vault/inbox/YYYY-MM-DD-slug.md`,
     with a summary, an assessment, and where it was integrated
   - decisions (what changed, and why) → `python tools/vault.py decide ...`
     (writes to `vault/_memory/decisions.md`)
   - experiment and backtest results → `vault/results/` (Phase 3+) and the trial log
3. **Before finishing a task (every turn that changed something)**:
   - append a session journal entry: `python tools/vault.py journal "..."`
     (writes to `vault/journal/`)
   - update `vault/_memory/MEMORY.md` (state, next step, open questions). Keep it under about
     150 lines; details belong in topic notes.
   - run `python tools/vault.py check` and `python -m pytest`
   - commit and push (the container is ephemeral; unpushed vault edits are lost)
4. Links are relative Markdown links (`[text](path.md)`), so they work in both Obsidian and
   GitHub. Notes start with YAML frontmatter.
5. The user's own words and requirements are in `vault/_memory/project-brief.md`. Where
   research contradicts the brief, the research wins. Record the conflict as a decision.

## Project rules (summary; details in the vault)
- Python 3.11, the `databento` client, pandas/numpy, pytest. The API key comes only from `.env`.
  Never print or commit it.
- Cost guard: `metadata.get_cost` before every download. Never more than $5 without asking.
- Work in phases. Stop at the end of each phase and wait for the user's OK.
- No live trading and no broker connections.
- Be skeptical. Too-good results mean: look for lookahead, leakage or bad fills first.
