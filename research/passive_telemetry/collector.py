#!/usr/bin/env python3
"""Orynval passive security telemetry collector (v0).

Public-read-only collection only. No active scanning, exploitation, package execution,
or interaction with third-party systems beyond documented public HTTP APIs.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import sqlite3
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

UA = "Orynval-Research/0.1 (+https://orynval.com)"

SOURCES = {
    "cisa_kev": "https://raw.githubusercontent.com/cisagov/kev-data/develop/known_exploited_vulnerabilities.json",
    "mcp_registry": "https://registry.modelcontextprotocol.io/v0.1/servers",
    "github_advisories": "https://api.github.com/advisories",
}


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def stable_json(obj: Any) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def fetch_json(url: str, *, token: str | None = None, timeout: int = 30) -> Any:
    headers = {"User-Agent": UA, "Accept": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
        headers["X-GitHub-Api-Version"] = "2022-11-28"
    req = urllib.request.Request(url, headers=headers, method="GET")
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def init_db(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        PRAGMA journal_mode=WAL;
        CREATE TABLE IF NOT EXISTS snapshots (
            id INTEGER PRIMARY KEY,
            source TEXT NOT NULL,
            collected_at TEXT NOT NULL,
            sha256 TEXT NOT NULL,
            raw_path TEXT NOT NULL,
            item_count INTEGER,
            UNIQUE(source, sha256)
        );
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY,
            source TEXT NOT NULL,
            event_key TEXT NOT NULL,
            event_type TEXT NOT NULL,
            observed_at TEXT NOT NULL,
            payload_json TEXT NOT NULL,
            payload_sha256 TEXT NOT NULL,
            UNIQUE(source, event_key, payload_sha256)
        );
        CREATE INDEX IF NOT EXISTS idx_events_time ON events(observed_at);
        CREATE INDEX IF NOT EXISTS idx_events_source ON events(source);
        """
    )
    conn.commit()


def write_snapshot(root: Path, conn: sqlite3.Connection, source: str, payload: Any, item_count: int | None = None) -> tuple[str, bool]:
    collected_at = utc_now()
    raw = stable_json(payload)
    digest = sha256_bytes(raw)
    day = collected_at[:10]
    out_dir = root / "raw" / source / day
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"{collected_at.replace(':','')}-{digest[:12]}.json"
    cur = conn.execute("SELECT 1 FROM snapshots WHERE source=? AND sha256=?", (source, digest))
    if cur.fetchone():
        return digest, False
    path.write_bytes(raw + b"\n")
    conn.execute(
        "INSERT INTO snapshots(source,collected_at,sha256,raw_path,item_count) VALUES(?,?,?,?,?)",
        (source, collected_at, digest, str(path), item_count),
    )
    conn.commit()
    return digest, True


def add_event(conn: sqlite3.Connection, source: str, event_key: str, event_type: str, observed_at: str, payload: Any) -> bool:
    raw = stable_json(payload)
    digest = sha256_bytes(raw)
    try:
        conn.execute(
            "INSERT INTO events(source,event_key,event_type,observed_at,payload_json,payload_sha256) VALUES(?,?,?,?,?,?)",
            (source, event_key, event_type, observed_at, raw.decode("utf-8"), digest),
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False


def collect_cisa(root: Path, conn: sqlite3.Connection) -> dict[str, Any]:
    data = fetch_json(SOURCES["cisa_kev"])
    vulns = data.get("vulnerabilities", []) if isinstance(data, dict) else []
    _, fresh = write_snapshot(root, conn, "cisa_kev", data, len(vulns))
    added = 0
    for v in vulns:
        cve = v.get("cveID") or v.get("cveId") or "unknown"
        observed = v.get("dateAdded") or data.get("dateReleased") or utc_now()
        if add_event(conn, "cisa_kev", cve, "kev_entry", observed, v):
            added += 1
    return {"source": "cisa_kev", "snapshot_new": fresh, "items": len(vulns), "events_new": added}


def collect_github_advisories(root: Path, conn: sqlite3.Connection, pages: int = 2) -> dict[str, Any]:
    token = os.getenv("GITHUB_TOKEN") or os.getenv("GH_TOKEN")
    all_items: list[dict[str, Any]] = []
    for page in range(1, pages + 1):
        q = urllib.parse.urlencode({"per_page": 100, "page": page, "sort": "updated", "direction": "desc"})
        batch = fetch_json(f"{SOURCES['github_advisories']}?{q}", token=token)
        if not isinstance(batch, list) or not batch:
            break
        all_items.extend(batch)
        if len(batch) < 100:
            break
        time.sleep(0.25)
    _, fresh = write_snapshot(root, conn, "github_advisories", all_items, len(all_items))
    added = 0
    for adv in all_items:
        key = adv.get("ghsa_id") or adv.get("cve_id") or adv.get("html_url") or sha256_bytes(stable_json(adv))[:16]
        observed = adv.get("updated_at") or adv.get("published_at") or utc_now()
        if add_event(conn, "github_advisories", str(key), "advisory", observed, adv):
            added += 1
    return {"source": "github_advisories", "snapshot_new": fresh, "items": len(all_items), "events_new": added, "authenticated": bool(token)}


def collect_mcp_registry(root: Path, conn: sqlite3.Connection, max_pages: int = 200) -> dict[str, Any]:
    servers: list[dict[str, Any]] = []
    cursor: str | None = None
    for _ in range(max_pages):
        params = {"limit": 100, "version": "latest"}
        if cursor:
            params["cursor"] = cursor
        url = SOURCES["mcp_registry"] + "?" + urllib.parse.urlencode(params)
        page = fetch_json(url)
        batch = page.get("servers", []) if isinstance(page, dict) else []
        if not isinstance(batch, list):
            raise RuntimeError("Unexpected MCP Registry response: missing servers[]")
        servers.extend(batch)
        meta = page.get("metadata") or {}
        cursor = meta.get("nextCursor")
        if not cursor or not batch:
            break
        time.sleep(0.15)
    _, fresh = write_snapshot(root, conn, "mcp_registry", servers, len(servers))
    added = 0
    for row in servers:
        server = row.get("server") if isinstance(row, dict) and isinstance(row.get("server"), dict) else row
        name = server.get("name") or row.get("name") or "unknown"
        version = server.get("version") or row.get("version") or "unknown"
        status = (row.get("_meta") or {}).get("io.modelcontextprotocol.registry/official", {}).get("status") or row.get("status") or server.get("status")
        payload = {"name": name, "version": version, "status": status, "record": row}
        if add_event(conn, "mcp_registry", f"{name}@{version}", "server_version", utc_now(), payload):
            added += 1
    return {"source": "mcp_registry", "snapshot_new": fresh, "items": len(servers), "events_new": added}


def export_recent(root: Path, conn: sqlite3.Connection, hours: int = 24) -> Path:
    cutoff = (dt.datetime.now(dt.timezone.utc) - dt.timedelta(hours=hours)).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    rows = conn.execute(
        "SELECT source,event_key,event_type,observed_at,payload_json,payload_sha256 FROM events WHERE observed_at >= ? ORDER BY observed_at DESC",
        (cutoff,),
    ).fetchall()
    out_dir = root / "normalized"
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / "recent.jsonl"
    with out.open("w", encoding="utf-8") as fh:
        for source, key, typ, observed, payload_json, digest in rows:
            fh.write(json.dumps({
                "source": source,
                "event_key": key,
                "event_type": typ,
                "observed_at": observed,
                "payload_sha256": digest,
                "payload": json.loads(payload_json),
            }, ensure_ascii=False) + "\n")
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="Passive public security telemetry collector for Orynval research")
    ap.add_argument("--root", default=os.getenv("ORYNVAL_TELEMETRY_ROOT", "./telemetry-data"))
    ap.add_argument("--source", action="append", choices=["cisa_kev", "github_advisories", "mcp_registry"], help="Collect only selected source(s)")
    ap.add_argument("--github-pages", type=int, default=2, help="Recent GitHub advisory pages to collect (100/page)")
    args = ap.parse_args()

    root = Path(args.root).expanduser().resolve()
    root.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(root / "telemetry.sqlite3")
    init_db(conn)
    selected = args.source or ["cisa_kev", "github_advisories", "mcp_registry"]
    results: list[dict[str, Any]] = []
    for name in selected:
        try:
            if name == "cisa_kev":
                results.append(collect_cisa(root, conn))
            elif name == "github_advisories":
                results.append(collect_github_advisories(root, conn, pages=max(1, args.github_pages)))
            elif name == "mcp_registry":
                results.append(collect_mcp_registry(root, conn))
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, RuntimeError, json.JSONDecodeError) as exc:
            results.append({"source": name, "error": f"{type(exc).__name__}: {exc}"})
    recent = export_recent(root, conn)
    print(json.dumps({"collected_at": utc_now(), "root": str(root), "recent": str(recent), "results": results}, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
