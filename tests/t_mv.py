"""Modo Mediavida (secreto, sin conexion): Konami -> se activa y reinicia;
al volver suena la intro y sale el aviso. Logo en la barra lateral, Spy y
Hilo en Mediavida, modo oscuro en gris, y que nunca toque la red."""
import sys; sys.path.insert(0, __file__.rsplit("/", 1)[0])
from harness import *
import webbrowser, urllib.request
HERE = os.path.dirname(os.path.abspath(__file__))
SP = os.environ.get("SHOTS", os.path.join(HERE, "out")); os.makedirs(SP, exist_ok=True)
R = []
def ck(n, c, i=""): R.append(bool(c)); print(("PASS " if c else "FAIL ") + n + (f"  [{i}]" if not c else ""), flush=True)

calls = {"play": [], "open": [], "net": [], "popen": []}
nsm.IntroSound.play = lambda self, path, volume=650: calls["play"].append(path) or True
webbrowser.open_new = lambda u: calls["open"].append(u)
_real_urlopen = urllib.request.urlopen
def _no_net(req, *a, **k):
    u = getattr(req, "full_url", req)
    calls["net"].append(u)
    raise OSError("network disabled in tests")
urllib.request.urlopen = _no_net
nsm.subprocess.Popen = lambda *a, **k: calls["popen"].append(a)

def cfg(): return json.load(open(nsm.CONFIG_PATH, encoding="utf-8"))
BASE = {"last_version": nsm.APP_VERSION, "welcomed": True, "lang_en_default": True, "lang": os.environ.get("LANGX", "es"),
        "control_verified": True, "profiles": [600, 1200, 1600, 1800, 2000], "active_profile": 3, "led_on": True,
        "win_geom": [1110, 900, 40, 40], "check_updates": False}
def setcfg(**kw):
    d = dict(BASE); d.update(kw); json.dump(d, open(nsm.CONFIG_PATH, "w"))
def walk(w):
    for c in w.winfo_children():
        yield c; yield from walk(c)
def labels(w): return [c.cget("text") for c in walk(w) if c.winfo_class() == "Label"]
def konami(root, api, extra=()):
    root.focus_force(); pump(root, 0.2)
    w = api["PAGES"]["profiles"]
    for k in list(extra) + ["Up", "Up", "Down", "Down", "Left", "Right", "Left", "Right", "b", "a"]:
        w.event_generate("<KeyPress>", keysym=k, when="tail"); root.update()
    pump(root, 0.4)
def settle(root, api, m):
    m.batt = (51, False); m.dpi = 1800
    pump(root, 1.3); api["_hide_batt_popup"]()
    api["verified"][0] = True; api["current"][0] = 3; api["refresh_battery"](); api["render_profiles"](); pump(root, 0.4)

# ---------------------------------------------------------------- A: bloqueado
setcfg()
def A(root, api, m):
    settle(root, api, m)
    ck("A: secret theme hidden in the list", "mediavida" not in api["_theme_keys"])
    ck("A: no Mediavida links", api["mv_nav"] is None and "mv_spy" not in api)
    ck("A: normal mouse icon", bool(api["dev_cv"].find_withtag("mouse")) and not api["dev_cv"].find_withtag("mvlogo"))
    # durante el asistente de grabado no hace nada
    api["wizard_active"][0] = True
    konami(root, api)
    ck("A: ignored while burning profiles", not cfg().get("mv_unlocked") and not calls["popen"])
    api["wizard_active"][0] = False
    # casi: le falta la A final
    w = api["PAGES"]["profiles"]
    for k in ["Up", "Up", "Down", "Down", "Left", "Right", "Left", "Right", "b", "x"]:
        w.event_generate("<KeyPress>", keysym=k, when="tail"); root.update()
    pump(root, 0.3)
    ck("A: wrong sequence does nothing", not cfg().get("mv_unlocked") and not calls["popen"])
    konami(root, api, extra=["Up"])                    # con un 'arriba' de mas
    c = cfg()
    ck("A: Konami unlocks and picks the theme", c.get("mv_unlocked") is True and c.get("theme") == "mediavida"
       and c.get("theme_mode") == "dark" and c.get("mv_welcome") is True, c)
    ck("A: restarts to apply it", len(calls["popen"]) == 1 and "--restarted" in calls["popen"][0][0], calls["popen"])
    try: alive = bool(root.winfo_exists())
    except Exception: alive = False
    ck("A: the window closed for the restart", not alive)
    ck("A: no music before the restart (it would be cut)", not calls["play"])
r = run(A); ck("A: ran", r["ok"], r["err"])

# ---------------------------------------------------------------- B: primera vez tras desbloquear
def B(root, api, m):
    settle(root, api, m); pump(root, 0.6)
    ck("B: Mediavida mode active", api["MV_ACTIVE"] and api["THEME_NAME"] == "mediavida")
    ck("B: the intro plays", len(calls["play"]) == 1 and calls["play"][0].endswith("mv_intro.mp3"), calls["play"])
    d = api["mv_dialog"][0]
    ck("B: unlocked notice shown", d is not None and d.winfo_exists())
    t = labels(d)
    ck("B: notice texts", any("desbloqueado" in x or "unlocked" in x for x in t)
       and any("desactivarlo" in x or "turn it off" in x for x in t), t)
    ck("B: notice has the logo", any(c.winfo_class() == "Canvas" and c.find_all() for c in walk(d)))
    btns = [b for b in walk(d) if b.winfo_class() == "TButton"]
    ck("B: single 'Vale' button", len(btns) == 1 and btns[0].cget("text") in ("Vale", "OK"), [b.cget("text") for b in btns])
    ck("B: title fits", d.winfo_width() >= max(c.winfo_reqwidth() for c in walk(d) if c.winfo_class() == "Label"))
    ck("B: welcome flag cleared", "mv_welcome" not in cfg())
    from PIL import ImageGrab
    shot(root, f"{SP}/mv_welcome_full.png")
    ImageGrab.grab(bbox=(d.winfo_rootx(), d.winfo_rooty(), d.winfo_rootx() + d.winfo_width(), d.winfo_rooty() + d.winfo_height()),
                   xdisplay=os.environ["DISPLAY"]).save(f"{SP}/mv_welcome.png")
    btns[0].invoke(); pump(root, 0.3)
    ck("B: 'Vale' closes it", api["mv_dialog"][0] is None and not d.winfo_exists())
    # barra lateral
    cv = api["dev_cv"]
    ck("B: logo instead of the mouse", bool(cv.find_withtag("mvlogo")) and not cv.find_withtag("mouse"))
    ck("B: mouse name and status as usual", api["dev_name"].cget("text") == "Viper Ultimate"
       and "51" in api["dev_sub"].cget("text"), (api["dev_name"].cget("text"), api["dev_sub"].cget("text")))
    kids = api["nav_top"].winfo_children()
    spy = api["mv_spy"]
    ck("B: Spy right below Settings", kids[-1] is spy and spy.winfo_y() > kids[-2].winfo_y())
    spy.winfo_children()[-1].event_generate("<Button-1>"); pump(root, 0.2)
    ck("B: Spy opens mediavida.com/foro/spy", calls["open"] and calls["open"][-1] == "https://www.mediavida.com/foro/spy", calls["open"])
    nav = api["mv_nav"]
    ck("B: thread link above Language", nav is not None and nav.winfo_y() < api["lang_switch"].frame.winfo_y())
    nav.winfo_children()[-1].event_generate("<Button-1>"); pump(root, 0.2)
    ck("B: thread link opens the thread", "739643" in calls["open"][-1], calls["open"])
    # tema
    ck("B: forum colours", api["BG"] == "#0B0A09" and api["ACCENT"] == "#FFA804")
    ck("B: rounded like the basic theme", api["THEMES"]["mediavida"]["shape"] == api["THEMES"]["basic"]["shape"])
    ck("B: theme card shows the logo", api["theme_card"].icon is not None and str(api["theme_card"].icon.cget("image")))
    ck("B: dark mode switch greyed out", not api["dark_tg"].enabled)
    ck("B: no restart card", not api["restart_card"].frame.winfo_ismapped())
    for pg in ("profiles", "lighting", "buttons", "settings", "log", "about"):
        api["show_page"](pg); pump(root, 0.4); shot(root, f"{SP}/mv_{pg}.png")
    # cambiar de tema en Ajustes
    combo = api["theme_combo"]; keys = api["_theme_keys"]
    combo.current(keys.index("basic")); api["_on_theme"](); pump(root, 0.2)
    ck("B: other theme -> dark switch back on", api["dark_tg"].enabled)
    ck("B: other theme -> restart offered", api["restart_card"].frame.winfo_ismapped())
    combo.current(keys.index("mediavida")); api["_on_theme"](); pump(root, 0.2)
    ck("B: back to Mediavida -> greyed again, no restart", not api["dark_tg"].enabled and not api["restart_card"].frame.winfo_ismapped())
    # Konami otra vez: solo musica
    n = len(calls["play"]); konami(root, api)
    ck("B: Konami again just plays the music", len(calls["play"]) == n + 1 and len(calls["popen"]) == 1)
    # sin raton: el texto de siempre, el logo se queda
    m.fail_all = True; api["last_conn_try"][0] = time.time() + 100
    for _ in range(3):
        api["last_mode_check"][0] = 0; api["auto_tick"](); pump(root, 0.5)
    ck("B: disconnected", api["state_conn"][0] is None)
    ck("B: searching text + spinner, logo kept", api["dev_name"].cget("text") == api["tr"]("searching")
       and api["spin_job"][0] is not None and bool(cv.find_withtag("mvlogo")))
    api["show_page"]("profiles"); pump(root, 0.3); shot(root, f"{SP}/mv_searching.png")
    m.fail_all = False; api["last_conn_try"][0] = 0
    for _ in range(6):
        api["auto_tick"](); pump(root, 0.5)
        if api["state_conn"][0]: break
    ck("B: reconnects", bool(api["state_conn"][0]) and api["spin_job"][0] is None)
r = run(B); ck("B: ran", r["ok"], r["err"])

# ---------------------------------------------------------------- C: siguientes arranques
def C(root, api, m):
    n = len(calls["play"]); settle(root, api, m); pump(root, 0.6)
    ck("C: no notice and no music on later starts", api["mv_dialog"][0] is None and len(calls["play"]) == n)
    ck("C: still in Mediavida mode", api["MV_ACTIVE"])
r = run(C); ck("C: ran", r["ok"], r["err"])

# ---------------------------------------------------------------- D: forzar el tema sin desbloquear
setcfg(theme="mediavida")
def D(root, api, m):
    pump(root, 1.0)
    ck("D: secret theme can't be forced from the config file", api["THEME_NAME"] == "basic" and not api["MV_ACTIVE"])
r = run(D); ck("D: ran", r["ok"], r["err"])

# ---------------------------------------------------------------- E: desbloqueado con otro tema
setcfg(mv_unlocked=True, theme="basic", mv_welcome=True)
def E(root, api, m):
    n = len(calls["play"]); settle(root, api, m); pump(root, 0.6)
    ck("E: unlocked + basic theme -> normal look", not api["MV_ACTIVE"] and api["mv_nav"] is None and "mv_spy" not in api)
    ck("E: Mediavida offered in the theme list", "mediavida" in api["_theme_keys"])
    ck("E: theme card keeps the logo", str(api["theme_card"].icon.cget("image")))
    ck("E: dark switch usable", api["dark_tg"].enabled)
    ck("E: no notice without the theme (flag cleaned)", api["mv_dialog"][0] is None and len(calls["play"]) == n and "mv_welcome" not in cfg())
r = run(E); ck("E: ran", r["ok"], r["err"])

# ---------------------------------------------------------------- F: config de la version con red (dev)
setcfg(mv_unlocked=True, theme="mediavida", mv_user="verseker", mv_avatar="C:/x/avatar.gif", mv_checked="ayer")
def F(root, api, m):
    settle(root, api, m)
    c = cfg()
    ck("F: old user/avatar keys dropped, mode kept", api["MV_ACTIVE"] and not any(k in c for k in ("mv_user", "mv_avatar", "mv_checked")), c)
r = run(F); ck("F: ran", r["ok"], r["err"])

# ---------------------------------------------------------------- G: sin el logo (exe mal compilado)
_res_dir = os.path.join(nsm.CONFIG_DIR, "noassets"); os.makedirs(_res_dir, exist_ok=True)
_orig_base = nsm._BASE_DIR; nsm._BASE_DIR = _res_dir
setcfg(mv_unlocked=True, theme="mediavida", mv_welcome=True)
def G(root, api, m):
    settle(root, api, m); pump(root, 0.6)
    ck("G: missing logo -> mouse icon, no crash", bool(api["dev_cv"].find_withtag("mouse")))
    ck("G: notice still opens", api["mv_dialog"][0] is not None)
r = run(G); ck("G: ran", r["ok"], r["err"])
nsm._BASE_DIR = _orig_base

ck("never touched the network", not calls["net"], calls["net"])
print(f"{sum(R)}/{len(R)}")
