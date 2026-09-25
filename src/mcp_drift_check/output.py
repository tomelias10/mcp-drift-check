import json
from pathlib import Path

ORDER={"HIGH":0,"MEDIUM":1,"REVIEW":2,"SAFE":3}

def render_text(findings):
    counts={k:0 for k in ORDER}
    for f in findings: counts[f.classification]=counts.get(f.classification,0)+1
    lines=["MCP Drift Check", "="*48, f"MCP server entries: {len(findings)}", "", f"HIGH   {counts.get('HIGH',0)} mutable package references", f"MEDIUM {counts.get('MEDIUM',0)} non-exact package selectors", f"REVIEW {counts.get('REVIEW',0)} entries requiring manual review", f"SAFE   {counts.get('SAFE',0)} exact-version package references", ""]
    for f in sorted(findings, key=lambda x: ORDER.get(x.classification,9)):
        lines += [f"{f.classification:<6} {f.server_name}", f"       client: {f.client}", f"       config: {f.config_path}"]
        if f.command: lines.append(f"       command: {f.command}")
        if f.package: lines.append(f"       package: {f.package}" + (f" @{f.declared_version}" if f.declared_version else ""))
        lines += [f"       reason: {f.reason}", f"       recommendation: {f.recommendation}", ""]
    lines += ["No MCP servers were executed.", "No credentials or secrets were collected.", "All analysis was performed locally.", "", "Found something concerning in a production environment?", "Request private security triage: https://site-creator-vinext-starter.surfaceproof.workers.dev/security-triage?utm_source=github&utm_medium=repo&utm_campaign=mcp_drift_check"]
    return "\n".join(lines)

def render_json(findings):
    return json.dumps([f.to_dict() for f in findings], indent=2)

def render_markdown(findings):
    counts={k:0 for k in ORDER}
    for f in findings:
        counts[f.classification]=counts.get(f.classification,0)+1
    lines=[
        "## MCP Drift Check",
        "",
        "Static scan only — **no MCP servers executed, no package downloads, no telemetry**.",
        "",
        "| High | Medium | Review | Safe |",
        "| ---: | ---: | ---: | ---: |",
        f"| {counts.get('HIGH',0)} | {counts.get('MEDIUM',0)} | {counts.get('REVIEW',0)} | {counts.get('SAFE',0)} |",
        "",
    ]
    risky=[f for f in sorted(findings, key=lambda x: ORDER.get(x.classification,9)) if f.classification != "SAFE"]
    if not risky:
        lines += ["✅ No mutable or non-exact MCP package references found.", ""]
    else:
        lines += ["### Findings", ""]
        for f in risky:
            package=f.package or f.command or "manual review"
            lines += [
                f"- **{f.classification}** `{f.server_name}` — `{package}`",
                f"  - {f.reason}",
                f"  - **Fix:** {f.recommendation}",
            ]
        lines.append("")
    lines += ["[MCP Drift Check](https://github.com/tomelias10/mcp-drift-check) · zero-execution MCP configuration preflight"]
    return "\n".join(lines)

def _sarif_rule(classification):
    if classification == "HIGH":
        return "MCP001", "Mutable MCP package reference", "error"
    if classification == "MEDIUM":
        return "MCP002", "Non-exact MCP package selector", "warning"
    return "MCP003", "MCP configuration requires review", "note"

def render_sarif(findings):
    rules={}
    results=[]
    for f in findings:
        if f.classification == "SAFE":
            continue
        rule_id, rule_name, level = _sarif_rule(f.classification)
        rules[rule_id]={
            "id": rule_id,
            "name": rule_name,
            "shortDescription": {"text": rule_name},
            "helpUri": "https://github.com/tomelias10/mcp-drift-check#what-it-checks",
        }
        uri=str(Path(f.config_path)).replace("\\", "/")
        results.append({
            "ruleId": rule_id,
            "level": level,
            "message": {"text": f"{f.server_name}: {f.reason} Recommendation: {f.recommendation}"},
            "locations": [{
                "physicalLocation": {"artifactLocation": {"uri": uri}}
            }],
            "properties": {
                "classification": f.classification,
                "client": f.client,
                "server": f.server_name,
                "package": f.package,
                "declaredVersion": f.declared_version,
            },
        })
    doc={
        "$schema": "https://json.schemastore.org/sarif-2.1.0.json",
        "version": "2.1.0",
        "runs": [{
            "tool": {"driver": {
                "name": "MCP Drift Check",
                "informationUri": "https://github.com/tomelias10/mcp-drift-check",
                "rules": list(rules.values()),
            }},
            "results": results,
        }],
    }
    return json.dumps(doc, indent=2)
