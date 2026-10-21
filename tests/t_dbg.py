import sys; sys.path.insert(0, __file__.rsplit("/", 1)[0])
from harness import *
def drv(root, api, m):
    pump(root, 2.2)
    for x in root.winfo_children():
        if x.winfo_class()=="Toplevel" and not x.overrideredirect(): x.destroy()
    api["exec_action"]("sniper", True, True); pump(root, 0.5)
    print("active:", api["sniper_state"], "dpi", m.dpi, "ctrl_on", api["ctrl_on"][0])
    m.fail_all = True
    for k in range(4):
        api["last_mode_check"][0] = 0; api["auto_tick"](); pump(root, 0.1)
        print(k, "read_fails", api["read_fails"][0], "dev", m.dev is not None, "conn", api["state_conn"][0], api["sniper_state"]["active"])
r = run(drv); print(r)
