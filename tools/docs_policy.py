"""Classify documentation changes and check their local links without dependencies."""

import argparse
from html.parser import HTMLParser
import json
import os
from pathlib import Path, PurePosixPath
import re
import subprocess
from urllib.parse import unquote, urlsplit


ROOT = Path(__file__).resolve().parent.parent
IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".gif", ".webp"}


def is_docs_path(filename: str) -> bool:
    path = PurePosixPath(filename)
    if path.is_absolute() or ".." in path.parts or "\\" in filename:
        return False
    return (
        filename in {"README.md", "CHANGELOG.md"}
        or (path.parent == PurePosixPath(".github") and path.suffix == ".md")
        or (filename.startswith("docs/") and path.suffix == ".md")
        or (filename.startswith("docs/images/") and path.suffix in IMAGE_SUFFIXES)
    )


def docs_only(files: list[dict], expected_count: int) -> bool:
    return bool(files) and len(files) == expected_count and all(
        file.get("status") in {"added", "modified", "removed", "renamed"}
        and is_docs_path(file.get("filename", ""))
        and (file.get("status") != "renamed" or is_docs_path(file.get("previous_filename", "")))
        for file in files
    )


class LinkParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []

    def handle_starttag(self, tag, attrs):
        for name, value in attrs:
            if value and ((tag == "img" and name == "src") or (tag == "a" and name == "href")):
                self.links.append(value)


def check_links(root: Path, filenames: list[str]) -> list[str]:
    errors = []
    root = root.resolve()
    for filename in filenames:
        file = root / filename
        if file.suffix != ".md" or not file.exists():
            continue
        if file.is_symlink() or not file.resolve().is_relative_to(root):
            errors.append(f"{filename}: documentation must be a regular repository file")
            continue
        # Ignore fenced examples; check inline links, reference definitions, and HTML assets.
        text = re.sub(r"^(`{3,}|~{3,}).*?^\1[^\n]*$", "", file.read_text(encoding="utf-8"), flags=re.M | re.S)
        parser = LinkParser()
        parser.feed(text)
        links = re.findall(r"\[[^\]\n]*\]\(<?([^\s)>]+)>?(?:\s+[^)]*)?\)", text)
        links += re.findall(r"^\s*\[[^\]]+\]:\s*<?([^\s>]+)", text, flags=re.M)
        for target in links + parser.links:
            url = urlsplit(target)
            if url.scheme or url.netloc or not url.path:
                continue
            path = (file.parent / unquote(url.path)).resolve()
            if not path.is_relative_to(root) or not path.exists():
                errors.append(f"{filename}: missing or outside-repository target: {target}")
    return errors


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--base")
    parser.add_argument("--pr-files", type=Path)
    parser.add_argument("--expected-count", type=int)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if args.pr_files:
        pages = json.loads(args.pr_files.read_text(encoding="utf-8"))
        files = [file for page in pages for file in page]
        eligible = docs_only(files, args.expected_count)
    elif args.base and set(args.base) != {"0"}:
        result = subprocess.run(
            ["git", "diff", "--name-only", "--no-renames", "-z", args.base, "HEAD", "--"],
            cwd=ROOT, check=True, capture_output=True,
        )
        files = [{"filename": name, "status": "modified"} for name in result.stdout.decode("utf-8").split("\0") if name]
        eligible = docs_only(files, len(files))
    else:
        files, eligible = [], False
    if args.check:
        if not eligible:
            raise SystemExit("Documentation-only validation requires a nonempty, complete documentation diff.")
        # Check unchanged pages too, so deleting a referenced image cannot pass.
        filenames = ["README.md", "CHANGELOG.md"] + [
            str(file.relative_to(ROOT))
            for directory in ("docs", ".github")
            for file in (ROOT / directory).rglob("*.md")
        ]
        errors = check_links(ROOT, filenames)
        if errors:
            raise SystemExit("\n".join(errors))
        print("Documentation local links and image paths passed.")
    if output := os.environ.get("GITHUB_OUTPUT"):
        with Path(output).open("a", encoding="utf-8") as stream:
            stream.write(f"docs_only={str(eligible).lower()}\n")
    print("Documentation-only changes." if eligible else "Full CI / manual review required.")


if __name__ == "__main__":
    main()
