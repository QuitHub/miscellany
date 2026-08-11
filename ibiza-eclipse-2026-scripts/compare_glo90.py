#!/usr/bin/env python3
"""Compare Open-Meteo GLO-90 fan maxima against the combined GLO-30+MDT05 analysis."""
import json
import math
import os

BASE = os.path.dirname(os.path.abspath(__file__))
R, KFAC, EYE = 6371000.0, 0.87, 2.0

om = json.load(open(f"{BASE}/openmeteo_profiles.json"))
combined = {o["name"]: o for o in json.load(open(f"{BASE}/analysis_combined.json"))["observers"]}

dists = om["dists_m"]
for obs in om["observers"]:
    best = (-99, None, None, None)
    for az, elevs in obs["rays"].items():
        for d, e in zip(dists, elevs):
            drop = d * d / (2 * R) * KFAC
            a = math.degrees(math.atan2(e - EYE - drop, d))
            if a > best[0]:
                best = (a, float(az), d, e)
    c = combined[obs["name"]]
    print(f"{obs['name']:32s} GLO-90 {best[0]:6.3f} at az {best[1]:6.1f} d {best[2]/1000:5.2f} km "
          f"({best[3]:.0f} m) | combined {c['max_angle']:6.3f} | diff {c['max_angle']-best[0]:+.3f}")
