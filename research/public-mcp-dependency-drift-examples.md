# Public examples of mutable MCP package references

**Observed:** 2026-09-25  
**Method:** targeted public-code search for MCP configuration files containing mutable npm/npx package references, followed by passive static analysis with MCP Drift Check v0.1.1.

> This is **not a prevalence study**. The examples were intentionally discovered with queries biased toward `@latest` and other mutable package references. They demonstrate that the pattern exists in real public repositories; they do not estimate how common it is across MCP deployments.

## What we checked

The scanner reads configuration text only. It did **not** start an MCP server, execute a discovered command, download a package, or transmit configuration data.

| Repository | Public config | Mutable references observed | Follow-up |
| --- | --- | --- | --- |
| dotCMS/core | [`.mcp.json`](https://github.com/dotCMS/core/blob/f5a4d4a92f5af10bdbd4146d2f744e2803faba60/.mcp.json) | `chrome-devtools-mcp@latest`, bare `@primeng/mcp`, bare `@angular/cli` | [Issue #37738](https://github.com/dotCMS/core/issues/37738) |
| WooCommerce Android | [`.mcp.json`](https://github.com/woocommerce/woocommerce-android/blob/c554edb3b4092aa417dcf27f8b7a2ea14b3a45de/.mcp.json) | `@mobilenext/mobile-mcp@latest`, `@automattic/mcp-context-a8c@latest` | [Issue #16616](https://github.com/woocommerce/woocommerce-android/issues/16616) |
| Datadog Android SDK | [`.mcp.json`](https://github.com/DataDog/dd-sdk-android/blob/f33341758a219fae3e15ebec71899330a2d47eb0/.mcp.json) | `@mobilenext/mobile-mcp@latest` | [Issue #3904](https://github.com/DataDog/dd-sdk-android/issues/3904) |
| commercetools UI Kit | [`.mcp.json`](https://github.com/commercetools/ui-kit/blob/62ca335b629de087f574af71869d68cbd3bd004c/.mcp.json) | `@upstash/context7-mcp@latest`, `@playwright/mcp@latest`, bare `@modelcontextprotocol/server-sequential-thinking` | [Issue #3307](https://github.com/commercetools/ui-kit/issues/3307) |
| IBM MCP catalog | [`mcp.json`](https://github.com/IBM/mcp/blob/c78e894c0848b9f1b1be6c2b5811121bbc9d2180/mcp.json) | bare `di-mcp-server`, bare `@datastax/astra-db-mcp`, `@ibm/ibmi-mcp-server@latest` | [Issue #66](https://github.com/IBM/mcp/issues/66) |
| CZI Single Cell Data Portal | [`.mcp.json`](https://github.com/chanzuckerberg/single-cell-data-portal/blob/f41b2a4b1a0916a12767b52f567532b30a808418/.mcp.json) | six mutable refs including bare `@modelcontextprotocol/*`, bare `@playwright/mcp`, bare `@czi-sds/mcp`, `@zeroheight/mcp-server@latest` | [Issue #7801](https://github.com/chanzuckerberg/single-cell-data-portal/issues/7801) |
| ZK | [`.mcp.json`](https://github.com/zkoss/zk/blob/9ecf689dab0d3b7281b5c47fb0923b4d16cfadba/.mcp.json) | `mcp-remote@latest` | [Issue #3628](https://github.com/zkoss/zk/issues/3628) |

## Why the pattern matters

An MCP config can remain byte-for-byte unchanged while a bare npm package or `@latest` resolves to a newer package release. That is a **review-boundary and reproducibility** issue: a team may be running code or tool schemas that were not the exact version previously reviewed.

This does **not** mean the newer package is malicious or vulnerable. Pinning also does not make a package trustworthy by itself; it makes the reviewed artifact reproducible and version changes deliberate.

## Practical control

For teams that want deterministic MCP dependencies:

1. Pin npm/npx-backed MCP packages to reviewed exact versions.
2. Update pins intentionally after review/testing.
3. Add a static CI check that flags new bare package refs, `@latest`, or non-exact selectors.
4. Treat pinning as reproducibility evidence, not as proof that a dependency is safe.

Run the passive check: [`mcp-drift-check`](https://github.com/tomelias10/mcp-drift-check)
