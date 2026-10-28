#!/usr/bin/env python3
"""Offline release checks. Standard library only; never loads a CAD backend."""
from __future__ import annotations

import json
import ast
import re
import sys
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
SKILLS = (
    "creo-native-model", "creo-surface-design", "creo-parametric-edit",
    "creo-diagnose", "creo-toolkit-dev", "screen-observe-loop",
)
REQUIRED = (
    "README.md", "LICENSE", "THIRD_PARTY_NOTICES.md", "CONTRIBUTING.md",
    "SECURITY.md", "docs/SETUP.md", "docs/CAPABILITIES.md",
    "docs/TOOL-CONTRACT.md", "docs/TROUBLESHOOTING.md", "docs/DEVELOPMENT.md",
    "scripts/install-skills.ps1", ".github/workflows/validate.yml",
)
SKIP_DIRS = {".git", "__pycache__", ".venv", "venv"}
FORBIDDEN_SUFFIXES = {
    ".dll", ".exe", ".lib", ".obj", ".pdb", ".log", ".lic", ".dat",
    ".stp", ".step", ".igs", ".iges", ".brep", ".pem", ".key",
}
TOKEN = re.compile(r"(?:sk-[A-Za-z0-9_-]{20,}|gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,})")
PERSONAL_PATH = re.compile(r"(?i)[A-Z]:[\\/]Users[\\/](?![<%$])[^\\/\s]+")
LINK = re.compile(r"\[[^\]\n]+\]\(([^)\n]+)\)")


def main() -> int:
    errors: list[str] = []
    checked = 0
    for relative in REQUIRED:
        if not (ROOT / relative).is_file():
            errors.append(f"Missing required file: {relative}")

    for name in SKILLS:
        path = ROOT / "skills" / name / "SKILL.md"
        license_file = path.parent / "LICENSE"
        if not license_file.is_file() or license_file.read_bytes() != (ROOT / "LICENSE").read_bytes():
            errors.append(f"Standalone skill is missing the package license: {name}")
        if not path.is_file():
            errors.append(f"Missing skill: {name}")
            continue
        text = path.read_text(encoding="utf-8")
        front = re.match(r"\A---\n(.*?)\n---(?:\n|$)", text, re.S)
        if not front:
            errors.append(f"Invalid frontmatter boundary: {name}")
            continue
        name_line = re.search(r"^name:\s*['\"]?([a-z0-9-]+)['\"]?\s*$", front[1], re.M)
        description = re.search(r"^description:\s*(.+)$", front[1], re.M)
        if not name_line or name_line[1] != name:
            errors.append(f"Skill name mismatch: {name}")
        if not description or description[1].strip() in ('""', "''"):
            errors.append(f"Missing description: {name}")
        if "[TODO:" in text:
            errors.append(f"Unfinished skill scaffold: {name}")

    for path in sorted(ROOT.rglob("*")):
        relative = path.relative_to(ROOT)
        if any(part in SKIP_DIRS for part in relative.parts) or not path.is_file():
            continue
        checked += 1
        if path.suffix.lower() in FORBIDDEN_SUFFIXES or re.search(r"\.(prt|asm|drw)(\.\d+)?$", path.name, re.I):
            errors.append(f"Generated/proprietary artifact in release: {relative}")
        if path.name in {"auth.json", "config.toml"} or path.name == ".env":
            errors.append(f"Local configuration in release: {relative}")
        try:
            text = path.read_text(encoding="utf-8-sig")
        except UnicodeError:
            errors.append(f"Non-UTF-8 or binary file in text-only release: {relative}")
            continue
        if TOKEN.search(text):
            errors.append(f"Possible credential in {relative} (value suppressed)")
        if PERSONAL_PATH.search(text):
            errors.append(f"Machine-specific user path in {relative}")
        if path.suffix == ".json":
            try:
                json.loads(text)
            except ValueError as error:
                errors.append(f"Invalid JSON {relative}: {error}")
        if path.suffix == ".py":
            try:
                ast.parse(text, filename=str(relative))
            except SyntaxError as error:
                errors.append(f"Invalid Python {relative}: {error}")
        if path.suffix == ".md":
            for match in LINK.finditer(text):
                target = match[1].strip().strip("<>")
                parsed = urlsplit(target)
                if parsed.scheme or not parsed.path:
                    continue
                linked = (path.parent / unquote(parsed.path)).resolve()
                if not linked.is_relative_to(ROOT):
                    errors.append(f"Link leaves package in {relative}: {target}")
                elif not linked.exists():
                    errors.append(f"Broken link in {relative}: {target}")
                # Each skill must remain self-contained after separate install.
                elif relative.parts[0] == "skills":
                    skill_root = ROOT / "skills" / relative.parts[1]
                    if not linked.is_relative_to(skill_root):
                        errors.append(f"Link leaves installable skill in {relative}: {target}")

    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        print(f"FAIL: {len(errors)} issue(s)")
        return 1
    print(f"PASS: {len(SKILLS)} skills; {checked} package files; links, metadata, JSON and release scope checked.")
    print("Offline package check only. No Creo integration test was run.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
