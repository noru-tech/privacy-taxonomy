#!/usr/bin/env python3
"""Validate a Fides data map manifest against the BUNDLED Fideslang taxonomy snapshot.

Self-contained and atomic:
  * Uses only the Python standard library.
  * Sources valid keys from ../references/taxonomy/*.json (no `fideslang` package, no network).
  * Parses YAML with PyYAML if it happens to be importable, otherwise falls back to a small
    built-in loader for the block-YAML subset that Fides manifests use — so this runs anywhere
    `python3` exists.

Checks performed
  Structural:
    - every dataset / system has a `fides_key` matching the Fides key pattern
    - datasets have list `collections`, each with a `name` and list `fields` (recursed)
    - systems have a `system_type` and well-formed `privacy_declarations`
  Cross-reference (the part Pydantic alone does not do):
    - every `data_categories` value exists in the data-categories snapshot (or is declared
      as a custom `data_category` in the manifest)
    - every `data_use` exists in the data-uses snapshot (or custom)
    - every `data_subjects` value exists in the data-subjects snapshot (or custom)
  Unknown keys get a "did you mean ...?" suggestion.

Usage:
    python3 validate_manifest.py path/to/datamap.yml
Exit codes: 0 = valid (warnings allowed), 1 = validation errors, 2 = usage / load error.
"""
import difflib
import json
import pathlib
import re
import sys

TAXONOMY_DIR = pathlib.Path(__file__).resolve().parent.parent / "references" / "taxonomy"
FIDES_KEY_RE = re.compile(r"^[A-Za-z0-9_.<>-]+$")
_BLOCK_SCALAR_RE = re.compile(r"^[>|][+\-]?\d*$")  # >, |, >-, >+, |-, |+, >2, |2, …
RESOURCE_KEYS = {
    "dataset", "system", "data_category", "data_use", "data_subject",
    "organization", "policy", "registry", "evaluation",
}


# --------------------------------------------------------------------------- #
# Taxonomy snapshot
# --------------------------------------------------------------------------- #
def load_taxonomy():
    def keys(name):
        rows = json.loads((TAXONOMY_DIR / name).read_text(encoding="utf-8"))
        return [r["fides_key"] for r in rows]
    return {
        "category": keys("data_categories.json"),
        "use": keys("data_uses.json"),
        "subject": keys("data_subjects.json"),
    }


# --------------------------------------------------------------------------- #
# YAML loading: PyYAML if available, else a minimal block-YAML fallback loader
# --------------------------------------------------------------------------- #
def load_yaml(text):
    try:
        import yaml  # type: ignore
        return yaml.safe_load(text), "PyYAML"
    except ImportError:
        return _fallback_load(text), "bundled fallback loader"


def _scalar(raw):
    s = raw.strip()
    if s == "" or s in ("null", "~", "Null", "NULL"):
        return None
    if s in ("true", "True", "TRUE"):
        return True
    if s in ("false", "False", "FALSE"):
        return False
    if len(s) >= 2 and s[0] == s[-1] and s[0] in ("'", '"'):
        return s[1:-1]
    if s.startswith("[") and s.endswith("]"):  # inline flow sequence
        inner = s[1:-1].strip()
        return [_scalar(p) for p in _split_flow(inner)] if inner else []
    if re.fullmatch(r"-?\d+", s):
        return int(s)
    if re.fullmatch(r"-?\d+\.\d+", s):
        return float(s)
    return s


def _split_flow(inner):
    parts, buf, depth, quote = [], "", 0, None
    for ch in inner:
        if quote:
            buf += ch
            if ch == quote:
                quote = None
        elif ch in ("'", '"'):
            quote = ch
            buf += ch
        elif ch in "[{":
            depth += 1
            buf += ch
        elif ch in "]}":
            depth -= 1
            buf += ch
        elif ch == "," and depth == 0:
            parts.append(buf)
            buf = ""
        else:
            buf += ch
    if buf.strip():
        parts.append(buf)
    return parts


def _strip_comment(line):
    """Remove a trailing inline comment that is outside quotes."""
    quote = None
    for i, ch in enumerate(line):
        if quote:
            if ch == quote:
                quote = None
        elif ch in ("'", '"'):
            quote = ch
        elif ch == "#" and (i == 0 or line[i - 1] in (" ", "\t")):
            return line[:i]
    return line


def _tokenize(text):
    """Return [(indent, content)] for significant lines."""
    out = []
    for raw in text.splitlines():
        stripped = _strip_comment(raw).rstrip()
        if not stripped.strip():
            continue
        if stripped.lstrip().startswith("#"):
            continue
        indent = len(stripped) - len(stripped.lstrip(" "))
        out.append((indent, stripped.lstrip(" ")))
    return out


def _split_kv(content):
    """Split 'key: value' / 'key:' -> (key, value_or_None). Returns (None, None) if not a mapping."""
    if content.endswith(":"):
        return content[:-1].strip(), None
    m = re.match(r"^(.*?):\s+(.*)$", content)
    if m:
        return m.group(1).strip(), m.group(2)
    return None, None


def _fallback_load(text):
    lines = _tokenize(text)
    value, _ = _parse_node(lines, 0)
    return value


def _parse_node(lines, i):
    indent = lines[i][0]
    if lines[i][1] == "-" or lines[i][1].startswith("- "):
        return _parse_seq(lines, i, indent)
    return _parse_map(lines, i, indent)


def _parse_seq(lines, i, indent):
    seq = []
    while i < len(lines) and lines[i][0] == indent and (lines[i][1] == "-" or lines[i][1].startswith("- ")):
        rest = lines[i][1][1:].strip()
        if rest == "":
            i += 1
            if i < len(lines) and lines[i][0] > indent:
                val, i = _parse_node(lines, i)
            else:
                val = None
            seq.append(val)
        elif _split_kv(rest)[0] is not None:
            # mapping that starts inline after the dash; continuation keys align under `rest`
            child_indent = indent + (len(lines[i][1]) - len(lines[i][1].lstrip("- ")))
            child_indent = indent + 2 if child_indent <= indent else child_indent
            group = [(child_indent, rest)]
            j = i + 1
            while j < len(lines) and lines[j][0] >= child_indent:
                group.append(lines[j])
                j += 1
            mapping, _ = _parse_map(group, 0, child_indent)
            seq.append(mapping)
            i = j
        else:
            seq.append(_scalar(rest))
            i += 1
    return seq, i


def _parse_map(lines, i, indent):
    d = {}
    while i < len(lines) and lines[i][0] == indent:
        key, val = _split_kv(lines[i][1])
        if key is None:
            break
        if val is None:
            i += 1
            if i < len(lines) and lines[i][0] > indent:
                child, i = _parse_node(lines, i)
                d[key] = child
            elif i < len(lines) and lines[i][0] == indent and (lines[i][1] == "-" or lines[i][1].startswith("- ")):
                child, i = _parse_seq(lines, i, indent)
                d[key] = child
            else:
                d[key] = None
        elif _BLOCK_SCALAR_RE.match(val):
            # Block scalar (> folded, | literal) — consume indented continuation lines as value.
            # Without this, the continuation lines appear at a deeper indent than the current map
            # context, causing _parse_map to break early and silently drop all subsequent keys
            # (e.g. `collections:` after a `description: >` block).
            i += 1
            block_lines = []
            while i < len(lines) and lines[i][0] > indent:
                block_lines.append(lines[i][1])
                i += 1
            sep = " " if val[0] == ">" else "\n"
            d[key] = sep.join(block_lines)
        else:
            d[key] = _scalar(val)
            i += 1
    return d, i


# --------------------------------------------------------------------------- #
# Validation
# --------------------------------------------------------------------------- #
class Report:
    def __init__(self):
        self.errors = []
        self.warnings = []

    def err(self, path, msg):
        self.errors.append((path, msg))

    def warn(self, path, msg):
        self.warnings.append((path, msg))


def _suggest(key, valid):
    hit = difflib.get_close_matches(str(key), valid, n=1, cutoff=0.6)
    return f" (did you mean '{hit[0]}'?)" if hit else ""


def _aslist(node):
    return node if isinstance(node, list) else []


def _check_fides_key(rep, path, obj):
    fk = obj.get("fides_key") if isinstance(obj, dict) else None
    if not fk:
        rep.err(path, "missing required `fides_key`")
    elif not FIDES_KEY_RE.match(str(fk)):
        rep.err(f"{path}.fides_key", f"`{fk}` does not match the Fides key pattern [A-Za-z0-9_.<>-]")
    return fk


def _check_categories(rep, path, obj, valid):
    cats = obj.get("data_categories")
    if cats is None:
        return
    if not isinstance(cats, list):
        rep.err(f"{path}.data_categories", "must be a list")
        return
    for c in cats:
        if c not in valid["category"]:
            rep.err(f"{path}.data_categories", f"unknown data category '{c}'" + _suggest(c, valid["category"]))


def _check_fields(rep, path, fields, valid):
    for idx, fld in enumerate(_aslist(fields)):
        fpath = f"{path}.fields[{idx}]"
        if not isinstance(fld, dict):
            rep.err(fpath, "field must be a mapping")
            continue
        if not fld.get("name"):
            rep.err(fpath, "missing required `name`")
        _check_categories(rep, fpath, fld, valid)
        if "fields" in fld:  # nested (JSON / embedded)
            _check_fields(rep, fpath, fld["fields"], valid)


def validate(doc, valid):
    rep = Report()
    if not isinstance(doc, dict):
        rep.err("<root>", "manifest must be a mapping with resource keys like `dataset:` / `system:`")
        return rep

    # Extend valid keys with any custom resources declared in the manifest itself.
    for kind, field in (("data_category", "category"), ("data_use", "use"), ("data_subject", "subject")):
        for res in _aslist(doc.get(kind)):
            if isinstance(res, dict) and res.get("fides_key"):
                valid[field] = valid[field] + [res["fides_key"]]

    for top in doc:
        if top not in RESOURCE_KEYS:
            rep.warn(top, "unrecognized top-level resource key (ignored)")

    dataset_keys = set()

    # ---- datasets ----
    for di, ds in enumerate(_aslist(doc.get("dataset"))):
        path = f"dataset[{di}]"
        if not isinstance(ds, dict):
            rep.err(path, "dataset must be a mapping")
            continue
        fk = _check_fides_key(rep, path, ds)
        if fk:
            dataset_keys.add(fk)
        _check_categories(rep, path, ds, valid)
        collections = ds.get("collections")
        if collections is None:
            rep.warn(path, "dataset has no `collections`")
        elif not isinstance(collections, list):
            rep.err(f"{path}.collections", "must be a list")
        else:
            for ci, col in enumerate(collections):
                cpath = f"{path}.collections[{ci}]"
                if not isinstance(col, dict):
                    rep.err(cpath, "collection must be a mapping")
                    continue
                if not col.get("name"):
                    rep.err(cpath, "missing required `name`")
                _check_categories(rep, cpath, col, valid)
                if "fields" not in col:
                    rep.warn(cpath, "collection has no `fields`")
                else:
                    _check_fields(rep, cpath, col.get("fields"), valid)

    # ---- systems ----
    for si, sysd in enumerate(_aslist(doc.get("system"))):
        path = f"system[{si}]"
        if not isinstance(sysd, dict):
            rep.err(path, "system must be a mapping")
            continue
        _check_fides_key(rep, path, sysd)
        if not sysd.get("system_type"):
            rep.err(path, "missing required `system_type`")
        for ref in _aslist(sysd.get("dataset_references")):
            if ref not in dataset_keys:
                rep.warn(f"{path}.dataset_references",
                         f"'{ref}' is not a dataset defined in this manifest")
        decls = sysd.get("privacy_declarations")
        if decls is None:
            rep.warn(path, "system has no `privacy_declarations`")
        elif not isinstance(decls, list):
            rep.err(f"{path}.privacy_declarations", "must be a list")
        else:
            for pi, decl in enumerate(decls):
                dpath = f"{path}.privacy_declarations[{pi}]"
                if not isinstance(decl, dict):
                    rep.err(dpath, "privacy declaration must be a mapping")
                    continue
                if not decl.get("name"):
                    rep.warn(dpath, "privacy declaration has no `name`")
                use = decl.get("data_use")
                if not use:
                    rep.err(dpath, "missing required `data_use`")
                elif use not in valid["use"]:
                    rep.err(f"{dpath}.data_use", f"unknown data use '{use}'" + _suggest(use, valid["use"]))
                _check_categories(rep, dpath, decl, valid)
                subjects = decl.get("data_subjects")
                if subjects is not None:
                    if not isinstance(subjects, list):
                        rep.err(f"{dpath}.data_subjects", "must be a list")
                    else:
                        for s in subjects:
                            if s not in valid["subject"]:
                                rep.err(f"{dpath}.data_subjects",
                                        f"unknown data subject '{s}'" + _suggest(s, valid["subject"]))

    return rep, len(_aslist(doc.get("dataset"))), len(_aslist(doc.get("system")))


# --------------------------------------------------------------------------- #
def main(argv):
    if len(argv) != 1:
        sys.stderr.write("usage: validate_manifest.py <manifest.yml>\n")
        return 2
    path = pathlib.Path(argv[0])
    if not path.is_file():
        sys.stderr.write(f"error: no such file: {path}\n")
        return 2
    try:
        doc, loader = load_yaml(path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        sys.stderr.write(f"error: could not parse YAML ({exc})\n")
        return 2

    valid = load_taxonomy()
    result = validate(doc, valid)
    if isinstance(result, Report):  # root error
        rep, n_ds, n_sys = result, 0, 0
    else:
        rep, n_ds, n_sys = result

    print(f"(parsed with {loader})")
    for path_, msg in rep.warnings:
        print(f"  WARN  {path_}: {msg}")
    for path_, msg in rep.errors:
        print(f"  ERROR {path_}: {msg}")

    if rep.errors:
        print(f"\nFAILED: {len(rep.errors)} error(s), {len(rep.warnings)} warning(s).")
        return 1
    print(f"\nOK: {n_ds} dataset(s), {n_sys} system(s), all keys valid"
          f" ({len(rep.warnings)} warning(s)).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
