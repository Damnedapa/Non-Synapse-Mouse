import sys; sys.path.insert(0, __file__.rsplit("/", 1)[0])
from harness import *
RES=[]
def check(n,c,i=""):
    RES.append(bool(c)); print(("PASS " if c else "FAIL ")+n+(f"  [{i}]" if (i and not c) else ""))
def dialogs(root):
    return [w for w in root.winfo_children() if w.winfo_class()=="Toplevel" and not w.overrideredirect()]
def cfg(): return json.load(open(nsm.CONFIG_PATH, encoding="utf-8"))

def A(root, api, m):
    pump(root, 2.0)
    check("A: welcome on first run", len(dialogs(root)) == 1)
    p = cfg(); check("A: welcomed + last_version saved", p.get("welcomed") and p.get("last_version") == nsm.APP_VERSION, p)
    root.geometry("950x720+70+60"); pump(root, 1.3)
    check("A: geometry saved", cfg().get("win_geom", [0])[0] == 950, cfg().get("win_geom"))
    api["set_language"]("es"); pump(root, 0.2)
def B(root, api, m):
    pump(root, 2.0)
    check("B: no dialog when nothing new", len(dialogs(root)) == 0, len(dialogs(root)))
    check("B: window restored to saved size", (root.winfo_width(), root.winfo_height()) == (950, 720), (root.winfo_width(), root.winfo_height()))
    check("B: language ES remembered", api["lang"][0] == "es")
def C(root, api, m):
    pump(root, 2.0)
    d = dialogs(root); check("C: what's new after update", len(d) == 1, len(d))
    check("C: stored new version", cfg().get("last_version") == nsm.APP_VERSION)
def D(root, api, m):
    pump(root, 2.0)
    check("D: --minimized shows no dialog", len(dialogs(root)) == 0)
    check("D: ...and keeps old version for later", cfg().get("last_version") == "1.2.0")

run(A)
run(B)
p = cfg(); p["last_version"] = "1.2.0"; json.dump(p, open(nsm.CONFIG_PATH, "w"))
run(C)
p = cfg(); p["last_version"] = "1.2.0"; json.dump(p, open(nsm.CONFIG_PATH, "w"))
run(D, argv=["--minimized"])
print(f"{sum(RES)}/{len(RES)}")
