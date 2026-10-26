import json, sys, hashlib, math
from pathlib import Path
import numpy as np
ROOT = Path("C:/Users/<user>/Desktop/Research/sideband")
REAL = ROOT / "results" / "real"
POPS = {"k3": ("k3_verdict_arm1", "k3_verdict_s1_arm1", "data/prompts_k3_verdict.jsonl"),
        "oq15": ("oq15c_verdict_arm1", "oq15c_verdict_s3_arm1", "data/prompts_oq15_verdict.jsonl")}
BAR, ADV = 0.062, 3.191969887076537 - 3.1322448979591835
SIZES, M = (30, 42, 84, 126, 210), 1000
FAMS = ("instruct", "story", "summarize")
