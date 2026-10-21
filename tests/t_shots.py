import sys; sys.path.insert(0, __file__.rsplit("/", 1)[0])
from harness import *
from PIL import Image, ImageGrab
OUT="/home/claude/work/tests/out"; os.makedirs(OUT, exist_ok=True)
def drv(root, api, m):
    pump(root, 2.0)
    for x in root.winfo_children():
        if x.winfo_class()=="Toplevel" and not x.overrideredirect(): x.destroy()
    api["_hide_batt_popup"]()
    def pop(name, pct, chg, kind):
        api["show_batt_popup"](pct, chg, kind); pump(root, 0.4)
        tw = api["batt_win"][0]
        x,y,w,h = tw.winfo_rootx(), tw.winfo_rooty(), tw.winfo_width(), tw.winfo_height()
        ImageGrab.grab(bbox=(x-2,y-2,x+w+2,y+h+2), xdisplay=os.environ["DISPLAY"]).save(f"{OUT}/pop_{name}.png")
        api["_hide_batt_popup"]()
    pop("normal", 74, False, "open"); pop("low", 15, False, "low"); pop("crit", 8, False, "low")
    pop("charging", 45, True, "open"); pop("full", 100, True, "full")
    # aviso de perfil (abajo a la derecha)
    api["show_toast"](2); pump(root, 0.4)
    tw = api["toast_win"][0]
    x,y,w,h = tw.winfo_rootx(), tw.winfo_rooty(), tw.winfo_width(), tw.winfo_height()
    ImageGrab.grab(bbox=(x-2,y-2,x+w+2,y+h+2), xdisplay=os.environ["DISPLAY"]).save(f"{OUT}/pop_toast.png")
    # ventana principal
    api["verified"][0]=True; api["render_profiles"](); api["show_page"]("profiles"); pump(root,0.4)
    shot(root, f"{OUT}/main_profiles.png")
    # mosaico de popups
    names=["normal","low","crit","charging","full","toast"]
    ims=[Image.open(f"{OUT}/pop_{n}.png") for n in names]
    W=max(i.width for i in ims); H=sum(i.height+10 for i in ims)
    sheet=Image.new("RGB",(W+20,H+10),(20,20,20)); y=10
    for i in ims: sheet.paste(i,(10,y)); y+=i.height+10
    sheet.save(f"{OUT}/pop_sheet.png")
run(drv)
