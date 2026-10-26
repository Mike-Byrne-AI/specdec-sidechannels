"""Fail-closed preflight for hours-long GPU runs on a shared interactive box.

Ported pattern from the sibling llama_sae_starter's run_calibration_pass
(median utilization over several samples so one idle blip can't open the
gate; unreadable nvidia-smi FAILS the check rather than passing it).

Checks: free VRAM, median GPU utilization (another process mid-burn),
free disk, and (Windows) a pending OS reboot. Returns the measurements as a
dict for the run's meta sidecar; raises SystemExit on failure unless
force=True. Stdlib-only; no torch import.
"""

from __future__ import annotations

import shutil
import subprocess
import time


def _nvidia_smi_sample() -> dict:
    out = subprocess.run(
        ["nvidia-smi", "--query-gpu=memory.total,memory.free,utilization.gpu",
         "--format=csv,noheader,nounits"],
        capture_output=True, text=True, timeout=15,
    )
    if out.returncode != 0 or not out.stdout.strip():
        raise RuntimeError(f"nvidia-smi unreadable: rc={out.returncode} {out.stderr.strip()!r}")
    total, free, util = (float(x) for x in out.stdout.strip().splitlines()[0].split(","))
    return {"vram_total_mb": total, "vram_free_mb": free, "util_pct": util}


def _pending_reboot() -> bool | None:
    """Windows pending-reboot flags; None = not determinable (non-Windows,
    or the registry refused access — absence of evidence is not absence of
    a pending reboot)."""
    try:
        import winreg
    except ImportError:
        return None
    keys = (
        r"SOFTWARE\Microsoft\Windows\CurrentVersion\WindowsUpdate\Auto Update\RebootRequired",
        r"SOFTWARE\Microsoft\Windows\CurrentVersion\Component Based Servicing\RebootPending",
    )
    indeterminate = False
    for key in keys:
        try:
            winreg.CloseKey(winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key))
            return True
        except FileNotFoundError:
            continue  # key absent == not pending, the normal case
        except OSError:
            indeterminate = True
    return None if indeterminate else False


def preflight(
    min_vram_free_gb: float = 9.5,
    max_util_pct: float = 15.0,
    min_disk_free_gb: float = 10.0,
    samples: int = 3,
    interval_s: float = 1.0,
    force: bool = False,
    disk_path: str = ".",
) -> dict:
    """Gate an expensive run; returns measurements for the meta sidecar.
    disk_path: check free space on the volume the OUTPUT lands on, not
    whatever the cwd happens to be. force=True measures and warns but never
    gates. Inherent race: a pass here can still OOM at load time if another
    app grabs VRAM in between — the device-placement assert is the second
    line of defense."""
    problems: list[str] = []
    report: dict = {"forced": force}

    try:
        obs = []
        for i in range(samples):
            obs.append(_nvidia_smi_sample())
            if i + 1 < samples:
                time.sleep(interval_s)
        utils = sorted(o["util_pct"] for o in obs)
        median_util = utils[len(utils) // 2]
        vram_free_gb = min(o["vram_free_mb"] for o in obs) / 1024.0
        report.update(vram_free_gb=round(vram_free_gb, 2), median_util_pct=median_util,
                      vram_total_gb=round(obs[0]["vram_total_mb"] / 1024.0, 2))
        if vram_free_gb < min_vram_free_gb:
            problems.append(f"free VRAM {vram_free_gb:.1f}GB < {min_vram_free_gb}GB "
                            "(close games/browsers or lower the requirement)")
        if median_util > max_util_pct:
            problems.append(f"median GPU utilization {median_util:.0f}% > {max_util_pct}% "
                            "(another process is using the card)")
    except Exception as e:  # fail CLOSED: an unreadable GPU is not a pass
        report.update(nvidia_smi_error=str(e))
        problems.append(f"could not read GPU state ({e}); failing closed")

    disk_free_gb = shutil.disk_usage(disk_path).free / 1e9
    report["disk_free_gb"] = round(disk_free_gb, 1)
    if disk_free_gb < min_disk_free_gb:
        problems.append(f"free disk {disk_free_gb:.0f}GB < {min_disk_free_gb}GB")

    reboot = _pending_reboot()
    report["os_reboot_pending"] = reboot
    if reboot:
        problems.append("Windows has a PENDING REBOOT — an update restart can kill the run; "
                        "reboot first or pause updates")

    report["problems"] = problems
    if problems and not force:
        raise SystemExit("preflight failed:\n  - " + "\n  - ".join(problems)
                         + "\n(--skip-preflight to override)")
    for p in problems:
        print(f"[preflight OVERRIDDEN] {p}")
    return report
