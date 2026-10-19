import json, sys
R="C:/Users/<user>/Desktop/Research/sideband/"
def load(h):
    return json.load(open(R+"results/real/prefetch_strat_s3%s.json"%h,encoding="utf-8"))
def tw(h):
    return json.load(open(R+"results/real/prefetch_bigram_s3%s.json"%h,encoding="utf-8"))
P={"p":load(""),"r":load("_r")}
T={"p":tw(""),"r":tw("_r")}
def D(h,name,B,scope):
    x=P[h]["conclusion"]["deltas"]["%s|B=%d|%s"%(name,B,scope)]
    return x["delta"],x["lo"],x["hi"]
def TB(h,arm,B,scope):
    x=P[h]["conclusion"]["tables"]["%s|B=%d|%s"%(arm,B,scope)]["all"]
    return x["point"],x["ci_lo"],x["ci_hi"]
def reading(d,lo,hi):
    if lo>0 and d>=0.05: return "SIGNAL"
    if hi<0: return "NEGATIVE"
    return "NOT-SHOWN"
def f4(x): return "%+.4f"%x
def fmt(t): return "%s [%s, %s]"%(f4(t[0]),f4(t[1]),f4(t[2]))
