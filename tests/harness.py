# -*- coding: utf-8 -*-
"""Arnes de pruebas: carga el programa con un raton y un escucha de botones
FALSOS, abre la interfaz real en un servidor X virtual y ejecuta un guion."""
import os, sys, time, json, tempfile, importlib.util, threading, traceback

os.environ["NSM_TEST_API"] = "1"
HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.environ.get("NSM_SRC", os.path.join(HERE, "..", "Non_Synapse_Mouse.py"))
TMP = tempfile.mkdtemp(prefix="nsm_test_")

spec = importlib.util.spec_from_file_location("nsm", SRC)
nsm = importlib.util.module_from_spec(spec)
sys.modules["nsm"] = nsm
spec.loader.exec_module(nsm)
nsm.CONFIG_DIR = TMP
nsm.CONFIG_PATH = os.path.join(TMP, "razer_presets.json")
nsm.LEGACY_CONFIG_PATH = os.path.join(TMP, "legacy.json")


class FakeMouse(nsm.RazerMouse):
    def __init__(self):
        super().__init__()
        self.batt = (74, False)
        self.dpi = 800
        self.mode = 3
        self.calls = []          # (t, nombre, args...)
        self.fail_nostore = False
        self.fail_all = False
        self.reject_status = False   # el LED contesta 'fallo' (3) a NOSTORE

    def connect(self, model, log=lambda s: None):
        self.dev = object(); self.model = model; self.pid = 0x007B
        self.tx_cache = {0x00: 0xFF}
        return True
    def close(self): self.dev = None
    def get_firmware(self): return (1, 7)
    def get_battery(self):
        if self.fail_all: raise RuntimeError("x")
        return self.batt
    def get_dpi(self):
        if self.fail_all: raise RuntimeError("x")
        return (self.dpi, self.dpi)
    def set_dpi(self, x, y=None, persist=True):
        self.calls.append((time.time(), "dpi", x, persist)); self.dpi = x; return 2, (x, x)
    def set_device_mode(self, m): self.mode = m; self.calls.append((time.time(), "mode", m)); return 2
    def get_device_mode(self): return self.mode
    def set_poll_rate(self, hz): return 2
    def set_color(self, r, g, b, store=True):
        if not store and self.fail_nostore: raise RuntimeError("no soportado")
        self.calls.append((time.time(), "color", (r, g, b), store)); return 3 if (self.reject_status and not store) else 2
    def set_light_off(self, store=True):
        if not store and self.fail_nostore: raise RuntimeError("no soportado")
        self.calls.append((time.time(), "off", store)); return 2
    def set_brightness(self, p): self.calls.append((time.time(), "bright", p)); return 2


class FakeListener:
    last = None
    def __init__(self, pid, on_press, on_other=None, on_release=None):
        self.on_press, self.on_other, self.on_release = on_press, on_other, on_release
        FakeListener.last = self
    def start(self): return 1
    def alive(self): return True
    def stop(self): pass


# pystray: clases de menu REALES (sin backend grafico) + Icon falso
import types as _types, importlib.util as _iu
_base = "/usr/local/lib/python3.12/dist-packages/pystray"
_pkg = _types.ModuleType("pystray"); _pkg.__path__ = [_base]; sys.modules["pystray"] = _pkg
_sp = _iu.spec_from_file_location("pystray._base", _base + "/_base.py")
_b = _iu.module_from_spec(_sp); sys.modules["pystray._base"] = _b; _sp.loader.exec_module(_b)


class FakeIcon:
    last = None
    def __init__(self, name, icon=None, title=None, menu=None):
        self.name, self.icon, self.title, self.menu = name, icon, title, menu
        self.running = False; self.menu_updates = 0
        FakeIcon.last = self
    def run_detached(self): self.running = True
    def stop(self): self.running = False
    def update_menu(self): self.menu_updates += 1


_pkg.Menu, _pkg.MenuItem, _pkg.Icon = _b.Menu, _b.MenuItem, FakeIcon

nsm.RazerMouse = FakeMouse
nsm.ButtonListener = FakeListener

import tkinter
_orig_mainloop = tkinter.Tk.mainloop


def run(driver, argv=None):
    """Lanza la GUI y ejecuta driver(root, api, mouse) dentro del bucle de Tk."""
    result = {"ok": True, "err": None}

    def patched(self):
        def go():
            try:
                driver(self, nsm._TEST_API, nsm._TEST_API["mouse"])
            except Exception:
                result["ok"] = False; result["err"] = traceback.format_exc()
            try:
                nsm._TEST_API["quit_app"]()
            except Exception:
                try: self.destroy()
                except Exception: pass
        self.after(400, go)
        _orig_mainloop(self)
    tkinter.Tk.mainloop = patched
    sys.argv = ["nsm"] + (argv or [])
    nsm.run_gui()
    tkinter.Tk.mainloop = _orig_mainloop
    return result


def pump(root, secs):
    end = time.time() + secs
    while time.time() < end:
        root.update()
        time.sleep(0.02)


def shot(root, path):
    from PIL import ImageGrab
    root.update_idletasks(); root.update()
    x, y, w, h = root.winfo_rootx(), root.winfo_rooty(), root.winfo_width(), root.winfo_height()
    ImageGrab.grab(bbox=(x, y, x + w, y + h), xdisplay=os.environ.get("DISPLAY")).save(path)


def shot_screen(root, path):
    from PIL import ImageGrab
    root.update()
    ImageGrab.grab(xdisplay=os.environ.get("DISPLAY")).save(path)


def log_text(api):
    return api["logbox"].get("1.0", "end")
