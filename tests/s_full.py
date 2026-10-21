# -*- coding: utf-8 -*-
"""Simulaciones de uso real con el raton simulado a nivel de protocolo.
Cada escenario arranca el programa de cero con su configuracion."""
import sys; sys.path.insert(0, __file__.rsplit("/", 1)[0])
from simharness import *
import random

R = []
def ck(n, c, i=""):
    R.append(bool(c)); print(("PASS " if c else "FAIL ") + n + (f"  [{i}]" if not c else ""), flush=True)

BASE = {"last_version": nsm.APP_VERSION, "welcomed": True, "lang_en_default": True,
        "control_verified": True, "profiles": [400, 800, 1600, 3200, 6400], "active_profile": 1,
        "batt_alert": True, "batt_full": True}
ONLY = set(sys.argv[1:])


def scenario(name):
    def deco(fn):
        if ONLY and name not in ONLY:
            return fn
        print(f"--- {name}", flush=True)
        n_err = len(ERRORS)
        fn()
        new = ERRORS[n_err:]
        ck(f"{name}: no exceptions (Tk callbacks / threads)", not new, new[:1])
        return fn
    return deco


def errors_in_log(api):
    return [l for l in logtext(api).splitlines() if "[ERROR]" in l or "Traceback" in l]


# ---------------------------------------------------------------------------
@scenario("control")
def _():
    write_cfg(dict(BASE))
    sim = SimMouse(seed=11)
    def drv(root, api, sim):
        ck("control: connects and takes control", wait_for(root, lambda: api["ctrl_on"][0] and sim.mode == 3, 8))
        ck("control: active profile applied to the mouse", wait_for(root, lambda: sim.dpi[0] == 800, 4), sim.dpi)
        for k in range(7):
            sim.press(0x50); pump(root, 0.25)
        want = [400, 800, 1600, 3200, 6400][(1 + 7) % 5]
        ck("control: 7 profile presses land on the right profile", wait_for(root, lambda: sim.dpi[0] == want, 3), (sim.dpi, want))
        ck("control: app and mouse agree", api["current"][0] == (1 + 7) % 5)
        ck("control: switching never writes the mouse's memory", sim.flash_writes == 0, sim.flash_writes)
        sim.press(0x21); pump(root, 0.4)          # DPI- = perfil anterior
        ck("control: DPI-down goes back one profile", wait_for(root, lambda: api["current"][0] == (1 + 6) % 5, 2))
        # pulsaciones muy rapidas
        start = api["current"][0]
        for k in range(20):
            sim.press(0x50, hold=0.01); time.sleep(0.02)
        pump(root, 1.5)
        ck("control: 20 fast presses, no lost presses", api["current"][0] == (start + 20) % 5, (api["current"][0], (start + 20) % 5))
        ck("control: final DPI matches profile", sim.dpi[0] == api["profiles"][api["current"][0]], (sim.dpi, api["current"][0]))
        ck("control: log has no errors", not errors_in_log(api), errors_in_log(api)[:2])
    r = run(drv, sim); ck("control: driver ran", r["ok"], r["err"])
    ck("control: on exit the mouse is back to normal mode", sim.mode == 0, sim.mode)


@scenario("noise")
def _():
    write_cfg(dict(BASE))
    sim = SimMouse(seed=5)
    sim.stale_p, sim.empty_p, sim.latency = 0.3, 0.1, 0.01
    def drv(root, api, sim):
        ck("noise: connects through a noisy receiver", wait_for(root, lambda: api["ctrl_on"][0] and sim.mode == 3, 12))
        seen_batt = set()
        for k in range(10):
            sim.busy_n = random.Random(k).randrange(0, 4)
            sim.press(0x50); pump(root, 0.35)
            if api["state_batt"][0]: seen_batt.add(api["state_batt"][0])
        pump(root, 1.5)
        ck("noise: profile still right after 10 presses", api["current"][0] == (1 + 10) % 5, api["current"][0])
        ck("noise: DPI on the mouse is right", wait_for(root, lambda: sim.dpi[0] == api["profiles"][api["current"][0]], 6), sim.dpi)
        api["refresh_battery"](); pump(root, 3)
        ck("noise: battery never wrong", all(b == (74, False) for b in seen_batt | ({api["state_batt"][0]} if api["state_batt"][0] else set())), seen_batt)
        ck("noise: still connected (no false disconnects)", api["state_conn"][0] is not None and "Disconnected" not in logtext(api))
        ck("noise: log has no errors", not errors_in_log(api), errors_in_log(api)[:2])
    r = run(drv, sim); ck("noise: driver ran", r["ok"], r["err"])


@scenario("garbage")
def _():
    write_cfg(dict(BASE))
    sim = SimMouse(seed=8)
    def drv(root, api, sim):
        wait_for(root, lambda: api["ctrl_on"][0], 8)
        sim.garbage_p = 0.15
        for k in range(8):
            sim.press(0x50); pump(root, 0.3)
            api["refresh_battery"]()
        pump(root, 2)
        sim.garbage_p = 0.0
        pump(root, 4)
        b = api["state_batt"][0]
        ck("garbage: battery shown is real or nothing", b in (None, (74, False)), b)
        ck("garbage: mouse DPI ends matching the profile", wait_for(root, lambda: sim.dpi[0] == api["profiles"][api["current"][0]], 8), (sim.dpi, api["current"][0]))
    r = run(drv, sim); ck("garbage: driver ran", r["ok"], r["err"])


@scenario("unplug")
def _():
    write_cfg(dict(BASE))
    sim = SimMouse(seed=2)
    def drv(root, api, sim):
        wait_for(root, lambda: api["ctrl_on"][0], 8)
        sim.press(0x50); pump(root, 0.5)
        cur = api["current"][0]
        sim.plugged = False
        ck("unplug: detected as disconnected", wait_for(root, lambda: api["state_conn"][0] is None, 25))
        ck("unplug: no battery shown while disconnected", api["state_batt"][0] is None)
        pump(root, 3)
        sim.plugged = True; sim.mode = 0; sim.dpi = (800, 800)
        ck("unplug: reconnects by itself", wait_for(root, lambda: api["state_conn"][0] is not None, 15))
        ck("unplug: takes control again", wait_for(root, lambda: api["ctrl_on"][0] and sim.mode == 3, 8))
        ck("unplug: keeps the same profile and reapplies it", wait_for(root, lambda: api["current"][0] == cur and sim.dpi[0] == api["profiles"][cur], 6), (api["current"][0], cur, sim.dpi))
        ck("unplug: battery back", wait_for(root, lambda: api["state_batt"][0] == (74, False), 8), api["state_batt"][0])
        ck("unplug: log has no errors", not errors_in_log(api), errors_in_log(api)[:2])
    r = run(drv, sim); ck("unplug: driver ran", r["ok"], r["err"])


@scenario("sleep")
def _():
    write_cfg(dict(BASE))
    sim = SimMouse(seed=4)
    def drv(root, api, sim):
        wait_for(root, lambda: api["ctrl_on"][0], 8)
        sim.timeout_until = time.time() + 12           # el raton se duerme 12 s
        pump(root, 13)
        lt = logtext(api)
        ck("sleep: a sleeping mouse is not 'disconnected'", "Disconnected" not in lt, lt[-300:])
        ck("sleep: no 0 % while sleeping", api["state_batt"][0] in (None, (74, False)), api["state_batt"][0])
        sim.mode = 0                                    # al despertar ha vuelto a modo normal
        ck("sleep: control comes back after waking", wait_for(root, lambda: sim.mode == 3, 10))
        sim.press(0x50); pump(root, 0.6)
        ck("sleep: profile button works after waking", sim.dpi[0] == api["profiles"][api["current"][0]], sim.dpi)
    r = run(drv, sim); ck("sleep: driver ran", r["ok"], r["err"])


@scenario("battery")
def _():
    write_cfg(dict(BASE))
    sim = SimMouse(seed=6)
    sim.batt_raw = int(0.93 * 255)
    def drv(root, api, sim):
        wait_for(root, lambda: api["state_batt"][0] is not None, 10)
        pump(root, 0.5); api["_hide_batt_popup"]()          # el aviso de "al abrir"
        shown = []
        orig = api["show_batt_popup"]
        pops = []
        # cada lectura: bajar 1 % y leer
        for pct in range(92, 0, -1):
            sim.batt_raw = int(round(pct * 255 / 100.0))
            api["refresh_battery"]()
            shown.append(api["state_batt"][0][0] if api["state_batt"][0] else None)
            w = api["batt_win"][0]
            if w is not None and w.winfo_exists() and w.winfo_ismapped():
                pops.append(api["state_batt"][0][0]); api["_hide_batt_popup"]()
            root.update()
        ck("battery: every reading shown as it is", shown == list(range(92, 0, -1)), [x for x in zip(shown, range(92, 0, -1)) if x[0] != x[1]][:5])
        want = [90, 80, 70, 60, 50, 40, 30, 20, 15, 10, 8, 6, 5, 4, 3, 2, 1]
        ck("battery: alerts exactly at 90..1", pops == want, pops)
        # carga hasta el 100 %: aviso de carga completa
        sim.charging = True
        for pct in [2] + list(range(10, 101, 10)):
            sim.batt_raw = int(round(pct * 255 / 100.0)); api["refresh_battery"](); root.update()
        w = api["batt_win"][0]
        ck("battery: full-charge pop-up", w is not None and w.winfo_ismapped())
        ck("battery: charging readings follow", api["state_batt"][0] == (100, True), api["state_batt"][0])
        api["_hide_batt_popup"]()
        # salto raro de verdad (receptor): 100 -> 40 de golpe, luego vuelve a 100
        sim.charging = False; sim.batt_raw = 255; api["refresh_battery"]()
        sim.batt_raw = int(0.40 * 255); api["refresh_battery"](); root.update()
        ck("battery: a single odd jump is not shown", api["state_batt"][0] == (100, False), api["state_batt"][0])
        sim.batt_raw = 255; api["refresh_battery"](); root.update()
        ck("battery: back to normal", api["state_batt"][0] == (100, False))
        # salto real que se mantiene: se acepta al confirmarse
        sim.batt_raw = int(0.40 * 255)
        ck("battery: a real jump is accepted once confirmed", wait_for(root, lambda: api["state_batt"][0] == (40, False), 12), api["state_batt"][0])
    r = run(drv, sim); ck("battery: driver ran", r["ok"], r["err"])


@scenario("sniper")
def _():
    cfg = dict(BASE); cfg["button_map"] = {str(0x22): "sniper"}; cfg["buttons_seen"] = [0x50, 0x22]
    cfg["sniper_dpi"] = 450
    write_cfg(cfg)
    sim = SimMouse(seed=9)
    def drv(root, api, sim):
        wait_for(root, lambda: api["ctrl_on"][0], 8); pump(root, 0.5)
        sim.events.put(bytes([0x04, 0x22] + [0] * 14))      # mantener
        ck("sniper: DPI drops while held", wait_for(root, lambda: sim.dpi[0] == 450, 3), sim.dpi)
        sim.events.put(bytes([0x04, 0x22, 0x50] + [0] * 13))   # cambia de perfil sin soltar
        pump(root, 0.6)
        ck("sniper: profile change while held keeps the sniper DPI", sim.dpi[0] == 450, sim.dpi)
        sim.events.put(bytes([0x04] + [0] * 15))              # soltar todo
        ck("sniper: releases to the NEW profile", wait_for(root, lambda: sim.dpi[0] == api["profiles"][api["current"][0]] and api["current"][0] == 2, 3), (sim.dpi, api["current"][0]))
        for k in range(15):                                  # machacar el boton
            sim.events.put(bytes([0x04, 0x22] + [0] * 14)); time.sleep(0.02)
            sim.events.put(bytes([0x04] + [0] * 15)); time.sleep(0.02)
        pump(root, 1.0)
        ck("sniper: after mashing, back to the profile DPI", wait_for(root, lambda: sim.dpi[0] == api["profiles"][api["current"][0]], 3), sim.dpi)
        ck("sniper: never writes memory", sim.flash_writes == 0, sim.flash_writes)
    r = run(drv, sim); ck("sniper: driver ran", r["ok"], r["err"])


@scenario("blink")
def _():
    cfg = dict(BASE); cfg.update({"led_on": True, "led_color": [10, 200, 30], "profile_blink": True})
    write_cfg(cfg)
    sim = SimMouse(seed=10)
    def drv(root, api, sim):
        wait_for(root, lambda: api["ctrl_on"][0], 8); pump(root, 0.5)
        stores0 = sim.led["stores"]
        sim.press(0x50); pump(root, 0.2)
        ck("blink: pulses sent with NOSTORE", wait_for(root, lambda: sim.led["nostores"] >= 4, 4), sim.led)
        pump(root, 1.5)
        ck("blink: LED restored to the user's colour", sim.led["rgb"] == (10, 200, 30) and sim.led["effect"] == 1, sim.led)
        ck("blink: no memory writes", sim.led["stores"] == stores0, (stores0, sim.led["stores"]))
        # parpadeos encadenados
        for k in range(6):
            sim.press(0x50, hold=0.02); time.sleep(0.05)
        pump(root, 3)
        ck("blink: after rapid changes the LED ends in the user's colour", sim.led["rgb"] == (10, 200, 30) and sim.led["effect"] == 1, sim.led)
        # LED apagado: el parpadeo vuelve a apagado
        api["led_var"].set(False); pump(root, 0.5)
        sim.press(0x50); pump(root, 2)
        ck("blink: LED off stays off afterwards", sim.led["effect"] == 0, sim.led)
    r = run(drv, sim); ck("blink: driver ran", r["ok"], r["err"])


@scenario("compat")
def _():
    write_cfg(dict(BASE))
    sim = SimMouse(seed=12)
    sim.listener_ok = False
    def drv(root, api, sim):
        ck("compat: falls back to compatibility mode", wait_for(root, lambda: api["state_conn"][0] and not api["ctrl_on"][0] and "compat" in api["mode_var"].get().lower() or "compat" in api["mode_var"].get().lower(), 10), api["mode_var"].get())
        ck("compat: mouse left in normal mode", sim.mode == 0)
        sim.onboard = [400, 800, 1600, 3200, 6400]; sim.onboard_i = 1; sim.dpi = (800, 800)
        pump(root, 2)
        sim.press(0x50)                          # el raton cambia solo: 1600
        ck("compat: detects the profile from the DPI", wait_for(root, lambda: api["current"][0] == 2, 6), api["current"][0])
        ck("compat: never writes memory", sim.flash_writes == 0)
    r = run(drv, sim); ck("compat: driver ran", r["ok"], r["err"])


@scenario("badconfig")
def _():
    with open(nsm.CONFIG_PATH, "w", encoding="utf-8") as f:
        f.write('{"profiles": [1, "x", null], "lang": 7, "theme": "nope", "win_geom": "big", "led_color": "red", ')
    sim = SimMouse(seed=13)
    def drv(root, api, sim):
        ck("badconfig: starts with a broken config file", wait_for(root, lambda: api["state_conn"][0] is not None, 10))
        pump(root, 1)
    r = run(drv, sim); ck("badconfig: driver ran", r["ok"], r["err"])
    weird = {"profiles": [0, 0, 0, 0, 0], "lang": "xx", "theme": 5, "theme_mode": None, "win_geom": [1, 2],
             "led_color": [999, -5, "a"], "active_profile": 99, "sniper_dpi": "fast", "button_map": {"abc": 5},
             "soft_map": [], "buttons_seen": "x", "led_bright": "lots", "profile_blink": "yes", "last_page": 3}
    write_cfg(weird)
    def drv2(root, api, sim):
        ck("badconfig: starts with nonsense values", wait_for(root, lambda: api["state_conn"][0] is not None, 10))
        for pg in ("profiles", "lighting", "buttons", "settings", "log", "about"):
            api["show_page"](pg); pump(root, 0.2)
        sim.press(0x50); pump(root, 0.5)
    r = run(drv2, SimMouse(seed=14)); ck("badconfig: nonsense values handled", r["ok"], (r["err"] or "")[-800:])


@scenario("monkey")
def _():
    write_cfg(dict(BASE))
    sim = SimMouse(seed=21)
    sim.stale_p, sim.empty_p = 0.15, 0.05
    def walk(w):
        for c in w.winfo_children():
            yield c; yield from walk(c)
    def drv(root, api, sim):
        wait_for(root, lambda: api["ctrl_on"][0], 10)
        rng = random.Random(77)
        texts = ["", "abc", "-5", "0", "99", "100", "800", "99999999", "1e3", " 1600 ", "١٢٣", "#zzzzzz", "#00ff00"]
        t_end = time.time() + 45
        acts = 0
        import tkinter as tk
        from tkinter import ttk
        while time.time() < t_end:
            pg = rng.choice(["profiles", "lighting", "buttons", "settings", "about", "log"])
            api["show_page"](pg); root.update()
            page = api["PAGES"][pg]
            ws = [w for w in walk(page) if w.winfo_ismapped()]
            if not ws: continue
            w = rng.choice(ws); cls = w.winfo_class()
            try:
                if cls == "Entry" and str(w.cget("state")) == "normal":
                    w.delete(0, "end"); w.insert(0, rng.choice(texts)); w.event_generate("<Return>"); w.event_generate("<FocusOut>")
                elif cls == "TButton":
                    txt = str(w.cget("text"))
                    if any(k in txt for k in ("Restart", "Reiniciar", "Write", "Grabar", "Download", "Descargar", "Report", "Reportar", "Check for", "Buscar", "Open", "Abrir", "Source", "OpenRazer")):
                        continue                         # navegador / reinicio / asistente: aparte
                    w.invoke()
                elif cls == "Canvas":
                    x = rng.randrange(1, max(2, w.winfo_width())); y = rng.randrange(1, max(2, w.winfo_height()))
                    w.event_generate("<Button-1>", x=x, y=y); w.event_generate("<ButtonRelease-1>", x=x, y=y)
                elif cls == "Label":
                    w.event_generate("<Button-1>")
            except tk.TclError:
                pass
            acts += 1
            # cerrar dialogos que se hayan abierto
            for t in root.winfo_children():
                if t.winfo_class() == "Toplevel" and not t.overrideredirect():
                    try: t.destroy()
                    except Exception: pass
            api["picker_win"][0] = None
            if rng.random() < 0.15: sim.press(0x50, hold=0.01)
            if rng.random() < 0.05: api["set_language"](rng.choice(["es", "en"]))
            root.update()
        pump(root, 2)
        print(f"   monkey actions: {acts}")
        ck("monkey: still connected and in control", api["state_conn"][0] is not None)
        ck("monkey: mouse DPI matches the active profile or sniper", wait_for(root, lambda: sim.dpi[0] == (api["profiles"][api["current"][0]] or sim.dpi[0]), 6), (sim.dpi, api["current"][0], api["profiles"]))
        errs = errors_in_log(api)
        ck("monkey: log has no errors", not errs, errs[:3])
        ck("monkey: profiles still valid", all(p is None or (100 <= p <= 20000) for p in api["profiles"]), api["profiles"])
    r = run(drv, sim); ck("monkey: driver ran", r["ok"], r["err"])


print(f"\nTOTAL {sum(R)}/{len(R)}   uncaught={len(ERRORS)}")
for e in ERRORS[:5]:
    print(e[:1500])
