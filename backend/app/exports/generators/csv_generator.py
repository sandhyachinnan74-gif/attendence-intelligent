import csv
import io
from typing import List, Dict, Any

def generate_csv_bytes(rows: List[Dict[str, Any]], columns: List[Dict[str, str]]) -> bytes:
    output = io.StringIO()
    # Write header
    writer = csv.writer(output, lineterminator="\n")
    headers = [col["label"] for col in columns]
    writer.writerow(headers)

    col_ids = [col["id"] for col in columns]
    for row in rows:
        row_vals = [row.get(cid, "-") for cid in col_ids]
        writer.writerow(row_vals)

    # Encode with utf-8-sig for Excel compatibility
    return output.getvalue().encode("utf-8-sig")
