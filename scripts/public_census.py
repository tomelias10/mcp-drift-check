#!/usr/bin/env python3
"""Build a sanitized, reproducible GitHub code-search sample of MCP package drift.

This script searches public GitHub code for .mcp.json files that mention npm/npx,
fetches the exact blob returned by search, and classifies npm package selectors using
MCP Drift Check's existing static parser. It never executes an MCP server or package.
"""
from __future__ import annotations

import argparse
import concurrent.futures
import datetime as dt
import json
import subprocess
import sys
import urllib.request
from pathlib import Path

from mcp_drift_check.classifier import classify_package
from mcp_drift_check.parser import _command_parts, _extract_npm_spec, _walk_mcp_servers

DEFAULT_QUERIES = ('"npx" filename:.mcp.json', '"npm exec" filename:.mcp.json')
LIMITATIONS = [
    "GitHub code search ranking is not a random sample and is capped by query/result limits.",
    "Counts describe this retrieved sample only and MUST NOT be presented as ecosystem prevalence.",
    "Only npm/npx package references are classified; other commands are outside this census.",
    "No raw config contents, environment values, credentials, server names, or command arguments are stored.",
]


def run_json(command: list[str], timeout: int = 60):
    proc = subprocess.run(command, capture_output=True, text=True, timeout=timeout)
    if proc.returncode:
        raise RuntimeError(proc.stderr.strip() or "command failed")
    return json.loads(proc.stdout or "[]")


def repo_name(value) -> str | None:
    if not isinstance(value, dict):
        return None
    return value.get("nameWithOwner") or value.get("fullName") or value.get("full_name")


def search_hits(queries: tuple[str, ...], limit: int):
    deduped: dict[tuple[str, str, str], dict] = {}
    for query in queries:
        rows = run_json([
            "gh", "search", "code", query, "--limit", str(limit),
            "--json", "repository,path,url",
        ])
        print(f"query {query!r}: {len(rows)} results", file=sys.stderr)
        for row in rows:
            repo = repo_name(row.get("repository"))
            path = str(row.get("path") or "")
            url = str(row.get("url") or "")
            if not repo or not url or Path(path).name != ".mcp.json":
                continue
            deduped[(repo, path, url)] = row
    return sorted(deduped)


def raw_url(blob_url: str) -> str:
    if not blob_url.startswith("https://github.com/") or "/blob/" not in blob_url:
        raise ValueError("unexpected GitHub blob URL")
    owner_repo, tail = blob_url.removeprefix("https://github.com/").split("/blob/", 1)
    return f"https://raw.githubusercontent.com/{owner_repo}/{tail}"


def fetch_and_classify(hit: tuple[str, str, str]):
    repo, path, url = hit
    try:
        req = urllib.request.Request(raw_url(url), headers={"User-Agent": "mcp-drift-check-census/1"})
        with urllib.request.urlopen(req, timeout=10) as response:
            body = response.read(512_000).decode("utf-8", "replace")
        data = json.loads(body)
    except Exception as exc:
        return {"repo": repo, "path": path, "url": url, "error": exc.__class__.__name__}

    findings = []
    seen = set()
    for servers in _walk_mcp_servers(data):
        for name, server in servers.items():
            key = (id(servers), name)
            if key in seen:
                continue
            seen.add(key)
            parts, parse_error = _command_parts(server)
            if parse_error:
                continue
            spec, auto_yes = _extract_npm_spec(parts)
            if not spec:
                continue
            package, selector, level, _reason, _recommendation = classify_package(spec, auto_yes)
            findings.append({
                "package": package,
                "selector": selector,
                "level": level,
                "auto_yes": bool(auto_yes),
            })

    findings.sort(key=lambda item: ((item["package"] or "").lower(), item["selector"] or ""))
    return {"repo": repo, "path": path, "url": url, "findings": findings}


def summarize(hits, results, observation_date: str, queries, limit: int):
    parsed = [row for row in results if "findings" in row]
    with_packages = [row for row in parsed if row["findings"]]
    findings = [finding for row in with_packages for finding in row["findings"]]
    levels = {level: sum(f["level"] == level for f in findings) for level in ("HIGH", "MEDIUM", "SAFE", "REVIEW")}
    configs = {
        level: sum(any(f["level"] == level for f in row["findings"]) for row in with_packages)
        for level in ("HIGH", "MEDIUM", "SAFE", "REVIEW")
    }
    return {
        "observation_date": observation_date,
        "method": "GitHub code-search sample; exact basename .mcp.json; static MCP Drift Check classification; no MCP server execution",
        "queries": list(queries),
        "per_query_limit": limit,
        "limitations": LIMITATIONS,
        "search_hits_exact_config": len(hits),
        "configs_fetched_and_parsed": len(parsed),
        "configs_with_npm_package_refs": len(with_packages),
        "package_refs_classified": len(findings),
        "package_ref_levels": levels,
        "configs_containing_level": configs,
        "fetch_or_parse_errors": len(results) - len(parsed),
    }


def markdown(summary: dict, json_name: str) -> str:
    levels = summary["package_ref_levels"]
    configs = summary["configs_containing_level"]
    lines = [
        f"# Public MCP dependency-drift census — {summary['observation_date']}",
        "",
        "This is a **reproducible GitHub code-search sample, not an ecosystem prevalence estimate**.",
        "It statically inspects public files whose exact basename is `.mcp.json` and that were returned by the documented GitHub searches.",
        "",
        "No MCP server was executed. No package was downloaded. The dataset stores only public repository/path URLs and classified package selectors; it does not store raw configs, environment values, credentials, server names, or command arguments.",
        "",
        "## Snapshot",
        "",
        f"- Exact `.mcp.json` search hits after de-duplication: **{summary['search_hits_exact_config']}**",
        f"- Configs fetched and parsed: **{summary['configs_fetched_and_parsed']}**",
        f"- Configs containing npm/npx package references: **{summary['configs_with_npm_package_refs']}**",
        f"- Configs containing at least one HIGH mutable reference: **{configs['HIGH']}**",
        f"- Package references classified: **{summary['package_refs_classified']}**",
        f"- HIGH package references (bare package or `@latest`): **{levels['HIGH']}**",
        f"- MEDIUM package references (non-exact selector): **{levels['MEDIUM']}**",
        f"- SAFE exact semantic-version references: **{levels['SAFE']}**",
        "",
        "## What this does **not** prove",
        "",
        "- It does not show that any package is malicious or compromised.",
        "- It does not measure the percentage of all MCP configs that are mutable. GitHub search ranking and result caps make this a targeted search sample, not a random population sample.",
        "- A HIGH result means a reviewed config can resolve to different package code later unless the package reference is pinned.",
        "",
        "## Method and reproduction",
        "",
        "The snapshot was generated with `scripts/public_census.py`, which uses the same static package-selector classifier as the CLI.",
        "",
        "```bash",
        f"PYTHONPATH=src python3 scripts/public_census.py --limit {summary['per_query_limit']}",
        "```",
        "",
        f"Machine-readable sample: [`{json_name}`](./{json_name}).",
        "",
    ]
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--limit", type=int, default=500, help="maximum GitHub results requested per query")
    parser.add_argument("--workers", type=int, default=24)
    parser.add_argument("--date", default=dt.date.today().isoformat())
    parser.add_argument("--json-out", type=Path)
    parser.add_argument("--md-out", type=Path)
    args = parser.parse_args()
    if args.limit < 1 or args.limit > 1000:
        parser.error("--limit must be between 1 and 1000")
    if args.workers < 1 or args.workers > 64:
        parser.error("--workers must be between 1 and 64")

    json_out = args.json_out or Path(f"research/public-mcp-drift-census-{args.date}.json")
    md_out = args.md_out or Path(f"research/public-mcp-drift-census-{args.date}.md")
    hits = search_hits(DEFAULT_QUERIES, args.limit)
    print(f"unique exact .mcp.json hits: {len(hits)}", file=sys.stderr)

    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as executor:
        for index, row in enumerate(executor.map(fetch_and_classify, hits), 1):
            results.append(row)
            if index % 100 == 0:
                print(f"processed {index}", file=sys.stderr)

    summary = summarize(hits, results, args.date, DEFAULT_QUERIES, args.limit)
    records = [
        {"repo": row["repo"], "path": row["path"], "url": row["url"], "findings": row["findings"]}
        for row in results if row.get("findings")
    ]
    records.sort(key=lambda row: (row["repo"].lower(), row["path"]))
    payload = {"summary": summary, "records": records}

    json_out.parent.mkdir(parents=True, exist_ok=True)
    md_out.parent.mkdir(parents=True, exist_ok=True)
    json_out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    md_out.write_text(markdown(summary, json_out.name), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
