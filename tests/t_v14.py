import sys; sys.path.insert(0, __file__.rsplit("/", 1)[0])
from harness import *
R=[]
def ck(n,c,i=""): R.append(bool(c)); print(("PASS " if c else "FAIL ")+n+(f" [{i}]" if not c else ""))
def walk(w):
    for c in w.winfo_children():
        yield c; yield from walk(c)
# remapeo "disponible" (en Linux no lo esta): basta con fingirlo
nsm.SoftRemapper.supported = staticmethod(lambda: True)
nsm.SoftRemapper.start = lambda self: True
nsm.SoftRemapper.stop = lambda self: None
opened = []
import webbrowser; webbrowser.open_new = lambda u: opened.append(u)
json.dump({"last_version": nsm.APP_VERSION, "welcomed": True, "lang_en_default": True,
           "buttons_seen": [0x50], "soft_remap": False}, open(nsm.CONFIG_PATH,"w"))
def combos(box): return [w for w in walk(box) if w.winfo_class()=="TCombobox"]
def A(root, api, m):
    pump(root, 1.5); api["_hide_batt_popup"]()
    api["show_page"]("buttons"); pump(root, 0.4)
    wc = combos(api["win_rows"])
    ck("windows rows greyed while remap off", wc and all(str(c.cget("state"))=="disabled" for c in wc), [str(c.cget("state")) for c in wc])
    ck("note shown next to the header", api["win_note_lbl"].winfo_ismapped())
    api["soft_var"].set(True); pump(root, 0.3)
    wc = combos(api["win_rows"])
    ck("windows rows active with remap on", wc and all(str(c.cget("state"))=="readonly" for c in wc))
    ck("note hidden with remap on", not api["win_note_lbl"].winfo_ismapped())
    mc = combos(api["mouse_rows"])
    on = api["ctrl_on"][0]
    ck("mouse rows follow control mode", mc and all((str(c.cget("state"))=="readonly") == bool(on) for c in mc), (on, [str(c.cget("state")) for c in mc]))
    api["soft_var"].set(False); api["release_control"](announce=False); api["render_profiles"](); pump(root, 0.3)
    ck("sniper greyed when remap and control are off", str(api["sn_en"].cget("state"))=="disabled")
    mc = combos(api["mouse_rows"])
    ck("mouse rows greyed without control mode", mc and all(str(c.cget("state"))=="disabled" for c in mc))
    # registro siempre en ingles
    api["set_language"]("es"); pump(root, 0.2)
    m.batt = (55, False); api["do_read_battery"](); pump(root, 0.3)
    lt = api["logbox"].get("1.0", "end")
    ck("log stays in English after switching to ES", "Battery" in lt and "Batería" not in lt, lt[-300:])
    api["set_language"]("en")
    # ko-fi en la barra lateral
    kn = api["kofi_nav"]
    kn.winfo_children()[-1].event_generate("<Button-1>"); pump(root, 0.2)
    ck("sidebar Ko-fi opens the page", opened and "ko-fi.com" in opened[-1], opened)
    # ventana al minimo: nada se pisa en la barra lateral
    root.geometry(f"{root.minsize()[0]}x{root.minsize()[1]}"); pump(root, 0.8)
    top_bottom = api["nav_top"].winfo_rooty() + api["nav_top"].winfo_height()
    lang_top = api["lang_switch"].frame.winfo_rooty()
    k_bottom = kn.winfo_rooty() + kn.winfo_height()
    win_bottom = root.winfo_rooty() + root.winfo_height()
    ck("min size: sidebar items don't overlap", top_bottom <= lang_top, (top_bottom, lang_top))
    ck("min size: Ko-fi fully visible", k_bottom <= win_bottom, (k_bottom, win_bottom))
    shot(root, "out/v14_min_sidebar.png")
    # reinicio para el tema
    calls = []
    import subprocess as sp
    orig = sp.Popen
    sp.Popen = lambda args, **kw: calls.append((args, kw))
    try:
        api["restart_app"]()
    finally:
        sp.Popen = orig
    ck("restart relaunches with --restarted", calls and calls[0][0][-1] == "--restarted", calls)
    ck("restart asks PyInstaller for a clean process", calls and calls[0][1]["env"].get("PYINSTALLER_RESET_ENVIRONMENT") == "1")
r = run(A)
if not r["ok"]: print(r["err"])
print(f"{sum(R)}/{len(R)}")
