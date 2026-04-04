from __future__ import annotations

import argparse
from pathlib import Path
import sys


ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.app_metadata import (
    APP_NAME,
    APP_VERSION,
    AUTHOR_NAME_EN,
    WINDOWS_COMPANY_NAME,
    WINDOWS_FILE_DESCRIPTION,
    WINDOWS_INTERNAL_NAME,
    WINDOWS_LEGAL_COPYRIGHT,
    WINDOWS_ORIGINAL_FILENAME,
    WINDOWS_PRODUCT_NAME,
)


def version_tuple(version: str) -> tuple[int, int, int, int]:
    parts = [int(part) for part in str(version or "0").strip().split(".") if part.strip()]
    while len(parts) < 4:
        parts.append(0)
    return tuple(parts[:4])


def build_version_resource_text() -> str:
    file_version_tuple = version_tuple(APP_VERSION)
    product_version_tuple = file_version_tuple
    return f"""# UTF-8
VSVersionInfo(
  ffi=FixedFileInfo(
    filevers={file_version_tuple},
    prodvers={product_version_tuple},
    mask=0x3f,
    flags=0x0,
    OS=0x40004,
    fileType=0x1,
    subtype=0x0,
    date=(0, 0)
  ),
  kids=[
    StringFileInfo([
      StringTable(
        '040904B0',
        [
          StringStruct('CompanyName', {WINDOWS_COMPANY_NAME!r}),
          StringStruct('FileDescription', {WINDOWS_FILE_DESCRIPTION!r}),
          StringStruct('FileVersion', {APP_VERSION!r}),
          StringStruct('InternalName', {WINDOWS_INTERNAL_NAME!r}),
          StringStruct('OriginalFilename', {WINDOWS_ORIGINAL_FILENAME!r}),
          StringStruct('ProductName', {WINDOWS_PRODUCT_NAME!r}),
          StringStruct('ProductVersion', {APP_VERSION!r}),
          StringStruct('LegalCopyright', {WINDOWS_LEGAL_COPYRIGHT!r}),
          StringStruct('Comments', {f'{APP_NAME} by {AUTHOR_NAME_EN}'!r}),
        ]
      )
    ]),
    VarFileInfo([
      VarStruct('Translation', [1033, 1200])
    ])
  ]
)
"""


def write_version_resource(output_path: str | Path) -> Path:
    target_path = Path(output_path)
    target_path.parent.mkdir(parents=True, exist_ok=True)
    target_path.write_text(build_version_resource_text(), encoding="utf-8")
    return target_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate a PyInstaller Windows version resource file.")
    parser.add_argument("--output", required=True, help="Output path for the generated version info file")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    write_version_resource(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
