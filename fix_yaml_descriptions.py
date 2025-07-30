#!/usr/bin/env python3
"""
Fix broken YAML description lines in Hugo markdown files
"""

from pathlib import Path

CONTENT_DIR = Path("C:/Users/joepe/seeds-kids-seo/site/content")
files_fixed = 0

for md_file in CONTENT_DIR.rglob("*.md"):
    try:
        lines = md_file.read_text(encoding="utf-8").splitlines()
        if not lines:
            continue

        new_lines = []
        i = 0
        while i < len(lines):
            line = lines[i]
            if line.strip().startswith("description:"):
                # Combine this line with the next one if the next is a dangling fragment
                if i + 1 < len(lines) and not lines[i + 1].strip().startswith(tuple("abcdefghijklmnopqrstuvwxyz")):
                    combined = line.rstrip().rstrip('"') + " " + lines[i + 1].strip().lstrip('"')
                    new_lines.append(combined + '"')
                    i += 2
                    continue
            new_lines.append(line)
            i += 1

        if lines != new_lines:
            md_file.write_text("\n".join(new_lines) + "\n", encoding="utf-8")
            files_fixed += 1
    except Exception as e:
        print(f"Error processing {md_file}: {e}")

print(f"Fixed YAML description line breaks in {files_fixed} markdown files.")