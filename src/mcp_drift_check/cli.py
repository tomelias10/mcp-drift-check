import argparse
import sys
from pathlib import Path
from .discovery import known_config_paths, workspace_config_paths
from .parser import parse_config
from .output import render_json, render_markdown, render_sarif, render_text

def _add_output_flags(parser):
    parser.add_argument("--json", action="store_true", dest="as_json", help="Print JSON findings")
    parser.add_argument("--markdown", action="store_true", dest="as_markdown", help="Print a compact Markdown report")
    parser.add_argument("--sarif", metavar="PATH", help="Also write SARIF 2.1.0 for GitHub Code Scanning")

def build_parser():
    p=argparse.ArgumentParser(prog="mcp-drift-check", description="Zero-execution MCP configuration security preflight. Never executes MCP servers.")
    sub=p.add_subparsers(dest="cmd", required=True)
    scan=sub.add_parser("scan", help="Scan one MCP JSON configuration")
    scan.add_argument("path")
    _add_output_flags(scan)
    workspace=sub.add_parser("scan-workspace", help="Scan only known MCP config locations in the current workspace")
    _add_output_flags(workspace)
    allp=sub.add_parser("scan-all", help="Scan known user and workspace MCP config locations without crawling the filesystem")
    _add_output_flags(allp)
    return p

def _emit(findings, args):
    if args.sarif:
        out=Path(args.sarif)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(render_sarif(findings), encoding="utf-8")
    if args.as_json:
        print(render_json(findings))
    elif args.as_markdown:
        print(render_markdown(findings))
    else:
        print(render_text(findings))

def main(argv=None):
    args=build_parser().parse_args(argv)
    findings=[]
    if args.cmd == "scan":
        findings=parse_config(args.path)
    else:
        configs=workspace_config_paths() if args.cmd == "scan-workspace" else known_config_paths()
        if not configs:
            if args.sarif:
                Path(args.sarif).write_text(render_sarif([]), encoding="utf-8")
            if args.as_json:
                print("[]")
            elif args.as_markdown:
                print("## MCP Drift Check\n\nNo known MCP configuration files found. Nothing was executed.")
            else:
                print("No known MCP configuration files found. Nothing was executed.")
            return 0
        for client, path in configs:
            findings.extend(parse_config(path, client))
    _emit(findings, args)
    return 1 if any(f.classification == "HIGH" for f in findings) else 0

if __name__ == "__main__":
    sys.exit(main())
