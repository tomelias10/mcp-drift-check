# MCP Drift Check

[![CI](https://github.com/tomelias10/mcp-drift-check/actions/workflows/ci.yml/badge.svg)](https://github.com/tomelias10/mcp-drift-check/actions/workflows/ci.yml) [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

### You approved the MCP configuration. Did you approve the code it will run next month?

MCP Drift Check is a small, passive security CLI that identifies MCP configurations whose package dependencies can resolve to different code over time. It never launches an MCP server, never downloads a package, and never sends your configuration anywhere.

> **Check your environment.** If you find something concerning in production, do not post secrets or private configs in a public issue. Request a private security review: **https://site-creator-vinext-starter.surfaceproof.workers.dev/security-triage?utm_source=github&utm_medium=repo&utm_campaign=mcp_drift_check**

## Production MCP security review

The CLI is free. If your team is running MCP or AI-agent tooling in production and wants a private assessment, SurfaceProof offers a focused paid review.

Typical deliverables:

- inventory of approved MCP/agent integrations and mutable dependency references
- privilege and data-access context for the integrations that matter most
- exact remediation and version-pinning guidance
- a CI policy/check to keep mutable references from silently reappearing
- a concise engineering/security report with prioritized next actions

Start here: **https://site-creator-vinext-starter.surfaceproof.workers.dev/security-triage?utm_source=github&utm_medium=repo&utm_campaign=mcp_drift_check**

Scope and price are agreed before work begins. No production testing is performed without explicit authorization.

## Why this exists

Many MCP clients can launch servers through package runners such as `npx`. A configuration can remain unchanged while package resolution changes later. That creates a review gap: code running today may not be the same package version that was reviewed previously.

This tool finds that condition. It does **not** claim that an unpinned dependency is malicious or compromised.

## 30-second check

```bash
python3 -m pip install git+https://github.com/tomelias10/mcp-drift-check.git
mcp-drift-check scan-all
```

Scan one file instead:

```bash
mcp-drift-check scan path/to/config.json
mcp-drift-check scan path/to/config.json --json
```

`scan-all` checks a small list of known MCP configuration locations. It does not crawl your filesystem.


## Public example of the review gap

This is not only a hypothetical packaging pattern. Microsoft has a public issue for GitHub Copilot for Azure titled **“Consider pinning Azure MCP”** where the project notes that its `.mcp.json` references the `@latest` Azure MCP package and discusses the tradeoff between automatic updates and mismatches between the reviewed/configured tools and the package version that actually resolves.

- Microsoft issue: https://github.com/microsoft/GitHub-Copilot-for-Azure/issues/3045

That issue is an example of the configuration-review problem this tool detects. It is **not** evidence that Azure MCP is malicious or compromised, and Microsoft does not endorse this project.

## What it checks

The first release focuses on package mutability in npm/npx-style MCP launch commands:

- exact versions such as `package@1.2.3` → `SAFE`
- bare packages such as `package` → `HIGH`
- explicit `package@latest` → `HIGH`
- version ranges such as `package@^1.2.0` → `MEDIUM`
- local or unknown executables → `REVIEW`
- `-y` / `--yes` is reported as context; it is not treated as a vulnerability by itself

Known-location discovery currently covers common Claude Desktop, Claude Code, Cursor, VS Code, Windsurf and generic MCP config paths where present.

## Example

```text
MCP Drift Check
================================================
MCP server entries: 3

HIGH   1 mutable package references
MEDIUM 1 non-exact package selectors
SAFE   1 exact-version package references

HIGH  github-mcp
      command: npx -y example-package
      reason: Package version is not pinned; future resolution may select different package code.
      recommendation: Pin example-package to a reviewed exact version.
```

## What it does NOT claim

- An unpinned dependency is not automatically malicious.
- A newer package version is not automatically compromised.
- A mutable package reference is not proof of exploitation.
- Pinning alone does not make an MCP integration secure.
- This tool does not test authorization, prompt injection, tool poisoning, data exposure, or runtime behavior.

It identifies a **change and review risk** that a security team may want to investigate.

## Public examples

We documented seven concrete public repositories where MCP configs contained mutable npm/npx package references. This is a **targeted examples set, not a prevalence study**. See the [public research page](https://site-creator-vinext-starter.surfaceproof.workers.dev/research/mcp-dependency-drift) or [`research/public-mcp-dependency-drift-examples.md`](research/public-mcp-dependency-drift-examples.md).

## Why we built this

While researching public MCP configurations, we observed repeated patterns where package references were mutable after the configuration was written.

We are validating the underlying dataset and methodology before publishing any aggregate statistic. Until that review is complete, this repository intentionally makes no numerical prevalence claim.

## For security teams

Use JSON output for inventory or CI workflows:

```bash
mcp-drift-check scan-all --json > mcp-drift-findings.json
```

The output includes client, config path, server name, command, package, declared version, classification, reason and recommendation.

## Private security review

Found this pattern in a production AI environment?

Do **not** post sensitive configuration, credentials, access tokens, customer information, internal URLs or proprietary data in a public GitHub issue.

Request a private security review: **https://site-creator-vinext-starter.surfaceproof.workers.dev/security-triage?utm_source=github&utm_medium=repo&utm_campaign=mcp_drift_check**

A review can help determine:

- whether the finding is actually exploitable
- what changed
- what access the MCP integration has
- whether credentials or data could be exposed
- what should be remediated
- how to verify the fix

## Privacy and safety

MCP Drift Check is static and local by design. It does not execute configured server commands, contact package registries, download dependencies, collect telemetry, or transmit findings. Common credential-bearing command arguments (for example `--api-key`, `--token`, `API_KEY=...`, and Authorization headers) are redacted from text and JSON reports. Avoid placing secrets directly in command arguments when possible.

## Development

```bash
python3 -m unittest discover -s tests -v
```

## Responsible disclosure

See [SECURITY.md](SECURITY.md).

## License

MIT
