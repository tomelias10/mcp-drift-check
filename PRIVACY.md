# Privacy behavior

MCP Drift Check is designed to keep local and CI scans local by default.

## CLI

The CLI does not execute configured MCP servers, contact package registries, download discovered dependencies, collect telemetry, or transmit scan findings.

## GitHub Action

The GitHub Action runs the same static scanner against repository workspace paths. By default it does **not** add Orynval-hosted links or badges to the job summary, so the action does not intentionally disclose `GITHUB_REPOSITORY` to Orynval.

The optional `share-public-result: 'true'` input adds an Orynval public-preflight link and badge containing the repository identifier. Use that option only when repository-name disclosure is acceptable, such as for a public repository.

Because the badge is hosted by Orynval, rendering it can cause GitHub or the viewer's browser to request the badge URL from Orynval. Private repositories should leave `share-public-result` at its default value of `false` unless the repository owner explicitly accepts that disclosure.

## Reports

Text and JSON reports redact common credential-bearing command arguments such as API keys, tokens, authorization headers, and similar values. Do not place secrets directly in command arguments when avoidable.

## Network boundary

The scanner itself performs static parsing. Browser-based public-repository scanning on `orynval.com` is a separate hosted feature and necessarily makes network requests to retrieve public repository configuration.
