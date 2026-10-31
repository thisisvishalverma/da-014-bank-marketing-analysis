"""Download and extract the official UCI Bank Marketing dataset file."""

from __future__ import annotations

import io
import urllib.request
import zipfile
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_DIR / "data"
CSV_NAME = "bank-additional-full.csv"
ARCHIVE_URL = "https://archive.ics.uci.edu/static/public/222/bank+marketing.zip"


def main() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    target = DATA_DIR / CSV_NAME
    if target.exists() and target.stat().st_size > 0:
        print(f"Dataset already exists: {target}")
        return

    request = urllib.request.Request(
        ARCHIVE_URL,
        headers={"User-Agent": "DA-014-bank-marketing-prototype/1.0"},
    )
    print("Downloading the official UCI archive…")
    with urllib.request.urlopen(request, timeout=60) as response:
        archive_bytes = response.read()

    with zipfile.ZipFile(io.BytesIO(archive_bytes)) as outer:
        nested_name = next((name for name in outer.namelist() if name.endswith("bank-additional.zip")), None)
        if nested_name is None:
            raise RuntimeError("The outer UCI archive did not contain bank-additional.zip.")
        with zipfile.ZipFile(io.BytesIO(outer.read(nested_name))) as nested:
            csv_member = next((name for name in nested.namelist() if name.endswith(CSV_NAME)), None)
            if csv_member is None:
                raise RuntimeError(f"The nested archive did not contain {CSV_NAME}.")
            target.write_bytes(nested.read(csv_member))

    print(f"Saved {target} ({target.stat().st_size:,} bytes).")


if __name__ == "__main__":
    main()
