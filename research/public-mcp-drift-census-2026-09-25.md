# Public MCP dependency-drift census — 2026-09-25

This is a **reproducible GitHub code-search sample, not an ecosystem prevalence estimate**.
It statically inspects public files whose exact basename is `.mcp.json` and that were returned by the documented GitHub searches.

No MCP server was executed. No package was downloaded. The dataset stores only public repository/path URLs and classified package selectors; it does not store raw configs, environment values, credentials, server names, or command arguments.

## Snapshot

- Exact `.mcp.json` search hits after de-duplication: **296**
- Configs fetched and parsed: **295**
- Configs containing npm/npx package references: **259**
- Configs containing at least one HIGH mutable reference: **232**
- Package references classified: **392**
- HIGH package references (bare package or `@latest`): **360**
- MEDIUM package references (non-exact selector): **3**
- SAFE exact semantic-version references: **29**

## What this does **not** prove

- It does not show that any package is malicious or compromised.
- It does not measure the percentage of all MCP configs that are mutable. GitHub search ranking and result caps make this a targeted search sample, not a random population sample.
- A HIGH result means a reviewed config can resolve to different package code later unless the package reference is pinned.

## Method and reproduction

The snapshot was generated with `scripts/public_census.py`, which uses the same static package-selector classifier as the CLI.

```bash
PYTHONPATH=src python3 scripts/public_census.py --limit 500
```

Machine-readable sample: [`public-mcp-drift-census-2026-09-25.json`](./public-mcp-drift-census-2026-09-25.json).
