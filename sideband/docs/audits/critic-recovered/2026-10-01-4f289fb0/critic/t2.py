pg = {0: 1.0, 1: 2.0}
srt = sorted(pg.items(), key=lambda kv: -kv[1])
print("per-gate gain top 4:", [(g, round(v, 4)) for g, v in srt[:4]], "argmax", srt[0][0])
vt = {"a": {"1.0": 0.5}}
for a, t in vt.items():
    print(" ", a, {k: round(v, 5) for k, v in t.items()})
d, lo, hi = 0.1, 0.0, 0.2
print(f"x {d:+.4f} [{lo:+.4f}, {hi:+.4f}]")
