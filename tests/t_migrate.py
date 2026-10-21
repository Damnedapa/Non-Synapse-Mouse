import sys; sys.path.insert(0, __file__.rsplit("/", 1)[0])
from harness import *
R=[]
def ck(n,c,i=""): R.append(bool(c)); print(("PASS " if c else "FAIL ")+n+(f"  [{i}]" if not c else ""))
# configuracion de la v1.0.0: junto al programa, con los presets de DPI y el seguimiento
json.dump({"dpi_presets": [450, 900, 1800, 3600, 7200], "tracking": True, "last_model": "Razer Viper Ultimate",
           "lang": "es", "led_color": [255, 0, 0], "poll_rate": 1000}, open(nsm.LEGACY_CONFIG_PATH, "w"))
if os.path.exists(nsm.CONFIG_PATH): os.remove(nsm.CONFIG_PATH)
def D(root, api, m):
    pump(root, 1.5)
    ck("from 1.0: DPI presets become the 5 profiles", api["profiles"] == [450, 900, 1800, 3600, 7200], api["profiles"])
    ck("from 1.0: model remembered", api["model_var"].get() == "Razer Viper Ultimate")
    ck("from 1.0: language reset to English once", api["lang"][0] == "en")
    ck("from 1.0: LED colour kept", api["led_color"][0] == [255, 0, 0])
    d = [w for w in root.winfo_children() if w.winfo_class()=="Toplevel" and not w.overrideredirect()]
    def walk(w):
        for c in w.winfo_children():
            yield c; yield from walk(c)
    txt = " ".join(str(x.cget("text")) for x in walk(d[0]) if x.winfo_class() == "Label") if d else ""
    ck("from 1.0: shows What's new (not the first-run welcome)", len(d) == 1 and "What's new" in txt, txt[:80])
    ck("from 1.0: new config written to the new place", os.path.exists(nsm.CONFIG_PATH))
r = run(D)
if not r["ok"]: print(r["err"])
print(f"{sum(R)}/{len(R)}")
