# -*- coding: utf-8 -*-
# SPDX-License-Identifier: EUPL-1.2
"""The exporter command line, tools/export.py (audit 2026-10-09: B-15). Exit code 0/1.

    python tools/tests/test_exports_cli.py

Runs the script as a subprocess in a temporary directory: an output directory that does not exist, a
result that is `unsupported` (not a failure), a refused manifest (clean FAILED, no traceback), and the
unchanged success path with the golden bytes.
"""
import json
import subprocess
import sys
import tempfile
from pathlib import Path

from exports_support import ROOT, check, finish, minimal

EXPORT = ROOT / "tools" / "export.py"


def run(*args):
    done = subprocess.run([sys.executable, "-B", str(EXPORT), *map(str, args)], capture_output=True, text=True,
                          encoding="utf-8", cwd=str(ROOT))
    return done.returncode, done.stdout + done.stderr


def main():
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        example = ROOT / "examples" / "qwerty-us.oklm.json"

        # --out that does not exist is created, nested too; the file is the golden
        out = tmp / "does" / "not" / "exist"
        code, text = run("--target", "klc", "--out", out, example)
        check(code == 0 and "Traceback" not in text, f"missing --out directory: exit {code}: {text[:200]}")
        golden = ROOT / "examples" / "exports" / "klc" / "qwerty-us.klc"
        check((out / "qwerty-us.klc").exists() and (out / "qwerty-us.klc").read_bytes() == golden.read_bytes(), "klc written to the new directory differs from the golden")

        # --out that is a file: clear message, exit 2, no traceback
        blocker = tmp / "blocker"
        blocker.write_text("x", encoding="utf-8")
        code, text = run("--target", "klc", "--out", blocker, example)
        check(code == 2 and "ERROR cannot use the output directory" in text and "Traceback" not in text, f"--out is a file: exit {code}: {text[:200]}")

        # unsupported (Stream Deck, only ASCII letters): report written, not FAILED, exit 0
        code, text = run("--target", "streamdeck", "--out", tmp, ROOT / "examples" / "azerty-global-minimal.oklm.json")
        check(code == 0 and "UNSUPPORTED" in text and "FAILED" not in text, f"unsupported: exit {code}: {text[:200]}")
        report = json.loads((tmp / "azerty-global-minimal.streamDeckProfile.report.json").read_text(encoding="utf-8"))
        check(report["compatibilityLevel"] == "unsupported", "unsupported report not written")

        # a refused manifest (control character in `name`): FAILED, exit 1, error listed, no traceback
        manifest = minimal()
        manifest["name"] = "A\nB"
        bad = tmp / "bad.oklm.json"
        bad.write_text(json.dumps(manifest, ensure_ascii=False), encoding="utf-8")
        for target in ("ldml", "xkb", "keylayout", "klc", "streamdeck"):
            code, text = run("--target", target, "--out", tmp / "bad-out", bad)
            check("Traceback" not in text, f"{target}: traceback on a refused manifest: {text[:200]}")
            check(code == 1 and ("FAILED" in text or "ERROR" in text), f"{target}: refused manifest exit {code}: {text[:200]}")
            check(not (tmp / "bad-out" / f"bad.{ {'ldml': 'ldml.xml', 'streamdeck': 'streamDeckProfile'}.get(target, target) }").exists(),
                  f"{target}: a file was written for a refused manifest")
    return finish("export.py command line")


if __name__ == "__main__":
    sys.exit(main())
