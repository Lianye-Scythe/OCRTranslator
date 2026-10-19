"""Validate dependency metadata and diff data without executing PR code."""

import json
import os
from pathlib import Path
import re
import sys


ALLOWED_PACKAGES = {"pillow", "requests", "pynput"}
REQUIREMENT = re.compile(r"([A-Za-z][A-Za-z0-9_-]*)>=(\d+)\.(\d+)\.(\d+)")
CONSTRAINT = re.compile(r"([A-Za-z][A-Za-z0-9_-]*)==(\d+)\.(\d+)\.(\d+)")


def eligible_patch(metadata: dict, files: list[dict]) -> bool:
    names = {name.strip().lower() for name in metadata.get("names", "").split(",") if name.strip()}
    if (
        not names
        or not names <= ALLOWED_PACKAGES
        or metadata.get("ecosystem") != "pip"
        or metadata.get("update_type") != "version-update:semver-patch"
        or metadata.get("maintainer_changes") != "false"
    ):
        return False
    patterns = {"requirements.txt": REQUIREMENT, "constraints.txt": CONSTRAINT}
    filenames = [file.get("filename") for file in files]
    if not files or len(set(filenames)) != len(files) or not set(filenames) <= patterns.keys():
        return False

    changed_names, target_versions = set(), {}
    for file in files:
        if file.get("status") != "modified":
            return False
        removed, added = {}, {}
        for line in file.get("patch", "").splitlines():
            if not line.startswith(("+", "-")):
                continue
            match = patterns[file["filename"]].fullmatch(line[1:])
            if not match:
                return False
            name = match[1].lower()
            versions = added if line[0] == "+" else removed
            if name in versions:
                return False
            versions[name] = tuple(int(value) for value in match.groups()[1:])

        # Missing/truncated patches or unrelated edits must fail closed.
        if (
            not added or set(removed) != set(added) or not set(added) <= names
            or file.get("additions") != len(added)
            or file.get("deletions") != len(removed)
        ):
            return False
        for name, version in added.items():
            if version[:2] != removed[name][:2] or version[2] <= removed[name][2]:
                return False
            if name in target_versions and target_versions[name] != version:
                return False
            target_versions[name] = version
        changed_names.update(added)
    return changed_names == names


def main():
    pages = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    files = [file for page in pages for file in page]
    eligible = eligible_patch(
        {
            "names": os.environ.get("DEPENDENCY_NAMES", ""),
            "ecosystem": os.environ.get("PACKAGE_ECOSYSTEM", ""),
            "update_type": os.environ.get("UPDATE_TYPE", ""),
            "maintainer_changes": os.environ.get("MAINTAINER_CHANGES", ""),
        },
        files,
    )
    with Path(os.environ["GITHUB_OUTPUT"]).open("a", encoding="utf-8") as output:
        output.write(f"eligible={str(eligible).lower()}\n")
    print("Eligible patch update; waiting for required checks." if eligible else "Manual review required; auto-merge was not enabled.")


if __name__ == "__main__":
    main()
