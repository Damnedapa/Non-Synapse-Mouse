# -*- coding: utf-8 -*-
"""Arnes con el raton SIMULADO a nivel de protocolo (ver sim.py): el programa
usa su RazerMouse y su ButtonListener de verdad."""
import os, sys, time, json, tempfile, importlib.util, threading, traceback
os.environ["NSM_TEST_API"] = "1"
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from sim import SimMouse, SimHid
SRC = os.environ.get("NSM_SRC", os.path.join(HERE, "..", "Non_Synapse_Mouse.py"))
TMP = tempfile.mkdtemp(prefix="nsm_sim_")
spec = importlib.util.spec_from_file_location("nsm", SRC)
nsm = importlib.util.module_from_spec(spec); sys.modules["nsm"] = nsm; spec.loader.exec_module(nsm)
nsm.CONFIG_DIR = TMP
nsm.CONFIG_PATH = os.path.join(TMP, "razer_presets.json")
nsm.LEGACY_CONFIG_PATH = os.path.join(TMP, "legacy.json")
nsm.hid = SimHid

# pystray: menus reales, icono falso
import types as _types
_base = "/usr/local/lib/python3.12/dist-packages/pystray"
_pkg = _types.ModuleType("pystray"); _pkg.__path__ = [_base]; sys.modules["pystray"] = _pkg
_sp = importlib.util.spec_from_file_location("pystray._base", _base + "/_base.py")
_b = importlib.util.module_from_spec(_sp); sys.modules["pystray._base"] = _b; _sp.loader.exec_module(_b)
class FakeIcon:
    def __init__(self, name, icon=None, title=None, menu=None): self.title, self.menu = title, menu
    def run_detached(self): pass
    def stop(self): pass
    def update_menu(self): pass
_pkg.Menu, _pkg.MenuItem, _pkg.Icon = _b.Menu, _b.MenuItem, FakeIcon

# Captura de TODAS las excepciones: callbacks de Tk y otros hilos
ERRORS = []
import tkinter
def _tk_exc(self, exc, val, tb):
    ERRORS.append("TK: " + "".join(traceback.format_exception(exc, val, tb)))
tkinter.Tk.report_callback_exception = _tk_exc
_old_hook = threading.excepthook
def _th_exc(args):
    ERRORS.append("THREAD: " + "".join(traceback.format_exception(args.exc_type, args.exc_value, args.exc_traceback)))
threading.excepthook = _th_exc

_orig_mainloop = tkinter.Tk.mainloop


def write_cfg(d):
    with open(nsm.CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(d, f)


def run(driver, sim, argv=None):
    SimHid.sim = sim
    result = {"ok": True, "err": None}
    def patched(self):
        def go():
            try:
                driver(self, nsm._TEST_API, sim)
            except Exception:
                result["ok"] = False; result["err"] = traceback.format_exc()
            try: nsm._TEST_API["quit_app"]()
            except Exception:
                try: self.destroy()
                except Exception: pass
        self.after(300, go)
        _orig_mainloop(self)
    tkinter.Tk.mainloop = patched
    sys.argv = ["nsm"] + (argv or [])
    nsm.run_gui()
    tkinter.Tk.mainloop = _orig_mainloop
    return result


def pump(root, secs):
    end = time.time() + secs
    while time.time() < end:
        root.update(); time.sleep(0.01)


def wait_for(root, cond, secs=10.0):
    end = time.time() + secs
    while time.time() < end:
        root.update()
        try:
            if cond(): return True
        except Exception:
            pass
        time.sleep(0.02)
    return False


def logtext(api):
    return api["logbox"].get("1.0", "end")
