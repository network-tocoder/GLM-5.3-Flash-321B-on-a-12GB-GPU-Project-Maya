#!/usr/bin/env python3
"""1 Hz sampler: GPU mem/util, RAM used, disk read MB/s -> monitor.csv
Usage: python3 monitor.py [out.csv]   (Ctrl+C to stop)"""
import subprocess, sys, time
out = open(sys.argv[1] if len(sys.argv) > 1 else "monitor.csv", "a")
out.write("t,gpu_mem_mib,gpu_util,ram_used_gib,disk_read_mbs\n"); out.flush()
def disk_sectors():
    tot = 0
    for line in open("/proc/diskstats"):
        p = line.split()
        name = p[2]
        if (name.startswith("nvme") and "p" not in name[4:]) or (name[:2] in ("sd", "vd") and name[-1].isalpha()):
            tot += int(p[5])          # sectors read
    return tot
def ram_used():
    m = {l.split(":")[0]: int(l.split()[1]) for l in open("/proc/meminfo")}
    return (m["MemTotal"] - m["MemAvailable"]) / 1048576
prev = disk_sectors(); t0 = time.time()
while True:
    time.sleep(1)
    try:
        g = subprocess.run(["nvidia-smi", "--query-gpu=memory.used,utilization.gpu", "--format=csv,noheader,nounits"],
                           capture_output=True, text=True, timeout=5).stdout.strip().split(",")
    except Exception:
        g = ["", ""]
    cur = disk_sectors(); mbs = (cur - prev) * 512 / 1e6; prev = cur
    out.write(f"{time.time()-t0:.0f},{g[0].strip()},{g[1].strip()},{ram_used():.2f},{mbs:.1f}\n"); out.flush()
