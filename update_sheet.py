import csv
import os
import base64
import datetime
import pathlib

import snowflake.connector
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend

CSV_PATH = pathlib.Path(__file__).parent / "CBC_ITEM_LIST.csv"
RESULTS_DIR = pathlib.Path(__file__).parent / "results"

QUERY_TEMPLATE = """
WITH rrc_list AS (
    SELECT column1 AS retailer_sku, column2 AS description
    FROM VALUES {values_clause}
),

pfnd_latest AS (
    SELECT
        pfnd.data:retailer_reference_code::string AS retailer_sku,
        pfnd.inventory_area_id::string            AS inventory_area_id,
        pfnd.created_at                           AS last_seen_at
    FROM catalog.catalog.partner_file_normalized_data pfnd
    WHERE pfnd.partner_id = 27
      AND pfnd.retailer_id = 195
      AND pfnd.created_at > CURRENT_TIMESTAMP - INTERVAL '7 day'
      AND pfnd.data:retailer_reference_code::string IN (
          SELECT retailer_sku FROM rrc_list
      )
    QUALIFY ROW_NUMBER() OVER (
        PARTITION BY pfnd.data:retailer_reference_code::string,
                     pfnd.inventory_area_id
        ORDER BY pfnd.created_at DESC
    ) = 1
),

pfnd_summary AS (
    SELECT
        retailer_sku,
        COUNT(DISTINCT inventory_area_id) AS locations_reporting,
        MAX(last_seen_at)                 AS data_last_seen
    FROM pfnd_latest
    GROUP BY 1
)

SELECT
    l.retailer_sku,
    l.description,

    CASE
        WHEN p.retailer_sku IS NULL
            THEN 'Not received in last 7 days'
        ELSE 'Received in last 7 days'
    END AS feed_status,

    COALESCE(
        TO_VARCHAR(p.data_last_seen),
        'No recent data received'
    ) AS last_seen_in_feed

FROM rrc_list l
LEFT JOIN pfnd_summary p
    ON l.retailer_sku = p.retailer_sku
ORDER BY
    feed_status DESC,
    retailer_sku
"""


def load_private_key() -> bytes:
    """Load Snowflake RSA private key from base64-encoded env var or file path."""
    key_b64 = os.environ.get("SNOWFLAKE_PRIVATE_KEY_B64")
    key_path = os.environ.get("SNOWFLAKE_PRIVATE_KEY_PATH")
    passphrase = os.environ.get("SNOWFLAKE_PRIVATE_KEY_PASSPHRASE")

    if key_b64:
        pem_bytes = base64.b64decode(key_b64)
    elif key_path:
        with open(key_path, "rb") as f:
            pem_bytes = f.read()
    else:
        raise RuntimeError(
            "Set SNOWFLAKE_PRIVATE_KEY_B64 or SNOWFLAKE_PRIVATE_KEY_PATH"
        )

    p_key = serialization.load_pem_private_key(
        pem_bytes,
        password=passphrase.encode() if passphrase else None,
        backend=default_backend(),
    )

    return p_key.private_bytes(
        encoding=serialization.Encoding.DER,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )


def build_values_clause() -> str:
    """Read CBC_ITEM_LIST.csv and build a SQL VALUES clause."""
    rows = []
    with open(CSV_PATH, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            sku = row["ITEM_NUMBER"].replace("'", "''")
            desc = row["DESCRIPTION"].replace("'", "''")
            rows.append(f"('{sku}', '{desc}')")
    return ",\n    ".join(rows)


def run_snowflake_query() -> tuple[list[str], list[list[str]]]:
    """Connect to Snowflake, run the query, return (headers, rows)."""
    private_key = load_private_key()

    conn = snowflake.connector.connect(
        account=os.environ.get("SNOWFLAKE_ACCOUNT", "instacart-instacart"),
        user=os.environ["SNOWFLAKE_USER"],
        private_key=private_key,
        warehouse=os.environ.get("SNOWFLAKE_WAREHOUSE", "developer_wh"),
        database=os.environ.get("SNOWFLAKE_DATABASE", "instadata"),
        schema=os.environ.get("SNOWFLAKE_SCHEMA", "dwh"),
        role=os.environ.get("SNOWFLAKE_ROLE", "instacart_developer_role"),
        timeout=60,
    )

    query = QUERY_TEMPLATE.format(values_clause=build_values_clause())

    try:
        cur = conn.cursor()
        cur.execute(query)
        headers = [desc[0] for desc in cur.description]
        rows = [[str(val) if val is not None else "" for val in row] for row in cur.fetchall()]
        return headers, rows
    finally:
        conn.close()


def save_results(headers: list[str], rows: list[list[str]]) -> pathlib.Path:
    """Save query results to results/latest.csv and results/YYYY-MM-DD.csv."""
    RESULTS_DIR.mkdir(exist_ok=True)
    date_str = datetime.date.today().strftime("%Y-%m-%d")

    for filename in ["latest.csv", f"{date_str}.csv"]:
        filepath = RESULTS_DIR / filename
        with open(filepath, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(headers)
            writer.writerows(rows)

    print(f"Saved results/{date_str}.csv and results/latest.csv ({len(rows)} rows)")
    return RESULTS_DIR / f"{date_str}.csv"


def main():
    print("Running Snowflake query...")
    headers, rows = run_snowflake_query()
    print(f"Got {len(rows)} rows.")

    print("Saving results...")
    save_results(headers, rows)
    print("Done!")


if __name__ == "__main__":
    main()
