from __future__ import annotations

import argparse
import re
from pathlib import Path

TEXT_EXTENSIONS = {".py", ".md", ".txt", ".toml", ".yml", ".yaml", ".json", ".cff", ".ini", ".cfg", ".sh", ".ps1"}
SKIP_NAMES = {"privacy_scan.py"}
SKIP_DIRS = {".git", ".venv", "venv", "dist", "build", "__pycache__", ".mypy_cache", ".pytest_cache", ".ruff_cache"}

PATTERNS = {
    "private IPv4 address": re.compile(r"\b(?:10\.\d{1,3}\.\d{1,3}\.\d{1,3}|172\.(?:1[6-9]|2\d|3[01])\.\d{1,3}\.\d{1,3}|192\.168\.\d{1,3}\.\d{1,3})\b"),
    "raw Sphero-style device identifier": re.compile(r"\bBP-[0-9A-F]{4}\b", re.I),
    "Windows user path": re.compile(r"[A-Za-z]:\\Users\\[^\\\s]+", re.I),
    "institution/work-placement term": re.compile(r"\b(?:A" + "DFA|UN" + "SW|E" + "WE|lecturer[_ -]?handover)\b", re.I),
}


def scan(root: Path) -> list[str]:
    findings: list[str] = []
    for path in root.rglob("*"):
        if not path.is_file() or path.name in SKIP_NAMES or any(part in SKIP_DIRS for part in path.parts):
            continue
        if path.suffix.lower() not in TEXT_EXTENSIONS and path.name not in {"Makefile", ".editorconfig", ".gitignore", ".gitattributes"}:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for label, pattern in PATTERNS.items():
            for match in pattern.finditer(text):
                line = text.count("\n", 0, match.start()) + 1
                findings.append(f"{path.relative_to(root)}:{line}: {label}: {match.group(0)!r}")
    return findings


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", nargs="?", default=".")
    args = parser.parse_args()
    findings = scan(Path(args.root).resolve())
    if findings:
        print("Privacy scan FAILED")
        for finding in findings:
            print(" -", finding)
        return 1
    print("Privacy scan passed: no blocked identifiers found.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
