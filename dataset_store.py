"""Load the public NovaMart datasets into isolated SQLite tables."""

import csv
import hashlib
import json
import re
import sqlite3
from contextlib import closing
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "datasets" / "public"
DB_PATH = ROOT / "novamart.db"
_IDENTIFIER = re.compile(r"^[a-z_][a-z0-9_]*$")
_SPEC_HEADING = re.compile(r"^##\s+(.+?)\s+\((PROD-[^)]+)\)\s*$", re.MULTILINE)

_CSV_DATASETS = (
    ("customers", "Customers", "Customer profiles, loyalty, account and contact fields.", "Not bundled for privacy."),
    ("products", "Products", "SKU, category, pricing, availability and warranty details.", "Not bundled."),
    ("orders", "Orders", "Order identifiers, customer, payment, delivery and status.", "Not bundled for privacy."),
    ("order_items", "Order Items", "Product line items, quantities, prices and return status.", "Not bundled."),
    ("support_tickets", "Support Tickets", "Ticket category, priority, status and resolution.", "Not bundled for privacy."),
    ("reviews", "Reviews", "Product ratings, review text and verified-purchase flag.", "Not bundled."),
)

_DESCRIPTIONS = {
    "conversations": "Prior customer and agent chat histories.",
    "policies": "Versioned refund, return, shipping and support policy documents.",
    "product_specifications": "Per-product technical attributes extracted from category guides.",
}


def _quote_identifier(identifier: str) -> str:
    if not _IDENTIFIER.fullmatch(identifier):
        raise ValueError(f"Unsafe SQLite identifier: {identifier!r}")
    return f'"{identifier}"'


def _load_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open("r", encoding="utf-8-sig", newline="") as source:
        reader = csv.DictReader(source)
        if not reader.fieldnames:
            raise ValueError(f"{path.name} is missing a CSV header.")
        columns = [column.strip() for column in reader.fieldnames]
        if any(not _IDENTIFIER.fullmatch(column) for column in columns):
            raise ValueError(f"{path.name} contains an invalid column name.")
        records = []
        for line_number, row in enumerate(reader, start=2):
            if None in row:
                raise ValueError(f"{path.name} has too many fields on line {line_number}.")
            records.append({column: row.get(original) or "" for column, original in zip(columns, reader.fieldnames)})
    return columns, records


def _load_conversations(path: Path) -> tuple[list[str], list[dict[str, Any]]]:
    with path.open("r", encoding="utf-8") as source:
        payload = json.load(source)
    if not isinstance(payload, list) or any(not isinstance(row, dict) for row in payload):
        raise ValueError("conversations.json must contain a list of conversation objects.")
    columns = ["conversation_id", "customer_id", "order_id", "ticket_id", "channel", "language",
               "started_at", "status", "handled_by", "messages"]
    records = []
    for row in payload:
        records.append({
            column: json.dumps(row[column], ensure_ascii=False) if column == "messages"
            else ("" if row.get(column) is None else str(row.get(column, "")))
            for column in columns
        })
    return columns, records


def _load_policy_documents() -> tuple[list[str], list[dict[str, str]]]:
    records = []
    for path in sorted((DATA_DIR / "policies").glob("*.md")):
        version_match = re.search(r"_v(\d+(?:\.\d+)?)$", path.stem)
        records.append({
            "policy_id": path.stem,
            "document_name": path.name,
            "version": f"v{version_match.group(1)}" if version_match else "versioned",
            "content": path.read_text(encoding="utf-8"),
        })
    if not records:
        raise ValueError("No public policy documents were found.")
    return ["policy_id", "document_name", "version", "content"], records


def _load_product_specifications() -> tuple[list[str], list[dict[str, str]]]:
    records = []
    for path in sorted((DATA_DIR / "product_specifications").glob("*.md")):
        content = path.read_text(encoding="utf-8")
        headings = list(_SPEC_HEADING.finditer(content))
        for index, heading in enumerate(headings):
            end = headings[index + 1].start() if index + 1 < len(headings) else len(content)
            section = content[heading.start():end].strip()
            sku_match = re.search(r"\*\*SKU:\*\*\s*([^|\r\n]+)", section)
            records.append({
                "product_id": heading.group(2),
                "product_name": heading.group(1).strip(),
                "category": path.stem,
                "sku": sku_match.group(1).strip() if sku_match else "",
                "specification_text": section,
            })
    if not records:
        raise ValueError("No product specification records were found.")
    if len({record["product_id"] for record in records}) != len(records):
        raise ValueError("Product specification files contain duplicate product IDs.")
    return ["product_id", "product_name", "category", "sku", "specification_text"], records


def _source_fingerprint(paths: list[Path]) -> str:
    details = [
        f"{path.relative_to(DATA_DIR).as_posix()}:{path.stat().st_size}:{path.stat().st_mtime_ns}"
        for path in sorted(paths)
    ]
    return hashlib.sha256("\n".join(details).encode("utf-8")).hexdigest()


def import_public_datasets() -> list[dict[str, Any]]:
    """Idempotently import only files in the public dataset folder."""
    csv_paths = [DATA_DIR / f"{key}.csv" for key, _, _, _ in _CSV_DATASETS]
    conversation_path = DATA_DIR / "conversations.json"
    policy_paths = sorted((DATA_DIR / "policies").glob("*.md"))
    specification_paths = sorted((DATA_DIR / "product_specifications").glob("*.md"))
    paths = [path for path in csv_paths + [conversation_path] if path.is_file()]
    paths += policy_paths + specification_paths
    if not policy_paths:
        raise FileNotFoundError(f"No public policy documents found in {DATA_DIR / 'policies'}.")
    if not specification_paths:
        raise FileNotFoundError(
            f"No public product specifications found in {DATA_DIR / 'product_specifications'}."
        )

    fingerprint = _source_fingerprint(paths)
    with closing(sqlite3.connect(DB_PATH)) as conn:
        conn.row_factory = sqlite3.Row
        conn.execute("""
            CREATE TABLE IF NOT EXISTS public_dataset_registry (
                dataset_key TEXT PRIMARY KEY,
                display_name TEXT NOT NULL,
                table_name TEXT NOT NULL,
                record_count INTEGER,
                description TEXT NOT NULL,
                status TEXT NOT NULL
            )
        """)
        registry_columns = {
            row["name"] for row in conn.execute("PRAGMA table_info(public_dataset_registry)")
        }
        if "status" not in registry_columns:
            conn.execute(
                "ALTER TABLE public_dataset_registry ADD COLUMN status TEXT NOT NULL DEFAULT 'loaded'"
            )
        conn.execute("""
            CREATE TABLE IF NOT EXISTS public_dataset_state (
                state_key TEXT PRIMARY KEY,
                state_value TEXT NOT NULL
            )
        """)
        cached = conn.execute(
            "SELECT state_value FROM public_dataset_state WHERE state_key = 'source_fingerprint'"
        ).fetchone()
        if cached and cached[0] == fingerprint:
            return [
                dict(row) for row in conn.execute(
                    "SELECT dataset_key, display_name, table_name, record_count, description, status "
                    "FROM public_dataset_registry ORDER BY rowid"
                ).fetchall()
            ]

        datasets = []
        for key, title, description, missing_status in _CSV_DATASETS:
            path = DATA_DIR / f"{key}.csv"
            if path.is_file():
                columns, records = _load_csv(path)
                status = "loaded"
            else:
                columns, records, status = [], [], missing_status
            datasets.append((key, title, f"public_{key}", description, status, columns, records))

        if conversation_path.is_file():
            columns, records = _load_conversations(conversation_path)
            status = "loaded"
        else:
            columns, records, status = [], [], "Not bundled for privacy."
        datasets.append(("conversations", "Conversations", "public_conversations",
                         _DESCRIPTIONS["conversations"], status, columns, records))
        columns, records = _load_policy_documents()
        datasets.append(("policies", "Policies", "public_policies",
                         _DESCRIPTIONS["policies"], "loaded", columns, records))
        columns, records = _load_product_specifications()
        datasets.append(("product_specifications", "Product Specifications",
                         "public_product_specifications",
                         _DESCRIPTIONS["product_specifications"], "loaded", columns, records))

        with conn:
            for key, title, table, description, status, columns, records in datasets:
                quoted_table = _quote_identifier(table)
                if status != "loaded":
                    conn.execute(f"DROP TABLE IF EXISTS {quoted_table}")
                    continue
                quoted_columns = ", ".join(_quote_identifier(column) for column in columns)
                conn.execute(f"DROP TABLE IF EXISTS {quoted_table}")
                conn.execute(
                    f"CREATE TABLE {quoted_table} ({', '.join(f'{_quote_identifier(column)} TEXT' for column in columns)})"
                )
                if records:
                    placeholders = ", ".join("?" for _ in columns)
                    conn.executemany(
                        f"INSERT INTO {quoted_table} ({quoted_columns}) VALUES ({placeholders})",
                        [[record.get(column, "") for column in columns] for record in records],
                    )
            conn.execute("DELETE FROM public_dataset_registry")
            conn.executemany(
                "INSERT INTO public_dataset_registry "
                "(dataset_key, display_name, table_name, record_count, description, status) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                [(key, title, table, len(records) if status == "loaded" else None, description, status)
                 for key, title, table, description, status, _, records in datasets],
            )
            conn.execute(
                "INSERT INTO public_dataset_state (state_key, state_value) "
                "VALUES ('source_fingerprint', ?) "
                "ON CONFLICT(state_key) DO UPDATE SET state_value = excluded.state_value",
                (fingerprint,),
            )

        return [
            dict(row) for row in conn.execute(
                "SELECT dataset_key, display_name, table_name, record_count, description, status "
                "FROM public_dataset_registry ORDER BY rowid"
            ).fetchall()
        ]
