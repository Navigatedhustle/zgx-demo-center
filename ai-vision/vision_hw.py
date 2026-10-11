"""GPU telemetry for the AI Vision demo.

nvidia-smi for clock/power/temp/util (pynvml returns N/A for util on GB10).
pynvml only for memory queries — but on GB10 the unified-memory pool often
reports used=0, so we expose what we get and let the UI handle the case.
"""
import subprocess
import threading
import time

try:
    import pynvml
    pynvml.nvmlInit()
    _NVML_OK = True
except Exception:
    _NVML_OK = False


class GpuPoller(threading.Thread):
    _CMD = [
        "nvidia-smi",
        "--query-gpu=clocks.current.graphics,power.draw,temperature.gpu,utilization.gpu",
        "--format=csv,noheader,nounits",
    ]

    def __init__(self, interval_s=1.0):
        super().__init__(daemon=True, name="gpu-poll")
        self._interval = interval_s
        self._lock = threading.Lock()
        self._data = {
            "clock_mhz": 0,
            "power_w": 0.0,
            "temp_c": 0,
            "util_pct": None,
            "mem_used_gb": None,
            "mem_total_gb": None,
            "available": False,
        }

    def run(self):
        try:
            r = subprocess.run(self._CMD, capture_output=True, timeout=3)
            if r.returncode != 0:
                print("  [hw] nvidia-smi non-zero exit — telemetry will stay empty", flush=True)
        except FileNotFoundError:
            print("  [hw] nvidia-smi not found — telemetry disabled", flush=True)
            return

        nvml_handle = None
        if _NVML_OK:
            try:
                nvml_handle = pynvml.nvmlDeviceGetHandleByIndex(0)
            except Exception:
                nvml_handle = None

        while True:
            try:
                r = subprocess.run(self._CMD, capture_output=True, text=True, timeout=3)
                if r.returncode == 0:
                    parts = [p.strip() for p in r.stdout.strip().split(",")]
                    if len(parts) >= 4:
                        clock = int(parts[0]) if parts[0].lstrip("-").isdigit() else 0
                        power = float(parts[1]) if parts[1].replace(".","").lstrip("-").isdigit() else 0.0
                        temp  = int(parts[2]) if parts[2].lstrip("-").isdigit() else 0
                        util  = int(parts[3]) if parts[3].lstrip("-").isdigit() else None
                        mem_used = mem_total = None
                        if nvml_handle is not None:
                            try:
                                mi = pynvml.nvmlDeviceGetMemoryInfo(nvml_handle)
                                mem_used = round(mi.used / 1024**3, 1)
                                mem_total = round(mi.total / 1024**3, 1)
                            except Exception:
                                pass
                        with self._lock:
                            self._data = {
                                "clock_mhz": clock,
                                "power_w": round(power, 1),
                                "temp_c": temp,
                                "util_pct": util,
                                "mem_used_gb": mem_used,
                                "mem_total_gb": mem_total,
                                "available": True,
                            }
            except Exception:
                pass
            time.sleep(self._interval)

    def get(self):
        with self._lock:
            return dict(self._data)
