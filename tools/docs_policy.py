"""Classify CI scope and validate documentation; image checks require Pillow."""

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
PREVIEW_TOOL_PATHS = {"tools/generate_social_preview.py", "tests/test_social_preview.py"}


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


def _only_paths(files: list[dict], expected_count: int, allowed_path) -> bool:
    return bool(files) and len(files) == expected_count and all(
        file.get("status") in {"added", "modified", "removed", "renamed"}
        and allowed_path(file.get("filename", ""))
        and (file.get("status") != "renamed" or allowed_path(file.get("previous_filename", "")))
        for file in files
    )


def docs_only(files: list[dict], expected_count: int) -> bool:
    return _only_paths(files, expected_count, is_docs_path)


def classify_scope(files: list[dict], expected_count: int) -> str:
    if docs_only(files, expected_count):
        return "docs"
    if _only_paths(files, expected_count, lambda name: is_docs_path(name) or name in PREVIEW_TOOL_PATHS):
        return "preview"
    return "full"


def needs_preview_checks(files: list[dict], scope: str) -> bool:
    return scope == "preview" or (scope == "docs" and any(
        file.get("filename", "").startswith("docs/images/")
        or file.get("previous_filename", "").startswith("docs/images/")
        for file in files
    ))


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


def check_images(root: Path) -> list[str]:
    from PIL import Image

    root = root.resolve()
    errors = []
    for file in (root / "docs/images").rglob("*"):
        if file.suffix.lower() not in IMAGE_SUFFIXES or not file.is_file():
            continue
        filename = file.relative_to(root).as_posix()
        if file.is_symlink() or not file.resolve().is_relative_to(root):
            errors.append(f"{filename}: image must be a regular repository file")
            continue
        try:
            with Image.open(file) as image:
                if filename == "docs/images/social-preview.png" and image.size != (1280, 640):
                    errors.append(f"{filename}: expected 1280x640, got {image.width}x{image.height}")
                image.verify()
        except (OSError, ValueError, SyntaxError, Image.DecompressionBombError) as exc:
            errors.append(f"{filename}: invalid image ({type(exc).__name__})")
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
        expected_count = args.expected_count
    elif args.base and set(args.base) != {"0"}:
        result = subprocess.run(
            ["git", "diff", "--name-only", "--no-renames", "-z", args.base, "HEAD", "--"],
            cwd=ROOT, check=True, capture_output=True,
        )
        files = [{"filename": name, "status": "modified"} for name in result.stdout.decode("utf-8").split("\0") if name]
        expected_count = len(files)
    else:
        files, expected_count = [], 0
    scope = classify_scope(files, expected_count)
    preview_checks = needs_preview_checks(files, scope)
    if args.check:
        if scope == "full":
            raise SystemExit("Lightweight validation requires a nonempty, complete documentation or preview-tool diff.")
        # Check unchanged pages too, so deleting a referenced image cannot pass.
        filenames = ["README.md", "CHANGELOG.md"] + [
            str(file.relative_to(ROOT))
            for directory in ("docs", ".github")
            for file in (ROOT / directory).rglob("*.md")
        ]
        errors = check_links(ROOT, filenames)
        if preview_checks:
            errors.extend(check_images(ROOT))
        if errors:
            raise SystemExit("\n".join(errors))
        print("Documentation links and image paths passed." + (" Image integrity and dimensions passed." if preview_checks else ""))
    if output := os.environ.get("GITHUB_OUTPUT"):
        with Path(output).open("a", encoding="utf-8") as stream:
            stream.write(f"docs_only={str(scope == 'docs').lower()}\n")
            stream.write(f"scope={scope}\npreview_checks={str(preview_checks).lower()}\n")
    print({"docs": "Documentation-only changes.", "preview": "Preview-tool changes: lightweight CI / manual review required.", "full": "Full CI / manual review required."}[scope])


if __name__ == "__main__":
    main()
