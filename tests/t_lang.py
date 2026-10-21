import sys; sys.path.insert(0, __file__.rsplit("/", 1)[0])
from harness import *
R=[]
def ck(n,c): R.append(bool(c)); print(("PASS " if c else "FAIL ")+n)
def cfg(): return json.load(open(nsm.CONFIG_PATH, encoding="utf-8"))
base={"lang":"es","last_version":nsm.APP_VERSION,"welcomed":True}
json.dump(base, open(nsm.CONFIG_PATH,"w"))
def A(root,api,m):
    pump(root,1.5); ck("old saved 'es' resets to en once", api["lang"][0]=="en" and cfg()["lang"]=="en")
    api["set_language"]("es"); pump(root,0.3)
def B(root,api,m):
    pump(root,1.5); ck("user's later choice 'es' is kept", api["lang"][0]=="es")
run(A); run(B); print(f"{sum(R)}/{len(R)}")
