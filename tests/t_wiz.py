import sys; sys.path.insert(0, __file__.rsplit("/", 1)[0])
from harness import *
json.dump({"last_version": nsm.APP_VERSION, "welcomed": True, "profiles":[800,1600,3200,6400,12000]}, open(nsm.CONFIG_PATH,"w"))
R=[]
def ck(n,c,i=""): R.append(bool(c)); print(("PASS " if c else "FAIL ")+n+(f" [{i}]" if not c else ""))
def walk(w):
    for c in w.winfo_children():
        yield c; yield from walk(c)
def D(root, api, m):
    pump(root, 1.5)
    api["start_wizard"](); pump(root, 0.6)
    win = [w for w in root.winfo_children() if w.winfo_class()=="Toplevel" and not w.overrideredirect()][0]
    h0 = win.winfo_height(); print("win", win.winfo_width(), h0)
    for n in range(5):
        btns=[b for b in walk(win) if b.winfo_class()=="TButton" and b.winfo_ismapped()]
        go=[b for b in btns if "Accent" in str(b.cget("style"))][0]
        bottom = go.winfo_rooty()+go.winfo_height()-win.winfo_rooty()
        ck(f"step {n+1}: button inside window", bottom <= win.winfo_height(), (bottom, win.winfo_height()))
        ck(f"step {n+1}: height unchanged", win.winfo_height()==h0, win.winfo_height())
        go.invoke(); pump(root, 0.4)
        if n==2: shot(win, "out/wiz_mid.png")
    shot(win, "out/wiz_done.png")
    btns=[b for b in walk(win) if b.winfo_class()=="TButton" and b.winfo_ismapped()]
    ck("done: close button visible", btns and btns[0].winfo_rooty()+btns[0].winfo_height()-win.winfo_rooty() <= win.winfo_height()+1)
    btns[0].invoke(); pump(root,0.5)
run(D); print(f"{sum(R)}/{len(R)}")
