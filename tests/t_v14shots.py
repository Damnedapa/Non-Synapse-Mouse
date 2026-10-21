import sys; sys.path.insert(0, __file__.rsplit("/", 1)[0])
from harness import *
MODE = os.environ.get("MODE", "dark"); THEME = os.environ.get("THEME", "basic"); TAG = os.environ.get("TAG", MODE)
OUT = os.environ.get("OUT", os.path.join(os.path.dirname(os.path.abspath(__file__)), "out")); os.makedirs(OUT, exist_ok=True)
pre = {"last_version": nsm.APP_VERSION, "welcomed": True, "lang_en_default": True, "theme": THEME, "theme_mode": MODE,
       "profiles": [800, 1600, 0, 6400, 12000], "led_on": True}
json.dump(pre, open(nsm.CONFIG_PATH, "w"))
if os.environ.get("THEMEFILE"):
    os.makedirs(os.path.join(nsm.CONFIG_DIR, "themes"), exist_ok=True)
    import shutil; shutil.copy(os.environ["THEMEFILE"], os.path.join(nsm.CONFIG_DIR, "themes", os.path.basename(os.environ["THEMEFILE"])))
PAGES = os.environ.get("PAGES", "profiles,lighting,buttons,settings,log,about").split(",")
def drv(root, api, m):
    pump(root, 1.2)
    api["_hide_batt_popup"]()
    api["verified"][0] = True; api["render_profiles"]()
    pump(root, 0.3)
    for pg in PAGES:
        api["show_page"](pg); pump(root, 0.5); shot(root, f"{OUT}/v14_{TAG}_{pg}.png")
        if pg == "settings":
            outer = api["PAGES"]["settings"]
            cv = [c for c in outer.winfo_children() if c.winfo_class() == "Canvas"][0]
            cv.yview_moveto(1.0); pump(root, 0.4); shot(root, f"{OUT}/v14_{TAG}_settings2.png"); cv.yview_moveto(0)
run(drv)
