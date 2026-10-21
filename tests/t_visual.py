import sys; sys.path.insert(0, __file__.rsplit("/", 1)[0])
from harness import *
OUT = "/home/claude/work/tests/out"; os.makedirs(OUT, exist_ok=True)

def drv(root, api, m):
    pump(root, 2.0)
    shot_screen(root, f"{OUT}/v_screen_open.png")        # aviso de bateria + bienvenida
    for w in list(root.winfo_children()):
        if w.winfo_class() == "Toplevel" and w.winfo_ismapped() and not w.overrideredirect():
            w.destroy()
    api["_hide_batt_popup"]()
    # tamano por defecto
    for pg in ("profiles", "lighting", "buttons", "settings", "log", "about"):
        api["show_page"](pg); pump(root, 0.3); shot(root, f"{OUT}/v_{pg}.png")
    # tamano minimo
    root.geometry("800x600"); pump(root, 0.8)
    print("min size now:", root.winfo_width(), root.winfo_height(), "minsize:", root.minsize())
    for pg in ("profiles", "lighting", "buttons", "settings", "about"):
        api["show_page"](pg); pump(root, 0.4); shot(root, f"{OUT}/vmin_{pg}.png")
    # idioma ES
    api["set_language"]("es"); pump(root, 0.3)
    root.geometry("1126x855"); pump(root, 0.5)
    for pg in ("profiles", "settings", "buttons"):
        api["show_page"](pg); pump(root, 0.3); shot(root, f"{OUT}/ves_{pg}.png")
r = run(drv); print(r)
