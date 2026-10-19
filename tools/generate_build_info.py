"""Record build versions without including environment variables or package URLs."""

import argparse
from importlib import metadata
import json
from pathlib import Path
import platform
import shutil
import subprocess
import sys


ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.app_metadata import APP_VERSION


def build_info() -> dict:
    revision = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=ROOT_DIR, capture_output=True, text=True, check=False,
    ) if (ROOT_DIR / ".git").exists() and shutil.which("git") else None
    packages = {
        dist.metadata["Name"]: dist.version
        for dist in metadata.distributions()
        if dist.metadata["Name"]
    }
    return {
        "app_version": APP_VERSION,
        "source_commit": revision.stdout.strip() if revision is not None and revision.returncode == 0 else None,
        "python": platform.python_version(),
        "platform": platform.platform(),
        "packages": dict(sorted(packages.items(), key=lambda item: item[0].lower())),
    }


def main():
    parser = argparse.ArgumentParser(description="Record package versions used for the Windows build.")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(build_info(), indent=2, ensure_ascii=True) + "\n", encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()
