# Orynval Passive Telemetry v0

Purpose: build a **historical, reproducible, public-data security signal lake** for Orynval research without active scanning or executing third-party code.

## v0 sources

- CISA KEV — confirmed known-exploited vulnerabilities.
- GitHub Global Security Advisories — recent open-source vulnerability/malware advisories.
- Official MCP Registry — server/version/status metadata, snapshotted over time.

The collector stores raw snapshots plus normalized event rows in SQLite. The value is not a one-time scrape; it is the **history of change** we retain and can later correlate with package/repo/config timelines.

## Safety boundary

- Public documented GET endpoints only.
- No port scanning.
- No login/credential testing.
- No package installation or execution.
- No cloning/executing unknown repositories.
- No public vulnerability claims from model output.

## Run

```bash
python3 collector.py --root ~/orynval-signal-lake
```

Optional GitHub token (for higher API limits only):

```bash
export GH_TOKEN="$(gh auth token)"
python3 collector.py --root ~/orynval-signal-lake
```

## Data layout

```text
~/orynval-signal-lake/
  telemetry.sqlite3
  raw/<source>/<day>/*.json
  normalized/recent.jsonl
```

## Next layers (not in v0)

1. Package timeline snapshots for npm/PyPI packages referenced by MCP/agent configs.
2. GitHub code-search snapshots for repo-borne agent trust files (`AGENTS.md`, `CLAUDE.md`, MCP configs, skills/hooks).
3. Repository/file commit timelines for selected public samples.
4. Deterministic diff/event generation (new server, changed repo, new package release, deleted/deprecated registry entry).
5. Jev as a **triage/scoring layer only**, never as a factual source.
6. Astra/Claude/Gemini/Grok only after deterministic collection narrows candidates.

## Research objective

Create evidence for questions like:

- Which agent/MCP artifacts changed *after* users were likely to trust them?
- Which public configurations would have resolved to a newly malicious/vulnerable release during a real incident window?
- Which repo-borne instruction/tool surfaces are growing fastest and carry the most privilege?

The goal is an evidence-backed research asset and free diagnostic that naturally creates Orynval security inbound.
