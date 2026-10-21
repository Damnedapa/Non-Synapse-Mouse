# -*- coding: utf-8 -*-
"""Mas simulaciones con el raton simulado: asistente de grabado, luces, bandeja,
arranque minimizado, salir a mitad de algo y una prueba larga."""
import sys; sys.path.insert(0, __file__.rsplit("/", 1)[0])
from simharness import *
import random, gc

R = []
def ck(n, c, i=""):
    R.append(bool(c)); print(("PASS " if c else "FAIL ") + n + (f"  [{i}]" if not c else ""), flush=True)
BASE = {"last_version": nsm.APP_VERSION, "welcomed": True, "lang_en_default": True,
        "control_verified": True, "profiles": [400, 800, 1600, 3200, 6400], "active_profile": 1}
ONLY = set(sys.argv[1:])
def scenario(name):
    def deco(fn):
        if ONLY and name not in ONLY: return fn
        print(f"--- {name}", flush=True); n = len(ERRORS); fn()
        ck(f"{name}: no exceptions", len(ERRORS) == n, ERRORS[n:][:1]); return fn
    return deco
def walk(w):
    for c in w.winfo_children():
        yield c; yield from walk(c)
def errs(api): return [l for l in logtext(api).splitlines() if "[ERROR]" in l]


@scenario("wizard")
def _():
    cfg = dict(BASE); cfg["profiles"] = [450, 900, 1800, 3600, 7200]
    write_cfg(cfg)
    sim = SimMouse(seed=31); sim.stale_p = 0.2
    def drv(root, api, sim):
        wait_for(root, lambda: api["ctrl_on"][0], 10)
        api["start_wizard"](); pump(root, 0.5)
        ck("wizard: mouse handed back to its own profiles (normal mode)", sim.mode == 0)
        win = [w for w in root.winfo_children() if w.winfo_class() == "Toplevel" and not w.overrideredirect()][0]
        for n in range(5):
            go = [b for b in walk(win) if b.winfo_class() == "TButton" and "Accent" in str(b.cget("style"))][0]
            sim.onboard_i = n                       # el usuario pone el LED del color que toca
            go.invoke(); pump(root, 0.3)
        ck("wizard: the 5 onboard profiles hold the new DPI", sim.onboard == [450, 900, 1800, 3600, 7200], sim.onboard)
        ck("wizard: exactly 5 memory writes", sim.flash_writes == 5, sim.flash_writes)
        go = [b for b in walk(win) if b.winfo_class() == "TButton" and b.winfo_ismapped()][0]
        go.invoke(); pump(root, 1.0)
        ck("wizard: control taken back after closing", wait_for(root, lambda: api["ctrl_on"][0] and sim.mode == 3, 6))
        ck("wizard: log clean", not errs(api), errs(api)[:2])
    r = run(drv, sim); ck("wizard: driver ran", r["ok"], r["err"])


@scenario("led")
def _():
    write_cfg(dict(BASE))
    sim = SimMouse(seed=32)
    def drv(root, api, sim):
        wait_for(root, lambda: api["state_conn"][0] is not None, 10)
        api["show_page"]("lighting"); pump(root, 0.3)
        api["apply_color"]([255, 0, 128]); pump(root, 0.3)
        ck("led: colour reaches the mouse", sim.led["rgb"] == (255, 0, 128) and sim.led["effect"] == 1, sim.led)
        api["bright_var"].set(40); api["apply_bright"](); pump(root, 0.3)
        ck("led: brightness reaches the mouse", sim.led["bright"] == round(40 / 100 * 255), sim.led["bright"])
        api["led_var"].set(False); pump(root, 0.3)
        ck("led: off", sim.led["effect"] == 0)
        api["led_var"].set(True); pump(root, 0.3)
        ck("led: on again with the last colour", sim.led["effect"] == 1 and sim.led["rgb"] == (255, 0, 128), sim.led)
        win = api["open_color_picker"](); pump(root, 0.3)
        ent = [e for e in walk(win) if e.winfo_class() == "Entry"][0]
        ent.delete(0, "end"); ent.insert(0, "#12ab34"); pump(root, 0.2)
        [b for b in walk(win) if b.winfo_class() == "TButton" and "Accent" in str(b.cget("style"))][0].invoke(); pump(root, 0.3)
        ck("led: picker colour reaches the mouse", sim.led["rgb"] == (0x12, 0xAB, 0x34), sim.led)
        sim.garbage_p = 1.0                                 # el raton contesta basura a todo
        api["apply_color"]([1, 2, 3]); pump(root, 0.3)
        sim.garbage_p = 0.0
        ck("led: a failed command is reported, not crashed", any("[ERROR]" in l or "[!]" in l for l in logtext(api).splitlines()[-3:]))
    r = run(drv, sim); ck("led: driver ran", r["ok"], r["err"])


@scenario("tray")
def _():
    cfg = dict(BASE); cfg["tray"] = True
    write_cfg(cfg)
    sim = SimMouse(seed=33)
    def drv(root, api, sim):
        wait_for(root, lambda: api["ctrl_on"][0], 10); pump(root, 0.5)
        api["to_tray"](); pump(root, 0.3)
        ck("tray: window hidden", root.state() == "withdrawn")
        icon = api["tray"][0]
        ck("tray: icon created", icon is not None)
        menu = icon.menu
        prof = [i for i in menu.items if i.submenu is not None][0]
        sub = list(prof.submenu.items)
        sub[3](icon); pump(root, 0.5)                       # elegir perfil 4 desde la bandeja
        ck("tray: profile switched from the tray", sim.dpi[0] == 3200 and api["current"][0] == 3, (sim.dpi, api["current"][0]))
        sim.press(0x50); pump(root, 0.6)
        ck("tray: profile button keeps working in the tray", sim.dpi[0] == 6400, sim.dpi)
        api["show_window"](); pump(root, 0.3)
        ck("tray: window back", root.state() == "normal")
    r = run(drv, sim); ck("tray: driver ran", r["ok"], r["err"])


@scenario("minimized")
def _():
    cfg = dict(BASE); cfg["tray"] = True; cfg["last_version"] = "1.0.0"
    write_cfg(cfg)
    sim = SimMouse(seed=34)
    def drv(root, api, sim):
        ck("minimized: connects while hidden", wait_for(root, lambda: api["ctrl_on"][0] and sim.mode == 3, 10))
        ck("minimized: starts in the tray", root.state() == "withdrawn")
        dl = [w for w in root.winfo_children() if w.winfo_class() == "Toplevel" and not w.overrideredirect() and w.winfo_ismapped()]
        ck("minimized: no dialogs pop up", not dl)
        sim.press(0x50); pump(root, 0.6)
        ck("minimized: profile button works", sim.dpi[0] == 1600, sim.dpi)
    r = run(drv, sim, argv=["--minimized"]); ck("minimized: driver ran", r["ok"], r["err"])


@scenario("quit_mid")
def _():
    cfg = dict(BASE); cfg.update({"button_map": {str(0x22): "sniper"}, "led_on": True, "led_color": [0, 0, 255]})
    write_cfg(cfg)
    sim = SimMouse(seed=35)
    def drv(root, api, sim):
        wait_for(root, lambda: api["ctrl_on"][0], 10); pump(root, 0.3)
        sim.events.put(bytes([0x04, 0x22] + [0] * 14))    # sniper pulsado
        sim.press(0x50, hold=0.01)                          # y un parpadeo en marcha
        pump(root, 0.15)
        # se cierra el programa con todo a medias (lo hace run() al volver)
    r = run(drv, sim); ck("quit_mid: driver ran", r["ok"], r["err"])
    time.sleep(1.0)
    ck("quit_mid: mouse back in normal mode", sim.mode == 0, sim.mode)
    ck("quit_mid: no memory writes", sim.flash_writes == 0)


@scenario("soak")
def _():
    cfg = dict(BASE); cfg.update({"led_on": True, "led_color": [0, 255, 0], "profile_blink": True,
                                  "button_map": {str(0x22): "sniper"}, "batt_alert": True})
    write_cfg(cfg)
    sim = SimMouse(seed=36); sim.stale_p = 0.1; sim.empty_p = 0.05
    secs = float(os.environ.get("SOAK", "120"))
    def drv(root, api, sim):
        wait_for(root, lambda: api["ctrl_on"][0], 10)
        rng = random.Random(5)
        t0 = time.time(); n_thr0 = threading.active_count(); cache0 = None
        presses = 0; worst = 0.0
        while time.time() - t0 < secs:
            r_ = rng.random()
            if r_ < 0.25: sim.press(0x50, hold=0.02); presses += 1
            elif r_ < 0.30: sim.events.put(bytes([0x04, 0x22] + [0] * 14))
            elif r_ < 0.35: sim.events.put(bytes([0x04] + [0] * 15))
            elif r_ < 0.38: sim.busy_n = rng.randrange(1, 6)
            elif r_ < 0.40: sim.batt_raw = max(3, sim.batt_raw - 1)
            elif r_ < 0.41: sim.timeout_until = time.time() + rng.uniform(0.5, 4)
            elif r_ < 0.43: api["show_page"](rng.choice(["profiles", "lighting", "buttons", "settings", "log"]))
            elif r_ < 0.44: api["refresh_battery"]()
            t = time.time(); root.update(); worst = max(worst, time.time() - t)
            time.sleep(0.05)
            if cache0 is None and time.time() - t0 > 10: cache0 = len(api["_paint_cache"])
        sim.events.put(bytes([0x04] + [0] * 15)); sim.busy_n = 0; sim.timeout_until = 0
        pump(root, 5)
        print(f"   soak {secs:.0f}s: presses={presses} threads {n_thr0}->{threading.active_count()} "
              f"cache {cache0}->{len(api['_paint_cache'])} worst UI freeze {worst*1000:.0f} ms")
        ck("soak: still in control", api["ctrl_on"][0] and sim.mode == 3)
        ck("soak: app and mouse agree at the end", wait_for(root, lambda: sim.dpi[0] == api["profiles"][api["current"][0]], 8),
           (sim.dpi, api["current"][0]))
        b = api["state_batt"][0]
        ck("soak: battery shown matches the mouse", b is None or abs(b[0] - sim.pct()) <= 3, (b, sim.pct()))
        ck("soak: no thread leak", threading.active_count() <= n_thr0 + 2, (n_thr0, threading.active_count()))
        ck("soak: drawing cache stays bounded", len(api["_paint_cache"]) <= (cache0 or 0) + 40, (cache0, len(api["_paint_cache"])))
        ck("soak: UI never froze > 300 ms", worst < 0.3, worst)
        ck("soak: log clean", not errs(api), errs(api)[:3])
        lines = logtext(api).splitlines()
        ck("soak: log size capped", len(lines) <= api["LOG_MAX_LINES"] + 1, len(lines))
        for k in range(2000): api["log"](f"line {k}")
        ck("soak: log trims old lines past the cap", len(logtext(api).splitlines()) <= api["LOG_MAX_LINES"] + 1 and "line 1999" in logtext(api))
    r = run(drv, sim); ck("soak: driver ran", r["ok"], r["err"])

print(f"\nTOTAL {sum(R)}/{len(R)}   uncaught={len(ERRORS)}")
for e in ERRORS[:5]: print(e[:1500])
