import sys; sys.path.insert(0, __file__.rsplit("/", 1)[0])
from harness import *
from PIL import Image, ImageGrab
OUT="/home/claude/work/tests/final"; os.makedirs(OUT, exist_ok=True)
def drv(root, api, m):
    pump(root, 1.0)
    for x in root.winfo_children():
        if x.winfo_class()=="Toplevel" and not x.overrideredirect(): x.destroy()
    api["_hide_batt_popup"]()
    pump(root, 1.0)
    api["verified"][0] = True; api["render_profiles"]()
    api["apply_color"]([0,255,0]); api["blink_warned"][0] = True
    m.batt = (74, False); api["do_read_battery"]()
    api["_hide_batt_popup"]()
    api["log"]("Profile 2 -> 800 DPI")
    api["log"]("Sniper on -> 400 DPI"); api["log"]("Sniper released -> 800 DPI")
    for pg in ("profiles","lighting","buttons","settings","log","about"):
        api["show_page"](pg); pump(root, 0.4); shot(root, f"{OUT}/v13_{pg}.png")
    shot(root, f"{OUT}/screenshot.png") if False else None
    api["show_page"]("profiles"); pump(root, 0.3); shot(root, f"{OUT}/screenshot.png")
    # ES
    api["set_language"]("es"); pump(root, 0.3)
    for pg in ("profiles","buttons","settings"):
        api["show_page"](pg); pump(root, 0.4); shot(root, f"{OUT}/v13_es_{pg}.png")
    api["set_language"]("en"); pump(root, 0.3)
    # bienvenida
    d = api["show_welcome"](); pump(root, 0.5); root.update()
    x,y,w,h = d.winfo_rootx(), d.winfo_rooty(), d.winfo_width(), d.winfo_height()
    ImageGrab.grab(bbox=(x-1,y-1,x+w+1,y+h+1), xdisplay=os.environ["DISPLAY"]).save(f"{OUT}/v13_welcome.png"); d.destroy()
    d = api["show_whats_new"](); pump(root, 0.5); root.update()
    x,y,w,h = d.winfo_rootx(), d.winfo_rooty(), d.winfo_width(), d.winfo_height()
    ImageGrab.grab(bbox=(x-1,y-1,x+w+1,y+h+1), xdisplay=os.environ["DISPLAY"]).save(f"{OUT}/v13_whatsnew.png"); d.destroy()
    # popups
    def pop(name, pct, chg, kind):
        api["show_batt_popup"](pct, chg, kind); pump(root, 0.4)
        tw = api["batt_win"][0]
        x,y,w,h = tw.winfo_rootx(), tw.winfo_rooty(), tw.winfo_width(), tw.winfo_height()
        ImageGrab.grab(bbox=(x-1,y-1,x+w+1,y+h+1), xdisplay=os.environ["DISPLAY"]).save(f"{OUT}/pop_{name}.png"); api["_hide_batt_popup"]()
    pop("normal",74,False,"open"); pop("low",15,False,"low"); pop("crit",8,False,"low"); pop("charging",45,True,"open"); pop("full",100,True,"full")
    ims=[Image.open(f"{OUT}/pop_{n}.png") for n in ("normal","low","crit","charging","full")]
    W=sum(i.width for i in ims[:3])+40; sheet=Image.new("RGB",(W+10, max(i.height for i in ims)*2+30),(32,32,32))
    x=10
    for i in ims[:3]: sheet.paste(i,(x,10)); x+=i.width+10
    x=10
    for i in ims[3:]: sheet.paste(i,(x,ims[0].height+20)); x+=i.width+10
    sheet.save(f"{OUT}/v13_battery_popups.png")
    # ventana minima
    root.geometry("800x600"); pump(root, 0.8); api["show_page"]("buttons"); pump(root,0.4); shot(root, f"{OUT}/v13_min_buttons.png")
run(drv)
