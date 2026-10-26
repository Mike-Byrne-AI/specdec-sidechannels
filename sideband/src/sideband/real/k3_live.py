"""K-3 Attempt #1 live instrument (stage E; BLUEPRINT arc registration
2026-09-01, freeze pins + stage-E clarifications E1-E11, 2026-09-02).

GPU box. Pieces the extended spec-decode loop (hf_specdec.spec_decode_prompt,
k3=...) consumes:

- LiveShadowTap / LiveNormCatch: harvest-identical capture machinery
  (same HashSketch tables, same per-layer seeds) extended to capture
  EVERY position of the fed delta, because the block anchor — index
  base + accepted count, the position that produced the emitted
  residual-or-bonus token — is known only AFTER the verify loop runs.
  Both are passive hooks: no extra forwards, no RNG (E8 read-only).
- LiveReader: assembles harvest-dtype anchor features (E7) from the
  anchor distribution + captures and runs the exported seed-0 probes
  (E1) for BOTH arms at offsets 2-3; also maps draft tokens to their
  merged-label-space classes for the E2 agreement semantics.
- ByproductRecorder: the E8 per-prompt byproduct log (one npz per
  prompt; raw gitignored, metas committed by the runner).
- K3Config: the bundle spec_decode_prompt takes; validation mirrors the
  registration (probe policies need the reader; recording needs the
  reader; scheduling never coexists with steering).
- load_probe_weights: reads the export tool's npz + meta with the sha
  binding enforced.

Nothing here touches verifier math (D-3) or consumes RNG (D-6).
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from ..scheduler import (TOP_M, LinearProbe, SchedulerPolicy,
                         anchor_free_summaries, probe_input)
from .shadow_telemetry import ShadowTap

PROBE_OFFSETS = (2, 3)
PROBE_ARMS = ("a", "c")


class LiveShadowTap(ShadowTap):
    """ShadowTap variant capturing every position of the fed delta
    (batch-1 only). Sketch tables, per-layer seeds, and top-N semantics
    are inherited unchanged from the harvest tap — only the capture
    window differs, which is exactly what the live-tap fidelity rider
    (E9) measures."""

    def _make_hook(self, name: str):
        import torch

        def hook(_module, inputs):
            a = inputs[0]
            if a.shape[0] != 1:
                raise RuntimeError("LiveShadowTap is batch-1 only")
            imp = a[0].float().abs() * self._col_norms[name]  # (T, d_in)
            k = min(self.top_n, imp.shape[-1])
            top = torch.topk(imp, k=k, dim=-1).indices  # (T, k) unit ids
            self.latest[name] = self._slot_of[name][top]  # (T, k) slot ids

        return hook

    def collect_at(self, pos: int) -> np.ndarray:
        """(L, top_n) sorted-unique -1-padded slot ids at delta position
        `pos` of the last forward. Clears captured state; refuses if a
        tapped layer did not fire or pos is out of the captured range."""
        out = np.full((len(self.layer_names), self.top_n), -1, dtype=np.int16)
        for li, name in enumerate(self.layer_names):
            if name not in self.latest:
                raise RuntimeError(f"tapped layer {name} did not fire since last collect")
            raw = self.latest[name].cpu().numpy()
            if not 0 <= pos < raw.shape[0]:
                raise RuntimeError(f"{name}: anchor position {pos} outside "
                                   f"captured range 0..{raw.shape[0] - 1}")
            u = np.unique(raw[pos])
            out[li, : len(u)] = u.astype(np.int16)
        self.latest = {}
        return out


class LiveNormCatch:
    """Final-norm output at every position of the fed delta (batch-1),
    for the byproduct h_a log (the 2026-09-02 amendment). Passive."""

    def __init__(self, norm_module):
        self.latest = None
        self._handle = norm_module.register_forward_hook(self._hook)

    def _hook(self, _module, _inputs, output):
        if output.shape[0] != 1:
            raise RuntimeError("LiveNormCatch is batch-1 only")
        self.latest = output[0].detach()  # (T, d)

    def collect_at(self, pos: int) -> np.ndarray:
        if self.latest is None:
            raise RuntimeError("norm hook did not fire since last collect")
        if not 0 <= pos < self.latest.shape[0]:
            raise RuntimeError(f"anchor position {pos} outside captured range")
        h = self.latest[pos].float().cpu().numpy().astype(np.float16)
        self.latest = None
        return h

    def close(self) -> None:
        self._handle.remove()


@dataclass
class AnchorRead:
    """One block anchor's read: harvest-dtype summaries + captures +
    both arms' probe outputs at offsets 2-3 (pred = full-label-space
    argmax, conf = max softmax — the frozen signal)."""

    abs_pos: int
    summaries: dict
    slots: np.ndarray             # (L, top_n) int16
    h: np.ndarray                 # (d,) float16
    probe_pred: dict              # arm -> (off2, off3) int
    probe_conf: dict              # arm -> (off2, off3) float
    x: dict = None                # {"a": probe_input(summ), "c": +slots} —
    #                               read-only feature vectors the head arms
    #                               score through (STAGE-C FREEZE); already
    #                               computed for probe inference, now kept.


class LiveReader:
    """Block-anchor reader (E7/E8): deterministic, read-only."""

    def __init__(self, tap: LiveShadowTap, normcatch: LiveNormCatch,
                 bucket_maps: dict[str, np.ndarray], label_map: np.ndarray,
                 n_classes: int, probes: dict[tuple[str, int], LinearProbe],
                 n_slots: int = 512, top_m: int = TOP_M):
        for key in ("16", "32", "64", "512"):
            if key not in bucket_maps:
                raise ValueError(f"bucket_maps missing space {key}")
        self.tap = tap
        self.normcatch = normcatch
        self.bucket_maps = bucket_maps
        self.label_map = np.asarray(label_map, dtype=np.int64)
        self.n_classes = int(n_classes)
        self.glue_class = int(n_classes) - 1
        self.probes = dict(probes)
        self.n_slots = int(n_slots)
        self.top_m = int(top_m)
        # All four cells are required (critic advisory 2026-09-02): a
        # missing probe would otherwise degrade to NaN confidence and a
        # policy that silently never fires.
        want_keys = {(a, o) for a in PROBE_ARMS for o in PROBE_OFFSETS}
        if set(self.probes) != want_keys:
            raise ValueError(f"reader needs exactly the probe cells {sorted(want_keys)}, "
                             f"got {sorted(self.probes)}")
        for (arm, off), pr in self.probes.items():
            if pr.n_classes != self.n_classes:
                raise ValueError(f"probe {(arm, off)} has {pr.n_classes} classes, "
                                 f"label space has {self.n_classes}")

    def token_class(self, token_id: int) -> int:
        return int(self.label_map[int(token_id)])

    def read(self, p_anchor: np.ndarray, pos: int, abs_pos: int) -> AnchorRead:
        slots = self.tap.collect_at(pos)
        h = self.normcatch.collect_at(pos)
        summ = anchor_free_summaries(p_anchor, self.bucket_maps, self.top_m)
        x = {"a": probe_input(summ),
             "c": probe_input(summ, slots=slots, n_slots=self.n_slots)}
        pred: dict = {}
        conf: dict = {}
        for arm in PROBE_ARMS:
            pp, cc = [], []
            for off in PROBE_OFFSETS:
                cls, cf = self.probes[(arm, off)](x[arm])
                pp.append(cls)
                cc.append(cf)
            pred[arm] = tuple(pp)
            conf[arm] = tuple(cc)
        return AnchorRead(abs_pos=int(abs_pos), summaries=summ, slots=slots,
                          h=h, probe_pred=pred, probe_conf=conf, x=x)

    def close(self) -> None:
        self.tap.close()
        self.normcatch.close()


class ByproductRecorder:
    """E8 per-prompt byproduct accumulator. add_block() receives the
    anchor the block CONSULTED (the previous block's — or the prefill's
    — read) plus the block's outcomes; finalize() returns arrays for
    np.savez. Per-drafted-position arrays are padded to gamma_max."""

    def __init__(self, gamma_max: int = 6):
        self.gamma_max = int(gamma_max)
        self.rows: list[dict] = []

    def add_block(self, anchor: AnchorRead, gamma_used: int, stop_pos: int,
                  extend_fired: bool, accepted: int, proposed: list[int],
                  analytic: list[float], q_sigs: list[float],
                  draft_classes: list[int]) -> None:
        g = self.gamma_max
        if gamma_used > g or len(proposed) != gamma_used or len(analytic) != gamma_used:
            raise ValueError("inconsistent block record")
        prop = np.full(g, -1, dtype=np.int32)
        prop[:gamma_used] = proposed
        ana = np.full(g, np.nan, dtype=np.float32)
        ana[:gamma_used] = analytic
        # accepted flags: 1 accepted, 0 the rejected position, -1 unreached
        acc = np.full(g, -1, dtype=np.int8)
        acc[:accepted] = 1
        if accepted < gamma_used:
            acc[accepted] = 0
        dcl = np.full(g, -1, dtype=np.int32)
        dcl[: len(draft_classes)] = draft_classes
        qs = np.full(2, np.nan, dtype=np.float32)
        qs[: len(q_sigs)] = q_sigs
        self.rows.append({
            "anchor_pos": np.int32(anchor.abs_pos),
            "slots": anchor.slots, "h": anchor.h,
            **{k: anchor.summaries[k] for k in
               ("mass16", "mass32", "mass64", "mass512",
                "entropy", "argmax", "top_ids", "top_p")},
            "probe_pred_a": np.asarray(anchor.probe_pred["a"], np.int32),
            "probe_conf_a": np.asarray(anchor.probe_conf["a"], np.float32),
            "probe_pred_c": np.asarray(anchor.probe_pred["c"], np.int32),
            "probe_conf_c": np.asarray(anchor.probe_conf["c"], np.float32),
            "q_sig": qs,
            "gamma_used": np.int16(gamma_used),
            "stop_pos": np.int8(stop_pos),
            "extend": np.int8(extend_fired),
            "accepted": np.int16(accepted),
            "proposed": prop, "acc_flags": acc, "analytic": ana,
            "draft_class": dcl,
        })

    def finalize(self) -> dict[str, np.ndarray]:
        if not self.rows:
            return {"n_blocks": np.int64(0)}
        keys = self.rows[0].keys()
        out = {k: np.stack([r[k] for r in self.rows]) for k in keys}
        out["n_blocks"] = np.int64(len(self.rows))
        return out


@dataclass
class K3Config:
    """What spec_decode_prompt's k3 parameter carries. reader=None is the
    containment rider's instruments-OFF configuration (E10): the prefill
    still runs (identical forward pattern) but no hooks exist.
    head_scorer (STAGE-C FREEZE): the frozen OQ-15 heads a 'head'
    policy scores through; its family picks the AnchorRead.x key
    ('free' -> 'a', 'tel' -> 'c')."""

    policy: SchedulerPolicy
    reader: LiveReader | None = None
    recorder: ByproductRecorder | None = None
    head_scorer: object | None = None
    # OQ-16 STAGE-A FREEZE: a steer_inject.BlockInjector — the SD^2-style
    # draft-side injection driven by each block's consulted anchor. Rides
    # the FIXED gamma-4 schedule only (the actuator arms never schedule)
    # and needs the reader (the anchor's h / summaries / slots).
    inject: object | None = None

    def __post_init__(self):
        if self.recorder is not None and self.reader is None:
            raise ValueError("byproduct recording requires the live reader")
        if self.inject is not None:
            if self.reader is None:
                raise ValueError("injection arms require the live reader")
            if self.policy.kind != "fixed":
                raise ValueError("injection arms ride the fixed schedule only "
                                 "(STAGE-A FREEZE)")
        if self.policy.kind == "probe" and self.reader is None:
            raise ValueError("probe policies require the live reader")
        if self.policy.kind == "head":
            if self.reader is None or self.head_scorer is None:
                raise ValueError("head policies require the live reader AND a head_scorer")
            if self.policy.gamma_base != 4:
                raise ValueError("head policies are defined for gamma_base 4 "
                                 "(S_4 * a_hat_5 extend semantics; critic "
                                 "advisory at the STAGE-C FREEZE round)")
        elif self.head_scorer is not None:
            raise ValueError("head_scorer is only meaningful for kind='head'")


def build_live_reader(target, pmeta: dict,
                      probes: dict[tuple[str, int], LinearProbe],
                      bucket_paths: dict[str, str], glue16_path: str,
                      load_4bit: bool, expect_target: str) -> "LiveReader":
    """Construct the live reader with every E1/E7 binding enforced:
    export-meta model + load regime, bucket shas vs the harvest-bound
    shas, label-space class count, tap layer names + sketch seeds
    bit-reproduced. One construction path for the arm runner and the
    containment rider (E10) — they must not diverge."""
    from ..probes import load_label_space
    from .hf_specdec import load_buckets

    tap_meta = pmeta["tap"]
    if tap_meta["model"] != expect_target:
        raise SystemExit(f"probe weights were exported for {tap_meta['model']}, "
                         f"not {expect_target}")
    want_load = "nf4-double-quant-bf16compute" if load_4bit else "bf16"
    if tap_meta["target_load"] != want_load:
        raise SystemExit(f"load regime {want_load} != export meta "
                         f"{tap_meta['target_load']} (harvest regime)")
    for k, p in bucket_paths.items():
        want = pmeta["buckets_sha256"].get(f"buckets{k}")
        if want and hashlib.sha256(Path(p).read_bytes()).hexdigest() != want:
            raise SystemExit(f"buckets{k} sha != the harvest-bound sha in the "
                             "probe-weights meta — wrong space files")
    vocab = int(target.config.vocab_size)
    bucket_maps = {}
    for k, p in bucket_paths.items():
        arr = load_buckets(p, vocab, expect_model=expect_target)
        if (arr < 0).any():
            raise SystemExit(f"buckets{k} does not cover the full vocab")
        bucket_maps[k] = arr
    label_map, n_classes = load_label_space(bucket_paths["16"], glue16_path)
    if n_classes != int(pmeta["n_classes"]):
        raise SystemExit(f"label space has {n_classes} classes, export meta "
                         f"says {pmeta['n_classes']}")
    tap = LiveShadowTap(target, tap_meta["layer_regex"],
                        {int(x) for x in tap_meta["layers"].split(",")},
                        int(tap_meta["n_slots"]), int(tap_meta["top_n"]),
                        seed=int(tap_meta["sketch_seed"]))
    if tap.layer_names != list(tap_meta["layer_names"]):
        raise SystemExit("live tap layers do not reproduce the export meta")
    if {k: int(v) for k, v in tap.layer_seeds.items()} != \
            {k: int(v) for k, v in tap_meta["sketch_layer_seeds"].items()}:
        raise SystemExit("live tap sketch seeds do not reproduce the export meta")
    norm_module = getattr(getattr(target, "model", None), "norm", None)
    if norm_module is None:
        raise SystemExit("expected a LlamaForCausalLM-shaped target exposing .model.norm")
    normcatch = LiveNormCatch(norm_module)
    return LiveReader(tap, normcatch, bucket_maps, label_map, n_classes,
                      probes, n_slots=int(tap_meta["n_slots"]))


def load_probe_weights(npz_path: str | Path,
                       meta_path: str | Path | None = None
                       ) -> tuple[dict[tuple[str, int], LinearProbe], dict]:
    """Load the export tool's weights with the sha binding enforced (the
    meta records the npz sha at export time; a mismatch means the weights
    are not the audited bytes)."""
    npz_path = Path(npz_path)
    if meta_path is None:
        meta_path = npz_path.with_suffix(".meta.json")  # harvest convention
    meta = json.loads(Path(meta_path).read_text())
    got = hashlib.sha256(npz_path.read_bytes()).hexdigest()
    if meta.get("npz_sha256") != got:
        raise SystemExit(f"{npz_path} sha {got[:12]}... != meta npz_sha256 "
                         f"{str(meta.get('npz_sha256'))[:12]}... — refusing unbound weights")
    z = np.load(npz_path)
    probes: dict[tuple[str, int], LinearProbe] = {}
    for arm in PROBE_ARMS:
        for off in PROBE_OFFSETS:
            probes[(arm, off)] = LinearProbe(z[f"W_{arm}_off{off}"],
                                             z[f"b_{arm}_off{off}"])
    return probes, meta
