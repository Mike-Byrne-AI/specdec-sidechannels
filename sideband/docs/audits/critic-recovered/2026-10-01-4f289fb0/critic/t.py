# Independent recompute of the bigram smoke from its state file. No import of the tool or the frozen instrument.
import json
import numpy as np
S = r"C:/Users/x/bigram_smoke.json"
rows = []
print("keys", {r["key"] for r in rows}, "depths", {r["depth"] for r in rows})
for (a, B) in {}:
    name = f"{a}|B={B}"
