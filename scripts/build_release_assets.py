#!/usr/bin/env python3
"""Create portable Skill ZIPs from the same maintained source."""
import hashlib
import sys
import subprocess
import zipfile
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]

def build():
    subprocess.run([sys.executable, str(ROOT/"scripts/generate_skill_entries.py"), "--check"], check=True, cwd=ROOT)
    version=(ROOT/"VERSION").read_text().strip()
    output=ROOT/"dist"
    output.mkdir(exist_ok=True)
    common=[ROOT/"VERSION", ROOT/"LICENSE"]
    common += [p for folder in ("references", "templates") for p in (ROOT/folder).rglob("*") if p.is_file()]
    common += [ROOT/"scripts"/name for name in ("probe_system.sh", "probe_camera.py", "probe_uart.py", "probe_gpio.py", "probe_rknn.py", "run_baseline.sh")]
    for platform, entry in (("codex", "SKILL.md"), ("claude", "claude/SKILL.md"), ("dsh-skill", "dsh/SKILL.md")):
        path=output/f"taishan-rk3566-{platform}-{version}.zip"
        with zipfile.ZipFile(path,"w",compression=zipfile.ZIP_DEFLATED) as z:
            for source in sorted(common+[ROOT/entry]):
                relative="SKILL.md" if source == ROOT/entry else source.relative_to(ROOT).as_posix()
                info=zipfile.ZipInfo("taishan-rk3566/"+relative, date_time=(2026,1,1,0,0,0))
                info.compress_type=zipfile.ZIP_DEFLATED
                info.external_attr=0o100644 << 16
                z.writestr(info, source.read_bytes())
            if platform == "codex":
                info=zipfile.ZipInfo("taishan-rk3566/agents/openai.yaml", date_time=(2026,1,1,0,0,0))
                info.compress_type=zipfile.ZIP_DEFLATED
                info.external_attr=0o100644 << 16
                z.writestr(info, (ROOT/"agents/openai.yaml").read_bytes())
        with zipfile.ZipFile(path) as z:
            assert z.testzip() is None
            assert len(z.namelist()) == len(set(z.namelist()))
        print(f"built {path.name}")
    return output

if __name__ == "__main__":
    output=build()
    sums=[]
    for path in sorted(output.iterdir()):
        if path.suffix in {".zip",".tgz"}:
            sums.append(hashlib.sha256(path.read_bytes()).hexdigest()+"  "+path.name)
    (output/"SHA256SUMS.txt").write_text("\n".join(sums)+"\n",encoding="utf-8")
