# Security Policy

## Reporting a vulnerability in MCP Drift Check

Please do not include credentials, tokens, private MCP configurations, customer data, internal URLs, or other sensitive information in a public GitHub issue.

For a vulnerability in this tool, use GitHub's **Report a vulnerability** flow under the repository Security tab so the report stays private. If the issue is non-sensitive and does not expose exploit details, secrets, private configurations, or customer data, a minimal public issue is also acceptable.

## Production MCP findings

This repository is not a place to disclose secrets or production configuration. If this tool identifies a concerning pattern in a real environment, use **https://site-creator-vinext-starter.surfaceproof.workers.dev/security-triage?utm_source=github&utm_medium=repo&utm_campaign=mcp_drift_check** for private triage.

## Scope of the tool

The default scanner is passive. It parses local JSON configuration files and classifies command/package references. It must not execute MCP server commands, install packages, contact package registries, or transmit findings.
