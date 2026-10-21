#!/usr/bin/env python3
"""Rellena las plantillas de winget y Scoop con version + SHA256 del exe.
Uso: python prepare_packaging.py Non-Synapse-Mouse.exe 1.3.0 [--out salida]"""
import sys, re, hashlib, datetime, json, pathlib

def main(argv):
    if len(argv) < 3:
        print(__doc__); return 2
    exe, ver = pathlib.Path(argv[1]), argv[2]
    out = pathlib.Path(argv[argv.index("--out")+1]) if "--out" in argv else pathlib.Path("out")
    if not exe.is_file(): print("No existe", exe); return 1
    if not re.fullmatch(r"\d+\.\d+\.\d+", ver): print("Version invalida:", ver); return 1
    sha = hashlib.sha256(exe.read_bytes()).hexdigest().upper()
    vals = {"{{VERSION}}": ver, "{{SHA256}}": sha, "{{DATE}}": datetime.date.today().isoformat()}
    tpl = pathlib.Path(__file__).parent / "templates"
    wdir = out / "winget" / "manifests" / "d" / "Damnedapa" / "NonSynapseMouse" / ver
    wdir.mkdir(parents=True, exist_ok=True)
    for f in sorted(tpl.iterdir()):
        t = f.read_text(encoding="utf-8")
        for k, v in vals.items(): t = t.replace(k, v)
        if "{{" in t: print("Placeholder sin rellenar en", f.name); return 1
        if f.name == "scoop.json":
            json.loads(t.replace("$version", "x"))
            (out / "scoop").mkdir(parents=True, exist_ok=True)
            (out / "scoop" / "non-synapse-mouse.json").write_text(t, encoding="utf-8")
        else:
            (wdir / f.name).write_text(t, encoding="utf-8")
    print("SHA256:", sha); print("Salida en", out.resolve()); return 0

if __name__ == "__main__": sys.exit(main(sys.argv))
