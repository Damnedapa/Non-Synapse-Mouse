import sys; sys.path.insert(0, __file__.rsplit("/", 1)[0])
from harness import *
def pre():
    json.dump({"tray": True, "last_version": nsm.APP_VERSION, "welcomed": True, "batt_alert": True,
               "profiles": [800,1600,3200,6400,12000]}, open(nsm.CONFIG_PATH, "w"))
pre()
def D(root, api, m):
    pump(root, 3.0)
    print("state", root.state(), "tray", api["tray"][0], "resizable", root.resizable(), "geom", root.geometry(),
          "screen", root.winfo_screenwidth(), root.winfo_screenheight(), "scale", api["SCALE"])
    for k in ("profiles","lighting","buttons","settings","log","about"):
        try: api["show_page"](k)
        except Exception as e: print("skip", k, e); continue
        pump(root, 0.6)
        pg = api["pages"][k] if "pages" in api and k in api["pages"] else None
        print(k, "sb_mapped" , [w.winfo_ismapped() for w in root.winfo_children()[0].winfo_children()][:0])
run(D)
