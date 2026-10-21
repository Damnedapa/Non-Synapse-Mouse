import sys; sys.path.insert(0, __file__.rsplit("/", 1)[0])
from harness import *
MODE=os.environ.get("MODE","dark")
json.dump({"last_version": nsm.APP_VERSION, "welcomed": True, "lang_en_default": True, "theme_mode": MODE,
           "led_color": [255, 0, 0], "led_on": True}, open(nsm.CONFIG_PATH,"w"))
R=[]
def ck(n,c,i=""): R.append(bool(c)); print(("PASS " if c else "FAIL ")+n+(f" [{i}]" if not c else ""))
def walk(w):
    for c in w.winfo_children():
        yield c; yield from walk(c)
def D(root, api, m):
    pump(root, 1.2); api["_hide_batt_popup"]()
    api["show_page"]("lighting"); pump(root, 0.3)
    win = api["open_color_picker"](); pump(root, 0.5)
    from PIL import ImageGrab
    x,y,w,h = win.winfo_rootx(), win.winfo_rooty(), win.winfo_width(), win.winfo_height()
    ent = [e for e in walk(win) if e.winfo_class()=="Entry"][0]
    ck("hex starts at current", ent.get().lower()=="#ff0000", ent.get())
    ent.delete(0,"end"); ent.insert(0,"#00ffff"); pump(root,0.3)
    cvs=[c for c in walk(win) if c.winfo_class()=="Canvas"]
    disc=cvs[0]
    ImageGrab.grab(bbox=(x,y,x+w,y+h), xdisplay=os.environ["DISPLAY"]).save(f"out/picker_{MODE}.png")
    # click on disc: right edge = red
    D_=disc.winfo_width()
    disc.event_generate("<Button-1>", x=D_-12, y=D_//2); pump(root,0.2)
    r_=ent.get().lower(); ck("click right edge -> red", r_[:3]=="#ff" and int(r_[3:5],16)<8 and int(r_[5:7],16)<8, r_)
    disc.event_generate("<Button-1>", x=D_//2, y=D_//2); pump(root,0.2)
    ck("click centre -> white", ent.get().lower()=="#ffffff", ent.get())
    ent.delete(0,"end"); ent.insert(0,"#2f86ff"); pump(root,0.2)
    m.calls.clear()
    btn=[b for b in walk(win) if b.winfo_class()=="TButton" and "Accent" in str(b.cget("style"))][0]
    btn.invoke(); pump(root,0.4)
    ck("apply sends colour", any(c[1]=="color" and c[2]==(0x2f,0x86,0xff) for c in m.calls), m.calls)
    ck("main hex updated", api["hex_var"].get()=="#2f86ff", api["hex_var"].get())
    ck("window closed", not win.winfo_exists())
    shot(root, f"out/v14_{MODE}_lighting_after.png")
run(D); print(f"{sum(R)}/{len(R)}")
