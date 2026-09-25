# Security Policy

## Reporting a vulnerability in MCP Drift Check

Please do not include credentials, tokens, private MCP configurations, customer data, internal URLs, or other sensitive information in a public GitHub issue.

For a vulnerability in this tool, open a minimal public issue only if it can be described safely without sensitive data. Otherwise use the private contact channel that will be published with the project before external launch.

## Production MCP findings

This repository is not a place to disclose secrets or production configuration. If this tool identifies a concerning pattern in a real environment, use **https://surfaceproof-security.tome1.chatgpt.site/security-triage?utm_source=github&utm_medium=repo&utm_campaign=mcp_drift_check** for private triage once that URL is configured.

## Scope of the tool

The default scanner is passive. It parses local JSON configuration files and classifies command/package references. It must not execute MCP server commands, install packages, contact package registries, or transmit findings.
