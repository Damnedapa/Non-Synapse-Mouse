import sys; sys.path.insert(0, __file__.rsplit("/", 1)[0])
from harness import *
json.dump({"last_version": nsm.APP_VERSION, "welcomed": True, "profiles":[800,1600,3200,6400,12000]}, open(nsm.CONFIG_PATH,"w"))
def D(root, api, m):
    pump(root, 2.0)
    print("scale", round(api["SCALE"],2), "geom", root.geometry(), "screen", root.winfo_screenwidth(), root.winfo_screenheight())
    for k in api["PAGES"]:
        api["show_page"](k); pump(root, 0.7)
        outer = api["PAGES"][k]
        sb = [c for c in outer.winfo_children() if c.winfo_class() == "TScrollbar"]
        cv = [c for c in outer.winfo_children() if c.winfo_class() == "Canvas"]
        body = cv[0].winfo_children()[0] if cv and cv[0].winfo_children() else None
        print(f"  {k:9s} scrollbar={'YES' if sb and sb[0].winfo_ismapped() else 'no '}  need={body.winfo_reqheight() if body else '-'} have={cv[0].winfo_height() if cv else '-'}")
run(D)
