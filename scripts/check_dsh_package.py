#!/usr/bin/env python3
"""Check the actual npm archive against the maintained source resources."""
import argparse
import glob
import json
import tarfile
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]

def check(path):
    with tarfile.open(path, "r:gz") as archive:
        files = {m.name: m for m in archive.getmembers() if m.isfile()}
        expected = ["package.json", "VERSION", "LICENSE", "README.md", "cordis.patch.yml", "dsh/index.mjs", "dsh/SKILL.md", "tests/test_probe_camera.py"]
        expected += [p.relative_to(ROOT).as_posix() for folder in ("references", "templates") for p in (ROOT/folder).rglob("*") if p.is_file()]
        expected += ["scripts/" + name for name in ("probe_system.sh", "probe_camera.py", "probe_uart.py", "probe_gpio.py", "probe_rknn.py", "run_baseline.sh")]
        for relative in expected:
            member = files.get("package/" + relative)
            if member is None:
                raise ValueError(f"missing packed resource: {relative}")
            if archive.extractfile(member).read() != (ROOT / relative).read_bytes():
                raise ValueError(f"packed resource differs from source: {relative}")
        extra = set(files) - {"package/" + p for p in expected}
        if extra:
            raise ValueError(f"unexpected packaged files: {sorted(extra)}")
        package = json.loads(archive.extractfile(files["package/package.json"]).read())
        if package["version"] != (ROOT/"VERSION").read_text().strip():
            raise ValueError("packed version mismatch")
    print(f"package verified: {path} ({len(files)} files, byte-identical resources)")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("archives", nargs="+")
    args = parser.parse_args()
    for pattern in args.archives:
        paths = glob.glob(pattern)
        if not paths:
            parser.error(f"no archives match {pattern}")
        for path in paths:
            check(path)
