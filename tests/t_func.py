import sys, re; sys.path.insert(0, __file__.rsplit("/", 1)[0])
from harness import *
RES = []
def check(name, cond, info=""):
    RES.append(bool(cond)); print(("PASS " if cond else "FAIL ") + name + (f"   [{info}]" if info and not cond else ""))

def dialogs(root):
    out = []
    for w in root.winfo_children():
        if w.winfo_class() == "Toplevel" and not w.overrideredirect():
            out.append(w)
    return out

def labels(w):
    r = []
    for c in w.winfo_children():
        if c.winfo_class() == "Label": r.append(str(c.cget("text")))
        r += labels(c)
    return r

def drv(root, api, m):
    pump(root, 2.2)
    # --- primera ejecucion: bienvenida --------------------------------------------
    d = dialogs(root)
    check("first run shows welcome dialog", len(d) == 1 and any("Welcome" in t for t in labels(d[0])), [labels(x)[:3] for x in d])
    for x in d: x.destroy()
    check("default language is English", api["lang"][0] == "en")
    nb = api["nav_bottom"].pack_slaves()
    check("language switch is the first item of the bottom nav (above Log)", nb and nb[0] is api["lang_switch"].frame)

    # --- paridad de textos ES/EN y claves usadas ----------------------------------------
    L = api["LANG"]
    miss = set(L["es"]) ^ set(L["en"])
    check("ES/EN keys identical", not miss, sorted(miss)[:10])
    src = open(SRC, encoding="utf-8").read()
    used = set(re.findall(r'\btr\(\s*"([a-z0-9_]+)"', src))
    used |= set(re.findall(r'(?:reg_text\([^\n]*?,|title=|desc=|note_key=|placeholder_key=)\s*"([a-z0-9_]+)"', src))
    undefined = sorted(k for k in used if k not in L["es"] or k not in L["en"])
    check("every literal text key exists in both languages", not undefined, undefined[:15])

    # --- cambio de idioma con el interruptor ----------------------------------------------
    sw = api["lang_switch"]; W = api["px"](sw.W)
    sw.cv.event_generate("<Button-1>", x=5, y=10); pump(root, 0.2)
    check("click ES switches to Spanish + saves", api["lang"][0] == "es" and api["presets"]["lang"] == "es")
    navtxt = [t for t in labels(api["nav_top"])]
    check("sidebar retranslated", "Perfiles" in navtxt and "Ajustes" in navtxt, navtxt)
    sw.cv.event_generate("<Button-1>", x=W - 5, y=10); pump(root, 0.2)
    check("click EN switches back", api["lang"][0] == "en")

    # --- bateria ------------------------------------------------------------------------------------
    api["_hide_batt_popup"]()
    def vis():
        tw = api["batt_win"][0]
        return bool(tw is not None and tw.winfo_exists() and tw.state() == "normal")
    def read(pct, chg=False):
        api["_hide_batt_popup"](); m.batt = (pct, chg); api["refresh_battery"](); root.update()
        return vis()
    check("popup appeared when the app opened (first reading)", api["batt_first"][0] is False and api["batt_win"][0] is not None)
    seq = [(74, False), (69, True), (68, False), (59, True), (49, True), (41, False), (40, True), (30, True), (25, False),
           (20, True), (17, False), (15, True), (12, False), (10, True), (9, False), (8, True), (7, False), (6, True),
           (5, True), (4, True), (3, True), (2, True), (1, True), (2, False), (1, False)]
    bad = [(p, exp, got) for (p, exp) in seq for got in [read(p)] if got != exp]
    check("alerts at every threshold, silent in between, no flapping at +-1 %", not bad, bad)
    tw = api["batt_win"][0]
    check("charging resets silently", read(30, True) is False)
    read(100, True); read(100, True)                      # salto grande: se confirma con lecturas seguidas
    check("full charge popup at 100 % charging (after confirming the jump)", read(100, True) is True)
    check("no repeat while still full", read(100, True) is False)
    check("unplugged at 97 -> silent", read(97, False) is False)
    check("then 89 -> alert (re-armed)", read(89, False) is True)
    check("popup shows the level", tw._parts[1].cget("text") == "89 %", tw._parts[1].cget("text"))
    api["batt_alert_var"].set(False)
    check("alerts off -> no popup", read(79, False) is False)
    api["batt_alert_var"].set(True)
    api["test_batt_popup"](); check("test button shows popup", vis())
    api["_hide_batt_popup"]()
    # los umbrales de la logica pura
    bl = nsm.BATT_ALERT_LEVELS
    check("threshold list as requested", bl == (90, 80, 70, 60, 50, 40, 30, 20, 15, 10, 8, 6, 5, 4, 3, 2, 1))
    m.batt = (74, False)

    # --- sniper ---------------------------------------------------------------------------------------
    L_ = FakeListener.last
    api["button_map"][0x20] = "sniper"
    prof_dpi = api["profiles"][api["current"][0]]
    m.calls.clear(); L_.on_press(0x20); pump(root, 0.5)
    check("sniper press (side button reported by mouse) drops DPI", m.dpi == api["sniper_dpi"][0] == 400, m.dpi)
    api["last_mode_check"][0] = 0; api["auto_tick"](); pump(root, 0.3)
    check("auto-tick does not undo the sniper", m.dpi == 400, m.dpi)
    api["step_profile"](+1); pump(root, 0.3)
    check("changing profile while sniper keeps sniper DPI", m.dpi == 400, m.dpi)
    newp = api["profiles"][api["current"][0]]
    L_.on_release(0x20); pump(root, 0.5)
    check("release restores the NEW profile's DPI", m.dpi == newp, (m.dpi, newp))
    api["exec_action"]("sniper", True, True); pump(root, 0.4)
    check("soft button sniper press", m.dpi == 400)
    api["exec_action"]("sniper", False, True); pump(root, 0.4)
    check("soft button sniper release", m.dpi == newp, m.dpi)
    api["exec_action"]("sniper", True, False); pump(root, 0.3)
    check("sniper ignored on buttons without release (wheel)", m.dpi == newp)
    api["sn_var"].set("1200"); api["save_sniper"](); api["exec_action"]("sniper", True, True); pump(root, 0.4)
    check("sniper DPI is configurable", m.dpi == 1200 and api["presets"]["sniper_dpi"] == 1200, m.dpi)
    api["exec_action"]("sniper", False, True); pump(root, 0.4)
    api["sn_var"].set("50"); api["save_sniper"]()
    check("invalid sniper DPI rejected", api["sniper_dpi"][0] == 1200 and api["sn_var"].get() == "1200")
    def combos(w):
        r = []
        for c in w.winfo_children():
            if c.winfo_class() == "TCombobox": r.append(c)
            r += combos(c)
        return r
    api["build_btn_rows"](); root.update()
    rows = api["win_rows"].winfo_children()
    has = [any("Sniper" in v for v in combos(r)[0].cget("values")) for r in rows]
    names = [labels(r)[0] for r in rows]
    check("sniper offered on wheel click / side buttons only", has == [True, False, False, True, True], list(zip(names, has)))

    # --- parpadeo del logo ----------------------------------------------------------------------------
    m.calls.clear(); api["apply_profile"](1); pump(root, 1.5)
    col = [c for c in m.calls if c[1] in ("color", "off")]
    check("blink skipped while LED state is unknown (+ log)", not col and "Blink skipped" in log_text(api), col)
    api["apply_color"]([255, 0, 0]); pump(root, 0.3); m.calls.clear()
    api["apply_profile"](2); pump(root, 1.6)
    col = [c for c in m.calls if c[1] in ("color", "off")]
    exp = [((47, 134, 255)), (0, 0, 0)] * 3 + [(255, 0, 0)]
    got = [c[2] for c in col]
    check("blink = 3 pulses in profile colour then restore (all NOSTORE)", got == exp and all(c[3] is False for c in col), got)
    t = [c[0] for c in col]; check("blink lasts < 1.5 s", t[-1] - t[0] < 1.5, t[-1] - t[0])
    m.calls.clear(); api["apply_profile"](1); api["apply_profile"](3); pump(root, 2.0)
    col = [c for c in m.calls if c[1] in ("color", "off")]
    check("rapid profile changes: ends restored, no mix-up", col and col[-1][2] == (255, 0, 0) and col.count(col[-1]) >= 1 and sum(1 for c in col if c[2] == (0, 242, 225)) <= 3, [c[2] for c in col])
    # LED apagado
    api["led_var"].set(False); pump(root, 0.3); m.calls.clear()
    api["apply_profile"](0); pump(root, 1.6)
    col = [c for c in m.calls if c[1] in ("color", "off")]
    check("LED off: blinks then returns to OFF (no flash write)", col and col[-1][1] == "off" and col[-1][2] is False and api["presets"]["led_on"] is False, [c[1:] for c in col][-3:])
    api["led_var"].set(True); pump(root, 0.3)
    api["blink_var"].set(False); m.calls.clear(); api["apply_profile"](1); pump(root, 1.0)
    check("blink option off -> no blink", not [c for c in m.calls if c[1] in ("color", "off")])
    m.calls.clear(); api["blink_for"](1, force=True); pump(root, 1.5)
    check("Test button blinks even if option off", len([c for c in m.calls if c[1] == "color"]) >= 6)
    api["blink_var"].set(True)
    api["bright_var"].set(0); m.calls.clear(); api["apply_profile"](2); pump(root, 0.8)
    check("brightness 0 -> no blink", not [c for c in m.calls if c[1] in ("color", "off")])
    api["bright_var"].set(100)
    m.fail_nostore = True; m.calls.clear(); api["apply_profile"](1); pump(root, 1.0)
    check("LED rejecting NOSTORE -> blink disabled gracefully + log", api["blink_ok"][0] is False and "temporary colours" in log_text(api))
    m.fail_nostore = False; api["blink_ok"][0] = True
    m.reject_status = True; m.calls.clear(); api["apply_profile"](1); pump(root, 1.0)
    check("LED answering 'fail' status to NOSTORE -> blink disabled too", api["blink_ok"][0] is False)
    m.reject_status = False; api["blink_ok"][0] = True

    # --- tema / oscuro ---------------------------------------------------------------------------------
    api["dark_var"].set(False); pump(root, 0.2)
    check("light switch stays off and asks to restart", api["dark_var"].get() is False and api["restart_card"].frame.winfo_ismapped())
    api["dark_var"].set(True); pump(root, 0.2)
    check("basic theme has dark + light with the same keys", set(api["THEMES"]["basic"]["dark"]) == set(api["THEMES"]["basic"]["light"]) == set(api["THEME_COLOR_KEYS"]))

    # --- bandeja --------------------------------------------------------------------------------------------
    check("tray tip contains profile + battery", "Profile" in api["tray_tip"]() and "Battery" in api["tray_tip"](), api["tray_tip"]())
    if api["TRAY_OK"]:
        api["to_tray"]()
        pump(root, 0.5)
        icon = api["tray"][0]
        items = list(icon.menu.items)
        txt = [getattr(i, "text", "-") for i in items]
        print("   tray menu:", txt)
        sub = [i for i in items if getattr(i, "submenu", None)]
        subitems = list(sub[0].submenu.items) if sub else []
        check("tray menu has status + 5 profile items", len(subitems) == 5, len(subitems))
        check("exactly one profile checked and enabled", sum(1 for i in subitems if i.checked) == 1 and all(i.enabled for i in subitems))
        stat = [i for i in items if getattr(i, "text", "") and not getattr(i, "submenu", None) and i.text not in ("Show", "Quit", "- - - -")]
        check("tray status line is disabled text", stat and stat[0].enabled is False and "Profile" in stat[0].text, [(getattr(i,'text',''), i.enabled) for i in items])
        check("tray has Show (default) and Quit", "Show" in txt and "Quit" in txt, txt)
        before = icon.menu_updates; api["apply_profile"](4, announce=False); pump(root, 0.3)
        check("menu refreshed on profile change + tooltip updated", icon.menu_updates > before and "Profile 5" in icon.title, icon.title)
        subitems = list(sub[0].submenu.items)
        check("checked profile follows the active one", [i.checked for i in subitems] == [False, False, False, False, True])
        # clic en un perfil del menu = cambiar de perfil
        subitems[1](icon); pump(root, 0.6)
        check("clicking a profile in the tray switches to it", api["current"][0] == 1, api["current"][0])
        api["ctrl_on"][0] = False
        check("profile items disabled outside control mode", all(not i.enabled for i in sub[0].submenu.items))
        api["ctrl_on"][0] = True
        api["set_language"]("es"); pump(root, 0.2)
        check("tray menu follows language", "Mostrar" in [getattr(i, "text", "") for i in icon.menu.items]); api["set_language"]("en")
        api["show_window"](); pump(root, 0.3)
    else:
        print("   (pystray no disponible en este entorno)")

    # --- ventana: tamano/posicion recordados --------------------------------------------------------------
    root.geometry("930x700+60+50"); pump(root, 1.4)
    g = api["presets"].get("win_geom")
    check("window size/position saved", g and g[0] == 930 and g[1] == 700, g)
    check("resizable", root.resizable() == (True, True))

    # --- novedades --------------------------------------------------------------------------------------------------
    api["show_whats_new"](); pump(root, 0.3)
    d = dialogs(root)
    check("what's new dialog (EN)", d and any(f"What's new in v{nsm.APP_VERSION}" in t for t in labels(d[-1])), [labels(x)[:2] for x in d])
    for x in d: x.destroy()
    api["set_language"]("es"); api["show_whats_new"](); pump(root, 0.3); d = dialogs(root)
    check("what's new dialog (ES)", d and any(f"Novedades de la v{nsm.APP_VERSION}" in t for t in labels(d[-1])))
    for x in d: x.destroy()
    api["set_language"]("en")
    # --- desconexion con sniper activo -------------------------------------------------------------------------
    api["exec_action"]("sniper", True, True); pump(root, 0.4)
    m.fail_all = True; api["last_conn_try"][0] = time.time() + 100      # sin reconexion automatica durante la prueba
    for _ in range(3):
        api["last_mode_check"][0] = 0; api["auto_tick"](); pump(root, 0.5)
    check("disconnect clears sniper state", api["sniper_state"]["active"] is False and api["state_conn"][0] is None)
    errs = [l for l in log_text(api).splitlines() if "[ERROR]" in l]
    check("no [ERROR] lines in log", not errs, errs[:3])

r = run(drv)
print(r)
print(f"\n{sum(RES)}/{len(RES)} checks passed")
