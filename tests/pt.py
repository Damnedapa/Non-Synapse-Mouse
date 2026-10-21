import sys, types
import importlib.util
base = "/usr/local/lib/python3.12/dist-packages/pystray"
pkg = types.ModuleType("pystray"); pkg.__path__ = [base]; sys.modules["pystray"] = pkg
spec = importlib.util.spec_from_file_location("pystray._base", base + "/_base.py")
b = importlib.util.module_from_spec(spec); sys.modules["pystray._base"] = b; spec.loader.exec_module(b)
Menu, MenuItem = b.Menu, b.MenuItem
m = Menu(MenuItem(lambda i: 'x', None, enabled=False), Menu.SEPARATOR,
         MenuItem(lambda i: 'P', Menu(lambda: (MenuItem(lambda i,k=k:f'p{k}', lambda ic,it:None, checked=lambda i,k=k: k==1, radio=True, enabled=lambda i: True) for k in range(3)))))
print([getattr(i,'text',None) for i in m.items])
sub=[i for i in m.items if getattr(i,'submenu',None)][0]
print([(i.text,i.checked,i.enabled) for i in sub.submenu.items])
