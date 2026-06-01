# Taxonomy snapshot provenance

These JSON files are a **vendored snapshot** of the Fideslang default taxonomy. The skill is
self-contained: it validates against these files and never imports or installs the `fideslang`
package at runtime.

## License & attribution

The Fideslang taxonomy is © Ethyca, Inc. and licensed under **Creative Commons Attribution 4.0
International (CC BY 4.0)** — https://creativecommons.org/licenses/by/4.0/. These JSON files are a
**modified** redistribution: the upstream Python definitions were reformatted to JSON and reduced to
the `fides_key` / `name` / `description` fields. See the repository's `NOTICE` file for the full
attribution statement. The skill's own code is MIT-licensed; this data directory remains CC BY 4.0.

## Source

- Repository: https://github.com/ethyca/fideslang
- Files: `src/fideslang/default_taxonomy/{data_categories,data_uses,data_subjects}.py` (branch `main`)
- Taxonomy directory last modified at commit: `21eb1746904d` (2024-11-04)
- Latest published release at snapshot time: `3.1.3`
- Snapshot taken: 2026-06-01

## Contents

| File | Entries |
| --- | --- |
| `data_categories.json` | 85 |
| `data_uses.json` | 56 |
| `data_subjects.json` | 15 |

Each entry is `{ "fides_key": "...", "name": "...", "description": "..." }`. The parent of any key is
the dotted prefix (e.g. the parent of `user.contact.email` is `user.contact`).

## How to refresh

The three source files use a `default_*_factory(fides_key=..., name=..., description=..., parent_key=...)`
call pattern. Re-generate the JSON without executing the source (no `fideslang` install needed) by
parsing it with the standard library `ast` module:

```bash
base="https://raw.githubusercontent.com/ethyca/fideslang/main/src/fideslang/default_taxonomy"
tmp=$(mktemp -d)
for f in data_categories data_uses data_subjects; do curl -fsSL "$base/$f.py" -o "$tmp/$f.py"; done

python3 - "$tmp" "$(dirname "$0")" <<'PY'
import ast, json, sys, pathlib
src, out = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2])
def extract(p):
    rows = {}
    for n in ast.walk(ast.parse(p.read_text())):
        if isinstance(n, ast.Call):
            kw = {k.arg: k.value.value for k in n.keywords
                  if k.arg in ("fides_key", "name", "description") and isinstance(k.value, ast.Constant)}
            if "fides_key" in kw:
                rows[kw["fides_key"]] = {"fides_key": kw["fides_key"],
                                        "name": kw.get("name", ""), "description": kw.get("description", "")}
    return sorted(rows.values(), key=lambda r: r["fides_key"])
for name, f in {"data_categories":"data_categories.py","data_uses":"data_uses.py","data_subjects":"data_subjects.py"}.items():
    (out / f"{name}.json").write_text(json.dumps(extract(src / f), indent=2, ensure_ascii=False) + "\n")
PY
```

After refreshing, update the commit SHA / release / date above.
