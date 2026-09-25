import argparse
import sys
from .discovery import known_config_paths
from .parser import parse_config
from .output import render_json, render_text

def build_parser():
    p=argparse.ArgumentParser(prog="mcp-drift-check", description="Passive MCP dependency drift checker. Never executes MCP servers.")
    sub=p.add_subparsers(dest="cmd", required=True)
    scan=sub.add_parser("scan", help="Scan one MCP JSON configuration")
    scan.add_argument("path")
    scan.add_argument("--json", action="store_true", dest="as_json")
    allp=sub.add_parser("scan-all", help="Scan known MCP config locations without crawling the filesystem")
    allp.add_argument("--json", action="store_true", dest="as_json")
    return p

def main(argv=None):
    args=build_parser().parse_args(argv)
    findings=[]
    if args.cmd == "scan":
        findings=parse_config(args.path)
    else:
        configs=known_config_paths()
        if not configs:
            print("No known MCP configuration files found. Nothing was executed.")
            return 0
        for client, path in configs:
            findings.extend(parse_config(path, client))
    print(render_json(findings) if args.as_json else render_text(findings))
    return 1 if any(f.classification == "HIGH" for f in findings) else 0

if __name__ == "__main__":
    sys.exit(main())
