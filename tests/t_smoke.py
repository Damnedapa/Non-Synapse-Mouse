import sys; sys.path.insert(0, __file__.rsplit("/", 1)[0])
from harness import *
OUT = "/home/claude/work/tests/out"; os.makedirs(OUT, exist_ok=True)

def drv(root, api, m):
    pump(root, 2.5)
    print("lang:", api["lang"][0], "| size:", root.winfo_width(), "x", root.winfo_height())
    print("connected:", api["state_conn"][0])
    tops = [w for w in root.winfo_children() if w.winfo_class() == "Toplevel"]
    print("toplevels:", len(tops))
    for pg in ("profiles", "lighting", "buttons", "settings", "log", "about"):
        api["show_page"](pg); pump(root, 0.4); shot(root, f"{OUT}/smoke_{pg}.png")
    errs = [l for l in log_text(api).splitlines() if "[ERROR]" in l or "Traceback" in l]
    print("errors in log:", errs)

r = run(drv)
print(r)
