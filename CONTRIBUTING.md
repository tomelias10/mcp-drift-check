# Contributing

Thanks for helping make MCP configuration review more reproducible.

## Good contributions

- support for additional MCP client config locations
- package selector edge cases with small fixtures
- redaction improvements
- output integrations such as SARIF and CI
- public examples that can be independently verified without active testing

## Safety boundary

MCP Drift Check is intentionally static. Contributions must not execute discovered MCP server commands, download discovered packages, probe remote systems, or transmit users' configurations by default.

## Test

```bash
python -m pip install .
python -m unittest discover -s tests -v
```

Please keep findings factual: a mutable dependency is a review/reproducibility risk, not proof that a package is malicious or compromised.
