#!/usr/bin/env python3
"""Print the bundled Fideslang taxonomy snapshot as a compact classification reference.

Self-contained: reads only the vendored JSON files under ../references/taxonomy/ and uses
only the Python standard library. No `fideslang` package, no network.

Usage:
    python3 dump_taxonomy.py                      # all three taxonomies
    python3 dump_taxonomy.py categories          # just data categories
    python3 dump_taxonomy.py uses subjects       # any subset: categories | uses | subjects
    python3 dump_taxonomy.py --no-descriptions   # keys only (compact)
"""
import json
import pathlib
import sys

TAXONOMY_DIR = pathlib.Path(__file__).resolve().parent.parent / "references" / "taxonomy"

SECTIONS = {
    "categories": ("data_categories.json", "DATA CATEGORIES (what kind of data — use on dataset fields)"),
    "uses": ("data_uses.json", "DATA USES (why data is processed — use on system privacy_declarations.data_use)"),
    "subjects": ("data_subjects.json", "DATA SUBJECTS (whose data — use on privacy_declarations.data_subjects)"),
}


def load(filename):
    path = TAXONOMY_DIR / filename
    return json.loads(path.read_text(encoding="utf-8"))


def main(argv):
    show_desc = "--no-descriptions" not in argv
    wanted = [a for a in argv if not a.startswith("-")]
    if not wanted:
        wanted = ["categories", "uses", "subjects"]

    unknown = [w for w in wanted if w not in SECTIONS]
    if unknown:
        sys.stderr.write(f"Unknown section(s): {', '.join(unknown)}. "
                         f"Choose from: {', '.join(SECTIONS)}\n")
        return 2

    for section in wanted:
        filename, title = SECTIONS[section]
        rows = load(filename)
        print(f"## {title}  [{len(rows)} keys]")
        for r in rows:
            key = r["fides_key"]
            if show_desc and r.get("description"):
                print(f"  {key}  —  {r['description']}")
            else:
                print(f"  {key}")
        print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
