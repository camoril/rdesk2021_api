#!/usr/bin/env python3
"""Minimal RadiusDesk API probe and mapper.

This script focuses on the permanent-user endpoints documented by RadiusDesk.
It can:

- verify the API base URL
- list realms
- list profiles
- show the permanent-user create payload shape

It does not create or modify data unless the add-user command is used.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any


DEFAULT_TIMEOUT = 15
DEFAULT_EXPORT_LIMIT = 100

EXPORT_SPECS = {
    "realms": {
        "endpoint": "/cake3/rd_cake/realms/index.json",
        "filename": "realms",
    },
    "permanent-users": {
        "endpoint": "/cake3/rd_cake/permanent-users/index.json",
        "filename": "permanent-users",
    },
    "devices": {
        "endpoint": "/cake3/rd_cake/devices/index.json",
        "filename": "devices",
    },
}

KNOWN_QUERY_ENDPOINTS = [
    ("realms", "/cake3/rd_cake/realms/index-ap-create.json", True),
    ("realms-index", "/cake3/rd_cake/realms/index.json", True),
    ("realms-filter", "/cake3/rd_cake/realms/index-for-filter.json", True),
    ("profiles", "/cake3/rd_cake/profiles/index-ap.json", True),
    ("permanent-users", "/cake3/rd_cake/permanent-users/index.json", True),
    ("permanent-users-export", "/cake3/rd_cake/permanent-users/export-csv", True),
    ("permanent-users-basic", "/cake3/rd_cake/permanent-users/view-basic-info.json", True),
    ("permanent-users-password", "/cake3/rd_cake/permanent-users/view-password.json", True),
    ("permanent-users-menu-grid", "/cake3/rd_cake/permanent-users/menu-for-grid.json", True),
    ("permanent-users-menu-auth", "/cake3/rd_cake/permanent-users/menu-for-authentication-data.json", True),
    ("permanent-users-menu-accounting", "/cake3/rd_cake/permanent-users/menu-for-accounting-data.json", True),
    ("permanent-users-menu-devices", "/cake3/rd_cake/permanent-users/menu-for-user-devices.json", True),
    ("permanent-users-private-attr", "/cake3/rd_cake/permanent-users/private-attr-index.json", True),
    ("devices", "/cake3/rd_cake/devices/index.json", True),
    ("devices-export", "/cake3/rd_cake/devices/export-csv", True),
    ("devices-basic", "/cake3/rd_cake/devices/view-basic-info.json", True),
    ("devices-edit-basic", "/cake3/rd_cake/devices/edit-basic-info.json", True),
    ("devices-menu-grid", "/cake3/rd_cake/devices/menu-for-grid.json", True),
    ("devices-menu-auth", "/cake3/rd_cake/devices/menu-for-authentication-data.json", True),
    ("devices-menu-accounting", "/cake3/rd_cake/devices/menu-for-accounting-data.json", True),
    ("devices-private-attr", "/cake3/rd_cake/devices/private-attr-index.json", True),
    ("vouchers", "/cake3/rd_cake/vouchers/index.json", True),
    ("vouchers-basic", "/cake3/rd_cake/vouchers/view-basic-info.json", True),
    ("vouchers-menu-grid", "/cake3/rd_cake/vouchers/menu-for-grid.json", True),
]


@dataclass
class ApiResult:
    endpoint: str
    method: str
    status: int | None
    ok: bool
    payload: Any | None
    content_type: str | None = None
    error: str | None = None


def build_url(base_url: str, path: str, query: dict[str, str] | None = None) -> str:
    url = base_url.rstrip("/") + path
    if query:
        url = f"{url}?{urllib.parse.urlencode(query)}"
    return url


def request_json(
    url: str,
    method: str = "GET",
    data: dict[str, Any] | None = None,
    timeout: int = DEFAULT_TIMEOUT,
) -> ApiResult:
    headers = {"Accept": "application/json"}
    body = None
    if data is not None:
        headers["Content-Type"] = "application/json"
        body = json.dumps(data).encode("utf-8")

    request = urllib.request.Request(url, data=body, headers=headers, method=method)

    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read().decode("utf-8", errors="replace")
            content_type = response.headers.get_content_type()
            try:
                payload = json.loads(raw)
            except json.JSONDecodeError:
                payload = {"raw": raw}
            return ApiResult(
                endpoint=url,
                method=method,
                status=response.getcode(),
                ok=True,
                payload=payload,
                content_type=content_type,
            )
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        content_type = exc.headers.get_content_type() if exc.headers else None
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError:
            payload = {"raw": raw}
        return ApiResult(
            endpoint=url,
            method=method,
            status=exc.code,
            ok=False,
            payload=payload,
            content_type=content_type,
            error=f"HTTP {exc.code}",
        )
    except urllib.error.URLError as exc:
        return ApiResult(
            endpoint=url,
            method=method,
            status=None,
            ok=False,
            payload=None,
            error=str(exc.reason),
        )


def print_result(title: str, result: ApiResult) -> None:
    status = result.status if result.status is not None else "n/a"
    state = "ok" if result.ok else "error"
    print(f"\n== {title} ==")
    print(f"{result.method} {result.endpoint}")
    print(f"status: {status} ({state})")
    if result.content_type:
        print(f"content-type: {result.content_type}")
    if result.error:
        print(f"error: {result.error}")
    if result.payload is not None:
        if isinstance(result.payload, dict) and "raw" in result.payload and len(result.payload) == 1:
            raw = str(result.payload["raw"])
            preview = raw[:240].replace("\n", " ").replace("\r", " ")
            print(preview)
        else:
            print(json.dumps(result.payload, indent=2, ensure_ascii=True))


def load_dotenv_if_exists(dotenv_path: str = ".env") -> None:
    if not os.path.exists(dotenv_path):
        return

    with open(dotenv_path, "r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue

            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key and key not in os.environ:
                os.environ[key] = value


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="RadiusDesk API probe")
    parser.add_argument(
        "--base-url",
        default=os.getenv("RADIUSDESK_BASE_URL", "http://192.168.10.90"),
        help="RadiusDesk base URL, for example http://192.168.10.90",
    )
    parser.add_argument(
        "--token",
        default=os.getenv("RADIUSDESK_API_TOKEN", ""),
        help="API token for the access provider",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("map", help="Probe the documented GET endpoints")
    subparsers.add_parser("realms", help="List realms available to the token")
    subparsers.add_parser("profiles", help="List profiles available to the token")
    subparsers.add_parser("discover", help="Probe a curated set of likely read-only endpoints")
    export = subparsers.add_parser("export", help="Export realms, permanent users, and devices")
    export.add_argument(
        "--format",
        choices=["csv", "json"],
        default="csv",
        help="Export format for each dataset",
    )
    export.add_argument(
        "--outdir",
        default="radiusdesk-export",
        help="Directory where exported files will be written",
    )
    export.add_argument(
        "--entities",
        nargs="*",
        default=["realms", "permanent-users", "devices"],
        choices=list(EXPORT_SPECS.keys()),
        help="Entities to export",
    )

    query = subparsers.add_parser("query", help="Query any RadiusDesk endpoint path")
    query.add_argument("path", help="Endpoint path, for example /cake3/rd_cake/clients/index.json")
    query.add_argument("--method", default="GET", choices=["GET", "POST"], help="HTTP method")

    add_user = subparsers.add_parser("add-user", help="Show or submit a permanent-user payload")
    add_user.add_argument("--username", required=True)
    add_user.add_argument("--password", required=True)
    add_user.add_argument("--realm", required=True)
    add_user.add_argument("--profile", required=True)
    add_user.add_argument("--user-id", type=int, default=0)
    add_user.add_argument("--submit", action="store_true", help="Actually send the POST request")

    return parser.parse_args()


def summarize_payload(result: ApiResult) -> None:
    if not result.ok:
        print_result("request failed", result)
        return

    payload = result.payload or {}
    items = payload.get("items") if isinstance(payload, dict) else None
    if isinstance(items, list):
        print(f"items: {len(items)}")
        for item in items[:10]:
            if isinstance(item, dict):
                identifier = item.get("id", "?")
                name = item.get("name", item.get("username", ""))
                print(f"- {identifier}: {name}")
    else:
        print(json.dumps(payload, indent=2, ensure_ascii=True))


def fetch_with_token(base_url: str, path: str, token: str, method: str = "GET") -> ApiResult:
    query = {"token": token} if method == "GET" else None
    return request_json(build_url(base_url, path, query), method=method)


def fetch_with_query(base_url: str, path: str, query: dict[str, str], method: str = "GET") -> ApiResult:
    return request_json(build_url(base_url, path, query), method=method)


def summarize_shape(result: ApiResult) -> None:
    if not result.ok:
        print_result("request failed", result)
        return

    payload = result.payload
    if isinstance(payload, dict):
        keys = sorted(payload.keys())
        print(f"keys: {', '.join(keys)}")
        items = payload.get("items")
        if isinstance(items, list):
            print(f"items: {len(items)}")
    else:
        print(type(payload).__name__)


def stringify_value(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, str):
        return value
    return json.dumps(value, ensure_ascii=True)


def flatten_item(item: dict[str, Any]) -> dict[str, str]:
    row: dict[str, str] = {}
    for key, value in item.items():
        if isinstance(value, dict):
            for nested_key, nested_value in value.items():
                row[f"{key}.{nested_key}"] = stringify_value(nested_value)
        elif isinstance(value, list):
            row[key] = json.dumps(value, ensure_ascii=True)
        else:
            row[key] = stringify_value(value)
    return row


def write_csv_file(file_path: Path, items: list[dict[str, Any]]) -> None:
    rows = [flatten_item(item) for item in items]
    fieldnames = sorted({field for row in rows for field in row.keys()})
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with file_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_json_file(file_path: Path, payload: Any) -> None:
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with file_path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, ensure_ascii=True)
        handle.write("\n")


def export_entities(base_url: str, token: str, outdir: str, fmt: str, entities: list[str]) -> None:
    export_dir = Path(outdir)
    export_dir.mkdir(parents=True, exist_ok=True)

    for entity in entities:
        spec = EXPORT_SPECS[entity]
        first_query = {
            "token": token,
            "page": "1",
            "start": "0",
            "limit": str(DEFAULT_EXPORT_LIMIT),
        }
        result = fetch_with_query(base_url, spec["endpoint"], first_query)
        if not result.ok:
            print_result(f"export {entity}", result)
            continue

        payload = result.payload if isinstance(result.payload, dict) else {}
        items = payload.get("items") if isinstance(payload, dict) else None
        if not isinstance(items, list):
            print(f"{entity}: endpoint did not return an items list")
            continue

        total_count = payload.get("totalCount") if isinstance(payload, dict) else None
        if not isinstance(total_count, int):
            total_count = len(items)

        collected_items: list[dict[str, Any]] = [item for item in items if isinstance(item, dict)]
        offset = len(collected_items)
        page = 2
        while offset < total_count:
            page_query = {
                "token": token,
                "page": str(page),
                "start": str(offset),
                "limit": str(DEFAULT_EXPORT_LIMIT),
            }
            page_result = fetch_with_query(base_url, spec["endpoint"], page_query)
            if not page_result.ok:
                print_result(f"export {entity} page {page}", page_result)
                break

            page_payload = page_result.payload if isinstance(page_result.payload, dict) else {}
            page_items = page_payload.get("items") if isinstance(page_payload, dict) else None
            if not isinstance(page_items, list) or not page_items:
                break

            page_dict_items = [item for item in page_items if isinstance(item, dict)]
            collected_items.extend(page_dict_items)
            offset += len(page_dict_items)
            page += 1

        file_path = export_dir / f"{spec['filename']}.{fmt}"
        if fmt == "csv":
            write_csv_file(file_path, collected_items)
        else:
            write_json_file(file_path, {"items": collected_items, "totalCount": total_count, "success": True})
        print(f"exported {entity} -> {file_path}")


def main() -> int:
    load_dotenv_if_exists()
    args = parse_args()
    token = args.token.strip()
    if not token:
        print("Missing API token. Use --token or set RADIUSDESK_API_TOKEN.", file=sys.stderr)
        return 2

    base_url = args.base_url.rstrip("/")

    if args.command == "map":
        realms_url = build_url(base_url, "/cake3/rd_cake/realms/index-ap-create.json", {"token": token})
        profiles_url = build_url(base_url, "/cake3/rd_cake/profiles/index-ap.json", {"token": token})

        print_result("realms", request_json(realms_url))
        print_result("profiles", request_json(profiles_url))
        print("\nPOST /cake3/rd_cake/permanent-users/add.json")
        print("minimum payload:")
        print(
            json.dumps(
                {
                    "user_id": 0,
                    "username": "demo2",
                    "password": "demopassword",
                    "realm": "demo1",
                    "profile": "demo1",
                    "token": token,
                },
                indent=2,
                ensure_ascii=True,
            )
        )
        return 0

    if args.command == "realms":
        url = build_url(base_url, "/cake3/rd_cake/realms/index-ap-create.json", {"token": token})
        summarize_payload(request_json(url))
        return 0

    if args.command == "profiles":
        summarize_payload(fetch_with_token(base_url, "/cake3/rd_cake/profiles/index-ap.json", token))
        return 0

    if args.command == "discover":
        for label, path, use_token in KNOWN_QUERY_ENDPOINTS:
            result = fetch_with_token(base_url, path, token) if use_token else request_json(build_url(base_url, path))
            print(f"\n== {label} ==")
            print(f"{result.method} {result.endpoint}")
            print(f"status: {result.status if result.status is not None else 'n/a'} ({'ok' if result.ok else 'error'})")
            if result.ok:
                summarize_shape(result)
            else:
                print(f"error: {result.error}")
        return 0

    if args.command == "export":
        export_entities(base_url, token, args.outdir, args.format, args.entities)
        return 0

    if args.command == "query":
        path = args.path if args.path.startswith("/") else f"/{args.path}"
        result = fetch_with_token(base_url, path, token, method=args.method)
        print_result("query", result)
        return 0

    if args.command == "add-user":
        payload = {
            "user_id": args.user_id,
            "username": args.username,
            "password": args.password,
            "realm": args.realm,
            "profile": args.profile,
            "token": token,
        }
        url = build_url(base_url, "/cake3/rd_cake/permanent-users/add.json")
        if not args.submit:
            print("Dry run payload:")
            print(json.dumps(payload, indent=2, ensure_ascii=True))
            print("Use --submit to POST this payload.")
            return 0
        print_result("add-user", request_json(url, method="POST", data=payload))
        return 0

    print(f"Unknown command: {args.command}", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())