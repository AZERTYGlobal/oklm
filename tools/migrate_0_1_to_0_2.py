# -*- coding: utf-8 -*-
# SPDX-License-Identifier: EUPL-1.2
"""Migrate an OKLM manifest from schema 0.1 to schema 0.2.

    python tools/migrate_0_1_to_0_2.py FILE [FILE ...]            # rewrite in place
    python tools/migrate_0_1_to_0_2.py --out DIR FILE [FILE ...]  # write to DIR, keep the source

Only `schemaVersion` "0.1" is migrated. A file that already says "0.2" is left alone (not rewritten,
not reformatted; with --out it is copied byte for byte). Any other value, or none, is refused with a
message and exit code 1: a file of a newer version must not be rewritten as 0.2.

What changes (decisions of 2026-09-21, brief C5):
  - schemaVersion "0.1" -> "0.2";
  - `version` becomes SemVer (E2): "2026" -> "2026.0.0", "1.0" -> "1.0.0"; a label that is not
    SemVer keeps its year when it has one ("NF Z71-300:2019 (AZERTY option)" -> "2019.0.0"),
    otherwise "1.0.0". The original text moves to metadata.versionLabel whenever the new SemVer does
    not say it back (a label, "2026.1" -> "2026.1.0", "007"); it never overwrites a versionLabel
    that is already there (the migration stops instead);
  - a modifier output {"modifier": X} on a level, in `levels` or in a group, becomes role "modifier" +
    modifier X on the key (E22); the output is dropped, and `levels` / the group with it when it was
    the only one. Two different modifiers on one key stop the migration;
  - prefixed members outside an `extensions` object move into that object (D34, D38), on the
    root and on every object of the model (metadata.OKLM_siteView -> metadata.extensions.OKLM_siteView);
    a member that would overwrite an existing extension, or whose value is not an object, stops
    the migration;
  - in every `extensions` object the four reserved namespaces are renamed: frame-keys, firmware,
    geometry, ldml -> OKLM_frameKeys, OKLM_firmware, OKLM_geometry, OKLM_ldml; any other
    lowercase extension becomes EXT_<camelCase>; two names that end up equal stop the migration;
  - extensionsUsed lists every extension name found, plus the names it already listed (the list is
    omitted when there is none).

The migrated manifest is validated (validators/validate.py, errors only) before anything is written:
a migration never produces a file the validator rejects. The output is deterministic: same input,
same bytes. Writing is atomic (temporary file in the same directory, then rename): a failure leaves the
original file as it was.
"""
import argparse
import copy
import glob
import json
import os
import re
import shutil
import sys
import tempfile
from pathlib import Path

SEMVER = re.compile(
    r"(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)"
    r"(?:-(?:0|[1-9][0-9]*|[0-9]*[a-zA-Z-][0-9a-zA-Z-]*)(?:\.(?:0|[1-9][0-9]*|[0-9]*[a-zA-Z-][0-9a-zA-Z-]*))*)?"
    r"(?:\+[0-9a-zA-Z-]+(?:\.[0-9a-zA-Z-]+)*)?"
)
PREFIXED = re.compile(r"(OKLM|EXT|[A-Z][A-Z0-9]*)_[A-Za-z0-9]+")  # used with fullmatch: `$` would accept "\n"
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


class MigrationError(Exception):
    """The file cannot be migrated safely; the message says why. Nothing is written."""


def semver_of(version):
    """(semver, label_or_None) for a 0.1 `version` string.

    The label is the original text, returned when the SemVer alone would lose it: a text that is not a
    version ("NF Z71-300:2019"), a calendar-style "2026.1", a number with leading zeros ("007").
    """
    text = str(version)
    if SEMVER.fullmatch(text):
        return text, None
    if re.fullmatch(r"[0-9]{1,18}", text):
        return f"{int(text)}.0.0", (None if text == str(int(text)) else text)
    if re.fullmatch(r"[0-9]{1,18}\.[0-9]{1,18}", text):
        major, minor = text.split(".")
        plain = text == f"{int(major)}.{int(minor)}"
        return f"{int(major)}.{int(minor)}.0", (None if plain and int(minor) == 0 else text)
    year = re.search(r"\b((?:19|20)[0-9]{2})\b", text)
    return (f"{year.group(1)}.0.0" if year else "1.0.0"), text


def camel(name):
    parts = re.split(r"[^A-Za-z0-9]+", name)
    return "".join(p[:1].upper() + p[1:] for p in parts if p) or "Unnamed"


def ordered(obj, order):
    out = {name: obj[name] for name in order if name in obj}
    out.update({name: value for name, value in obj.items() if name not in out})
    return out


def lift_prefixed(obj, where):
    """Move prefixed members of `obj` into obj['extensions']. Refuses to overwrite an extension or to move
    a value that is not an object (the schema requires objects there)."""
    moved = [name for name in obj if PREFIXED.fullmatch(name)]
    if not moved:
        return
    if "extensions" in obj and not isinstance(obj["extensions"], dict):
        raise MigrationError(f"{where}.extensions is not an object: cannot move {moved[0]} into it")
    ext = obj.setdefault("extensions", {})
    for name in moved:
        if not isinstance(obj[name], dict):
            raise MigrationError(f"{where}.{name} has a non-object value: extension blocks must be objects")
        if name in ext:
            raise MigrationError(f"{where}.{name} collides with {where}.extensions.{name}: "
                                 "merge them by hand, the migration will not overwrite one with the other")
        ext[name] = obj.pop(name)


def rename_extensions(obj, where):
    """Give the keys of obj['extensions'] their 0.2 names (reserved renames, EXT_<camelCase>)."""
    if "extensions" not in obj:
        return
    ext = obj["extensions"]
    if not isinstance(ext, dict):
        raise MigrationError(f"{where}.extensions is not an object")
    renamed, origin = {}, {}
    for name, value in ext.items():
        target = name if PREFIXED.fullmatch(name) else (RENAMES.get(name) or f"EXT_{camel(name)}")
        if target in renamed:
            raise MigrationError(f"{where}.extensions: {origin[target]!r} and {name!r} both become {target!r}: "
                                 "rename one of them by hand")
        renamed[target] = value
        origin[target] = name
    obj["extensions"] = renamed


def _objects(m, name):
    """The objects of the array `name` (nothing when absent), with their path; any other shape stops the run."""
    if name not in m:
        return []
    items = m[name]
    if not isinstance(items, list):
        raise MigrationError(f"{name} is not an array")
    for index, item in enumerate(items):
        if not isinstance(item, dict):
            raise MigrationError(f"{name}[{index}] is not an object")
    return [(f"{name}[{index}]", item) for index, item in enumerate(items)]


def _output_tables(key, where):
    """(path, table) for the output tables of a key: `levels`, then each group of `groups`."""
    tables = []
    if "levels" in key:
        if not isinstance(key["levels"], dict):
            raise MigrationError(f"{where}.levels is not an object")
        tables.append((f"{where}.levels", key["levels"]))
    if "groups" in key:
        if not isinstance(key["groups"], dict):
            raise MigrationError(f"{where}.groups is not an object")
        for group, table in key["groups"].items():
            if not isinstance(table, dict):
                raise MigrationError(f"{where}.groups.{group} is not an object")
            tables.append((f"{where}.groups.{group}", table))
    return tables


def _take_modifiers(key, where):
    """Turn {"modifier": X} outputs into role / modifier on the key (E22)."""
    found = []
    for path, table in _output_tables(key, where):
        for level in list(table):
            out = table[level]
            if isinstance(out, dict) and "modifier" in out:
                found.append((f"{path}.{level}", out["modifier"]))
                del table[level]
    if not found:
        return
    names = sorted({str(value) for _, value in found})
    if len(names) > 1:
        raise MigrationError(f"{where} has modifier outputs naming different functions ({', '.join(names)}): "
                             "a key carries one modifier in 0.2, split it by hand")
    modifier = found[0][1]
    if key.get("role", "modifier") != "modifier":
        raise MigrationError(f"{where}.role is {key['role']!r}: it conflicts with a modifier output at {found[0][0]}")
    if "modifier" in key and key["modifier"] != modifier:
        raise MigrationError(f"{where}.modifier is {key['modifier']!r}, a modifier output at {found[0][0]} says {modifier!r}")
    key["role"] = "modifier"
    key["modifier"] = modifier
    if "levels" in key and not key["levels"]:
        del key["levels"]
    if "groups" in key:
        key["groups"] = {group: table for group, table in key["groups"].items() if table}
        if not key["groups"]:
            del key["groups"]


def _version_label(m, label):
    if "metadata" not in m:
        m["metadata"] = {}
    metadata = m["metadata"]
    if not isinstance(metadata, dict):
        raise MigrationError("metadata is not an object: cannot keep the old version text in metadata.versionLabel")
    if "versionLabel" in metadata and metadata["versionLabel"] != label:
        raise MigrationError(f"metadata.versionLabel is already {metadata['versionLabel']!r} and the old version is "
                             f"{label!r}: the migration will not overwrite one with the other")
    metadata["versionLabel"] = label


def _used_extensions(m):
    used, stack = set(), [m]
    while stack:
        node = stack.pop()
        if isinstance(node, dict):
            ext = node.get("extensions")
            if isinstance(ext, dict):
                used.update(ext)
            stack.extend(value for name, value in node.items() if name != "extensions")
        elif isinstance(node, list):
            stack.extend(node)
    return used


def _check_output(manifest):
    """Refuse to hand back a manifest the validator rejects (errors only, not warnings)."""
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "validators"))
    import validate
    errors = [f for f in validate.analyze(manifest) if f.severity == "error"]
    if errors:
        shown = "; ".join(str(f)[:160] for f in errors[:4])
        more = f" (+{len(errors) - 4} more)" if len(errors) > 4 else ""
        raise MigrationError(f"the migrated manifest would be invalid, nothing written: {shown}{more}")


def migrate(manifest):
    """Return a new 0.2 manifest from a 0.1 one (the argument is not modified).

    A manifest that already says "0.2" comes back unchanged. Raises MigrationError for any other
    schemaVersion, for a collision the migration cannot resolve, and for a result the validator rejects.
    """
    if not isinstance(manifest, dict):
        raise MigrationError("the document is not a JSON object")
    m = copy.deepcopy(manifest)
    declared = m.get("schemaVersion")
    if declared == "0.2":
        return m
    if declared != "0.1":
        shown = "missing" if "schemaVersion" not in m else repr(declared)[:40]
        raise MigrationError(f"schemaVersion is {shown}: this tool only migrates files declaring \"0.1\" "
                             "(a \"0.2\" file is left alone, a newer one needs a newer tool)")
    m["schemaVersion"] = "0.2"

    version = m.get("version", "1.0.0")
    if isinstance(version, bool) or not isinstance(version, (str, int, float)):
        raise MigrationError("version must be a string or a number")
    semver, label = semver_of(version)
    m["version"] = semver
    if label:
        _version_label(m, label)

    for where, key in _objects(m, "keys"):
        _take_modifiers(key, where)
        lift_prefixed(key, where)
        for path, table in _output_tables(key, where):
            for level, out in table.items():
                if isinstance(out, dict):
                    lift_prefixed(out, f"{path}.{level}")
    for name in ("deadKeys", "conformance", "exports"):
        for where, item in _objects(m, name):
            lift_prefixed(item, where)
    for name in ("metadata", "levelSelectors"):
        if isinstance(m.get(name), dict):
            lift_prefixed(m[name], name)
    lift_prefixed(m, "(root)")

    # every `extensions` object of the model gets its 0.2 names
    named = [(m, "(root)")]
    named += [(m[name], name) for name in ("metadata", "levelSelectors") if isinstance(m.get(name), dict)]
    for name in ("keys", "deadKeys", "conformance", "exports"):
        named += [(item, where) for where, item in _objects(m, name)]
    for where, key in _objects(m, "keys"):
        for path, table in _output_tables(key, where):
            named += [(out, f"{path}.{level}") for level, out in table.items() if isinstance(out, dict)]
    for obj, where in named:
        rename_extensions(obj, where)

    used = _used_extensions(m)
    if "extensionsUsed" in m:
        if not isinstance(m["extensionsUsed"], list) or not all(isinstance(n, str) for n in m["extensionsUsed"]):
            raise MigrationError("extensionsUsed is not an array of names")
        used.update(m["extensionsUsed"])
    if used:
        m["extensionsUsed"] = sorted(used)

    if "keys" in m:
        m["keys"] = [ordered(key, KEY_ORDER) for key in m["keys"]]
    result = ordered(m, ROOT_ORDER)
    _check_output(result)
    return result


# --- compact, stable JSON writer: 2-space indent, short scalar arrays and small flat
# objects on one line, the style the hand-written examples use -------------------------

def _scalar(value):
    return json.dumps(value, ensure_ascii=False, allow_nan=False)


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


def write_atomic(path, data):
    """Write `data` (bytes) to `path` through a temporary file of the same directory and a rename: the
    file is either the old one or the new one, never half written."""
    path = Path(path)
    handle, temp = tempfile.mkstemp(dir=path.parent, prefix=path.name + ".", suffix=".tmp")
    try:
        with os.fdopen(handle, "wb") as out:
            out.write(data)
        if path.exists():
            shutil.copymode(path, temp)
        os.replace(temp, path)
    except BaseException:
        try:
            os.unlink(temp)
        except OSError:
            pass
        raise


def manifest_bytes(manifest, expanded=False):
    """The bytes of a manifest. expanded=True uses plain json.dumps(indent=2), the style of manifests
    that were generated rather than hand-written. NaN and Infinity are refused (A-19)."""
    text = (json.dumps(manifest, indent=2, ensure_ascii=False, allow_nan=False) if expanded
            else dumps(manifest))
    return (text + "\n").encode("utf-8")


def write_manifest(path, manifest, expanded=False):
    write_atomic(path, manifest_bytes(manifest, expanded))


def is_expanded(text):
    """True when `text` is exactly what json.dumps(indent=2) prints for its own content."""
    return text == json.dumps(json.loads(text), indent=2, ensure_ascii=False) + "\n"


def _migrate_file(path, out_dir, written):
    """Migrate one file; returns the status line. Raises on any problem, the caller reports it."""
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "validators"))
    import validate
    raw = path.read_bytes().decode("utf-8-sig")  # a BOM (PowerShell 5.1 Set-Content) is accepted
    source = validate.load_json_text(raw)
    problems = [f for f in validate.text_findings(source) if f.severity == "error"]
    if problems:
        raise MigrationError("; ".join(str(f) for f in problems[:3]))
    migrated = migrate(source)
    target = (out_dir / path.name) if out_dir else path
    if out_dir:
        if target in written:
            raise MigrationError(f"{target} was already written by another input of this run: "
                                 "two files with the same name, nothing overwritten")
        out_dir.mkdir(parents=True, exist_ok=True)
    if migrated == source:  # already 0.2: left alone
        if out_dir and not (target.exists() and target.samefile(path)):
            write_atomic(target, path.read_bytes())
            written.add(target)
        return f"unchanged (already 0.2): {path}" + (f" -> {target}" if out_dir else "")
    data = manifest_bytes(migrated, expanded=is_expanded(raw))
    write_atomic(target, data)
    written.add(target)
    return f"migrated: {path} -> {target}"


def main(argv=None):
    for stream in (sys.stdout, sys.stderr):
        try:  # a redirected stdout is cp1252 on Windows: a CJK file name must not abort the run (A-12)
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass
    parser = argparse.ArgumentParser(description="Migrate OKLM manifests from schema 0.1 to 0.2.")
    parser.add_argument("files", nargs="+", metavar="FILE")
    parser.add_argument("--out", metavar="DIR", help="write migrated copies here instead of in place")
    args = parser.parse_args(argv)
    out_dir = Path(args.out) if args.out else None
    names = []
    for name in args.files:  # PowerShell 5.1 does not expand wildcards for a native command (A-20)
        if any(c in name for c in "*?[") and not Path(name).exists():
            names.extend(sorted(glob.glob(name, recursive=True)) or [name])
        else:
            names.append(name)
    status, written = 0, set()
    for name in names:
        path = Path(name)
        try:
            print(_migrate_file(path, out_dir, written))
        except MigrationError as exc:
            print(f"error: {path}: {exc}", file=sys.stderr)
            status = 1
        except Exception as exc:  # noqa: BLE001 - one bad file must not stop the batch
            print(f"error: {path}: {type(exc).__name__}: {str(exc)[:200]}", file=sys.stderr)
            status = 1
    return status


if __name__ == "__main__":
    sys.exit(main())
