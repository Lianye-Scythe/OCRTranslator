from __future__ import annotations

import argparse
import hashlib
from pathlib import Path


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate SHA256SUMS.txt style output for one or more files.")
    parser.add_argument("files", nargs="+", help="Files to hash")
    parser.add_argument("--output", required=True, help="Output checksum file path")
    args = parser.parse_args()

    file_paths = [Path(file_path).resolve() for file_path in args.files]
    output_path = Path(args.output).resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    lines = [f"{sha256_file(path)} *{path.name}" for path in file_paths]
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    print(f"Wrote {output_path}")


if __name__ == "__main__":
    main()
