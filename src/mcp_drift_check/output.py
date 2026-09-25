import json

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
