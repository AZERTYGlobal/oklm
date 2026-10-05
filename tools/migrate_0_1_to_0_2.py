# -*- coding: utf-8 -*-
"""Migrate an OKLM manifest from schema 0.1 to schema 0.2.

    python tools/migrate_0_1_to_0_2.py FILE [FILE ...]            # rewrite in place
    python tools/migrate_0_1_to_0_2.py --out DIR FILE [FILE ...]  # write to DIR, keep the source

What changes (decisions of 2026-09-21, brief C5):
  - schemaVersion "0.1" -> "0.2";
  - `version` becomes SemVer (E2): "2026" -> "2026.0.0", "1.0" -> "1.0.0"; a label that is not
    SemVer keeps its year when it has one ("NF Z71-300:2019 (AZERTY option)" -> "2019.0.0"),
    otherwise "1.0.0", and the original text moves to metadata.versionLabel;
  - a modifier output {"modifier": X} on a level becomes role "modifier" + modifier X on the key
    (E22); the level is dropped, and `levels` with it when it was the only one;
  - prefixed members outside an `extensions` object move into that object (D34, D38), on the
    root and on every object of the model (metadata.OKLM_siteView -> metadata.extensions.OKLM_siteView);
  - the four reserved namespaces are renamed: frame-keys, firmware, geometry, ldml ->
    OKLM_frameKeys, OKLM_firmware, OKLM_geometry, OKLM_ldml; any other lowercase root extension
    becomes EXT_<camelCase>;
  - extensionsUsed lists every extension name found (the list is omitted when there is none).

A file that is already 0.2 is left alone. The output is deterministic: same input, same bytes.
"""
import argparse
import json
import re
import sys
from pathlib import Path

SEMVER = re.compile(
    r"^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)(-[0-9A-Za-z-]+(\.[0-9A-Za-z-]+)*)?"
    r"(\+[0-9A-Za-z-]+(\.[0-9A-Za-z-]+)*)?$"
)
PREFIXED = re.compile(r"^(OKLM|EXT|[A-Z][A-Z0-9]*)_[A-Za-z0-9]+$")
RENAMES = {
    "frame-keys": "OKLM_frameKeys",
    "firmware": "OKLM_firmware",
    "geometry": "OKLM_geometry",
    "ldml": "OKLM_ldml",
}

ROOT_ORDER = [
    "schemaVersion", "layoutId", "name", "version", "license", "authors", "description", "locales",
    "geometry", "levelSelectors", "keys", "deadKeys", "conformance", "exports", "metadata",
    "extensionsUsed", "extensionsRequired", "featuresRequired", "extensions",
]
KEY_ORDER = [
    "id", "hid", "xkb", "code", "name", "role", "modifier", "levels", "groups", "categories", "extensions",
]


def semver_of(version):
    """(semver, label_or_None) for a 0.1 `version` string."""
    text = str(version)
    if SEMVER.match(text):
        return text, None
    if re.fullmatch(r"[0-9]+", text):
        return f"{int(text)}.0.0", None
    if re.fullmatch(r"[0-9]+\.[0-9]+", text):
        major, minor = text.split(".")
        return f"{int(major)}.{int(minor)}.0", None
    year = re.search(r"\b((?:19|20)[0-9]{2})\b", text)
    return (f"{year.group(1)}.0.0" if year else "1.0.0"), text


def camel(name):
    parts = re.split(r"[^A-Za-z0-9]+", name)
    return "".join(p[:1].upper() + p[1:] for p in parts if p) or "Unnamed"


def ordered(obj, order):
    out = {name: obj[name] for name in order if name in obj}
    out.update({name: value for name, value in obj.items() if name not in out})
    return out


def lift_prefixed(obj):
    """Move prefixed members of `obj` into obj['extensions']. Returns names moved."""
    moved = [name for name in list(obj) if PREFIXED.match(name)]
    if moved:
        ext = obj.setdefault("extensions", {})
        for name in moved:
            ext[name] = obj.pop(name)
    return moved


def migrate(manifest):
    """Return a new 0.2 manifest from a 0.1 one (the argument is not modified)."""
    m = json.loads(json.dumps(manifest))
    if str(m.get("schemaVersion")) == "0.2":
        return m
    m["schemaVersion"] = "0.2"

    semver, label = semver_of(m.get("version", "1.0.0"))
    m["version"] = semver
    if label is not None:
        m.setdefault("metadata", {})["versionLabel"] = label

    for key in m.get("keys", []):
        levels = key.get("levels", {})
        for level in sorted(levels, key=lambda x: int(x)):
            out = levels[level]
            if isinstance(out, dict) and "modifier" in out:
                key["role"] = "modifier"
                key["modifier"] = out["modifier"]
                del levels[level]
        if "levels" in key and not key["levels"]:
            del key["levels"]
        lift_prefixed(key)
        for lvl_out in list(key.get("levels", {}).values()):
            if isinstance(lvl_out, dict):
                lift_prefixed(lvl_out)

    for collection in ("deadKeys", "conformance", "exports"):
        for item in m.get(collection, []):
            lift_prefixed(item)
    if isinstance(m.get("metadata"), dict):
        lift_prefixed(m["metadata"])
    if isinstance(m.get("levelSelectors"), dict):
        lift_prefixed(m["levelSelectors"])

    lift_prefixed(m)
    root_ext = m.get("extensions")
    if isinstance(root_ext, dict):
        renamed = {}
        for name, value in root_ext.items():
            if PREFIXED.match(name):
                renamed[name] = value
            else:
                renamed[RENAMES.get(name) or f"EXT_{camel(name)}"] = value
        m["extensions"] = renamed

    used = set()

    def collect(node):
        if isinstance(node, dict):
            ext = node.get("extensions")
            if isinstance(ext, dict):
                used.update(ext)
            for name, value in node.items():
                if name != "extensions":
                    collect(value)
        elif isinstance(node, list):
            for value in node:
                collect(value)

    collect(m)
    if used:
        m["extensionsUsed"] = sorted(used)

    m["keys"] = [ordered(key, KEY_ORDER) for key in m.get("keys", [])]
    return ordered(m, ROOT_ORDER)


# --- compact, stable JSON writer: 2-space indent, short scalar arrays and small flat
# objects on one line, the style the hand-written examples use -------------------------

def _scalar(value):
    return json.dumps(value, ensure_ascii=False)


def _inline(value, limit):
    if isinstance(value, list) and all(not isinstance(v, (dict, list)) for v in value):
        text = "[" + ", ".join(_scalar(v) for v in value) + "]"
    elif isinstance(value, dict) and value and all(
        not isinstance(v, (list, dict)) or (isinstance(v, dict) and all(not isinstance(w, (list, dict)) for w in v.values()))
        for v in value.values()
    ):
        parts = []
        for name, item in value.items():
            if isinstance(item, dict):
                inner = "{ " + ", ".join(f"{_scalar(k)}: {_scalar(v)}" for k, v in item.items()) + " }"
            else:
                inner = _scalar(item)
            parts.append(f"{_scalar(name)}: {inner}")
        text = "{ " + ", ".join(parts) + " }"
    else:
        return None
    return text if len(text) <= limit else None


INLINE_KEYS = {"levels", "authors", "locales", "geometry", "categories"}


def dumps(value, indent=0, key=None):
    pad = "  " * indent
    if isinstance(value, dict):
        if not value:
            return "{}"
        if key in INLINE_KEYS:
            text = _inline(value, 100 - indent * 2)
            if text:
                return text
        items = [f"{pad}  {_scalar(name)}: {dumps(item, indent + 1, name)}" for name, item in value.items()]
        return "{\n" + ",\n".join(items) + f"\n{pad}}}"
    if isinstance(value, list):
        if not value:
            return "[]"
        text = _inline(value, 100 - indent * 2)
        if text:
            return text
        items = [f"{pad}  {dumps(item, indent + 1)}" for item in value]
        return "[\n" + ",\n".join(items) + f"\n{pad}]"
    return _scalar(value)


def write_manifest(path, manifest, expanded=False):
    """Write a manifest. expanded=True uses plain json.dumps(indent=2), the style of
    manifests that were generated rather than hand-written."""
    text = json.dumps(manifest, indent=2, ensure_ascii=False) if expanded else dumps(manifest)
    Path(path).write_bytes((text + "\n").encode("utf-8"))


def is_expanded(text):
    """True when `text` is exactly what json.dumps(indent=2) prints for its own content."""
    return text == json.dumps(json.loads(text), indent=2, ensure_ascii=False) + "\n"


def main(argv=None):
    parser = argparse.ArgumentParser(description="Migrate OKLM manifests from schema 0.1 to 0.2.")
    parser.add_argument("files", nargs="+", metavar="FILE")
    parser.add_argument("--out", metavar="DIR", help="write migrated copies here instead of in place")
    args = parser.parse_args(argv)
    for name in args.files:
        path = Path(name)
        raw = path.read_text(encoding="utf-8")
        source = json.loads(raw)
        migrated = migrate(source)
        target = (Path(args.out) / path.name) if args.out else path
        if args.out:
            Path(args.out).mkdir(parents=True, exist_ok=True)
        write_manifest(target, migrated, expanded=is_expanded(raw))
        state = "unchanged (already 0.2)" if migrated == source else "migrated"
        print(f"{state}: {path} -> {target}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
