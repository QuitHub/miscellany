#!/usr/bin/env python3
"""Re-run the full analysis with elevation = max(GLO-30 DSM, IGN MDT05 lidar).

MDT05 is bare-earth at 5 m (sharp crests, no vegetation); GLO-30 is a 30 m
surface model (vegetation included, smoothed crests). The pointwise max is
the pessimistic reading the verification prompt asks for.
Downloads four WCS chunks covering the whole 12 km wedge (cached on disk).
"""
import json
import math
import os
import subprocess

import numpy as np
import rasterio

BASE = os.path.dirname(os.path.abspath(__file__))
R = 6371000.0
KFAC = 0.87
M_PER_DEG_LAT = 111190.0
EYE = 2.0
SUN_AZ, SUN_ALT, SUN_R = 286.7, 3.12, 0.26
LIMB, ALL_HIDDEN = SUN_ALT - SUN_R, SUN_ALT + SUN_R
DESC_RATE, AZ_RATE = 0.168, 0.155

OBSERVERS = [
    ("1 South end (Cap des Falco)", 38.8400, 1.3690),
    ("2 South-mid", 38.8470, 1.3690),
    ("3 Mid-beach", 38.8515, 1.3655),
    ("4 North-mid", 38.8565, 1.3625),
    ("5 North end (airport road)", 38.8615, 1.3592),
    ("6 PLANNED SPOT (NW corner)", 38.865119, 1.355553),
]
CAPE = (38.8304, 1.3708)

CHUNKS = [(la, la + 0.07, lo, lo + 0.0825)
          for la in (38.80, 38.87) for lo in (1.21, 1.2925)]

WCS = ("https://servicios.idee.es/wcs-inspire/mdt?service=WCS&version=2.0.1"
       "&request=GetCoverage&coverageId=Elevacion4258_5"
       "&subset=Lat({0},{1})&subset=Long({2},{3})&format=image/tiff")

rasters = []
for i, (la0, la1, lo0, lo1) in enumerate(CHUNKS):
    path = f"{BASE}/mdt05_chunk{i}.tif"
    if not os.path.exists(path):
        url = WCS.format(la0, la1, lo0, lo1)
        subprocess.run(["curl", "-s", "-o", path, url], check=True, timeout=300)
    ds = rasterio.open(path)
    arr = ds.read(1).astype(float)
    arr[arr < -1000] = 0.0
    rasters.append((ds.bounds, ~ds.transform, np.maximum(arr, 0.0)))
    print(f"chunk {i}: {ds.shape} max {arr.max():.0f} m", flush=True)

GLO30 = f"{BASE}/glo30_N38E001.tif"
if not os.path.exists(GLO30):
    subprocess.run(["curl", "-s", "-o", GLO30,
                    "https://copernicus-dem-30m.s3.amazonaws.com/"
                    "Copernicus_DSM_COG_10_N38_00_E001_00_DEM/"
                    "Copernicus_DSM_COG_10_N38_00_E001_00_DEM.tif"],
                   check=True, timeout=300)
gds = rasterio.open(GLO30)
gband = gds.read(1).astype(float)
ginv = ~gds.transform


def sample_glo30(lats, lons):
    cols, rows = ginv * (lons, lats)
    r0 = np.clip(np.floor(rows).astype(int), 0, gband.shape[0] - 2)
    c0 = np.clip(np.floor(cols).astype(int), 0, gband.shape[1] - 2)
    fr, fc = rows - r0, cols - c0
    v = (gband[r0, c0] * (1 - fr) * (1 - fc) + gband[r0, c0 + 1] * (1 - fr) * fc
         + gband[r0 + 1, c0] * fr * (1 - fc) + gband[r0 + 1, c0 + 1] * fr * fc)
    return np.maximum(v, 0.0)


def sample_mdt05(lats, lons):
    out = np.zeros_like(lats)
    done = np.zeros(lats.shape, dtype=bool)
    for bounds, invt, arr in rasters:
        m = (~done & (lats >= bounds.bottom) & (lats <= bounds.top)
             & (lons >= bounds.left) & (lons <= bounds.right))
        if not m.any():
            continue
        cols, rows = invt * (lons[m], lats[m])
        r = np.clip(np.round(rows).astype(int), 0, arr.shape[0] - 1)
        c = np.clip(np.round(cols).astype(int), 0, arr.shape[1] - 1)
        out[m] = arr[r, c]
        done[m] = True
    return out, done


def sample_combined(lats, lons):
    g = sample_glo30(lats, lons)
    m5, cov = sample_mdt05(lats, lons)
    return np.where(cov, np.maximum(g, m5), g)


DISTS = np.arange(100.0, 12001.0, 50.0)
DROP = DISTS**2 / (2 * R) * KFAC
AZ_GRID = np.round(np.arange(262.0, 312.0, 0.1), 1)


def panorama(lat0, lon0, sampler):
    azr = np.radians(AZ_GRID)[:, None]
    d = DISTS[None, :]
    lat = lat0 + d * np.cos(azr) / M_PER_DEG_LAT
    lon = lon0 + d * np.sin(azr) / (M_PER_DEG_LAT * math.cos(math.radians(lat0)))
    elev = sampler(lat.ravel(), lon.ravel()).reshape(lat.shape)
    ang = np.degrees(np.arctan2(elev - EYE - DROP[None, :], d))
    imax = np.argmax(ang, axis=1)
    idx = np.arange(len(AZ_GRID))
    return ang[idx, imax], DISTS[imax], elev[idx, imax]


FAN = (AZ_GRID >= 286.15) & (AZ_GRID <= 287.25)


def verdict_word(a):
    return "CLEAR" if a < LIMB else ("CLIPPED" if a <= ALL_HIDDEN else "BLOCKED")


def gone_times(h):
    first = gone = None
    for t in np.arange(0, 30, 0.25):
        ter = float(np.interp(SUN_AZ + AZ_RATE * t, AZ_GRID, h))
        alt = SUN_ALT - DESC_RATE * t
        if first is None and alt - SUN_R <= ter:
            first = float(t)
        if gone is None and alt + SUN_R <= ter:
            gone = float(t)
            break
    return first, gone


def fmt_time(mins):
    if mins is None:
        return None
    total = 20 * 60 + 33 + mins
    return f"{int(total // 60):02d}:{int(total % 60):02d}"


results, horizons = [], {}
for name, lat0, lon0 in OBSERVERS:
    h, hd, he = panorama(lat0, lon0, sample_combined)
    hg, _, _ = panorama(lat0, lon0, sample_glo30)
    horizons[name] = (h, hd, he)
    i = np.argmax(h[FAN])
    first, gone = gone_times(h)
    results.append({
        "name": name, "lat": lat0, "lon": lon0,
        "max_angle": float(h[FAN][i]),
        "max_angle_glo30_only": float(hg[FAN].max()),
        "at_az": float(AZ_GRID[FAN][i]),
        "at_dist_m": float(hd[FAN][i]),
        "at_elev_m": float(he[FAN][i]),
        "verdict": verdict_word(float(h[FAN][i])),
        "margin_deg": float(LIMB - h[FAN][i]),
        "sun_touches_terrain": fmt_time(first),
        "sun_fully_gone": fmt_time(gone),
    })

chain = [CAPE] + [(o[1], o[2]) for o in OBSERVERS]
bpts, bdist, cum = [], [], 0.0
for (la1, lo1), (la2, lo2) in zip(chain[:-1], chain[1:]):
    dy = (la2 - la1) * M_PER_DEG_LAT
    dx = (lo2 - lo1) * M_PER_DEG_LAT * math.cos(math.radians(la1))
    seg = math.hypot(dx, dy)
    for i in range(max(1, int(seg // 50))):
        f = i / max(1, int(seg // 50))
        bpts.append((la1 + f * (la2 - la1), lo1 + f * (lo2 - lo1)))
        bdist.append(cum + f * seg)
    cum += seg
bpts.append(chain[-1])
bdist.append(cum)

brows = []
for (la, lo), d in zip(bpts, bdist):
    h, _, _ = panorama(la, lo, sample_combined)
    a = float(h[FAN].max())
    brows.append({"m_north_of_cape": round(d), "lat": round(la, 6),
                  "lon": round(lo, 6), "max_fan_angle": round(a, 3),
                  "verdict": verdict_word(a)})

with open(f"{BASE}/analysis_combined.json", "w") as f:
    json.dump({"observers": results,
               "boundary": {"chain_total_m": cum, "samples": brows}}, f, indent=1)

spots = []
for key, disp in [("6 PLANNED SPOT (NW corner)", "Your spot — NW corner (38.86512, 1.35555)"),
                  ("3 Mid-beach", "Mid-beach — 1.6 km further south (38.8515, 1.3655)")]:
    h, hd, he = horizons[key]
    o = next(x for x in OBSERVERS if x[0] == key)
    feats = []
    for i in range(2, len(AZ_GRID) - 2):
        if h[i] == max(h[max(0, i - 25):i + 25]) and h[i] > 0.3:
            feats.append({"az": float(AZ_GRID[i]), "alt": float(h[i]),
                          "label": f"{he[i]:.0f} m @ {hd[i]/1000:.1f} km"})
    out = []
    for fd in feats:
        if all(abs(fd["az"] - x["az"]) > 4 for x in out):
            out.append(fd)
    spots.append({"name": disp, "lat": o[1], "lon": o[2],
                  "az": [float(a) for a in AZ_GRID],
                  "horizon": [round(float(x), 4) for x in h],
                  "features": out})

with open(f"{BASE}/horizon.json", "w") as f:
    json.dump({"title_suffix": "Copernicus GLO-30 + IGN MDT05 5 m lidar", "spots": spots}, f)

for r in results:
    print(f"{r['name']:32s} max {r['max_angle']:6.3f} (glo30 {r['max_angle_glo30_only']:6.3f}) "
          f"az {r['at_az']:6.1f} d {r['at_dist_m']/1000:5.2f} km elev {r['at_elev_m']:6.1f} m "
          f"-> {r['verdict']:7s} margin {r['margin_deg']:+.3f} "
          f"touch {r['sun_touches_terrain']} gone {r['sun_fully_gone']}")

wa = [b for b in brows if b["verdict"] != "CLEAR"]
print("non-clear boundary samples:", len(wa))
for b in wa:
    print(f"  {b['m_north_of_cape']:5d} m N of cape: {b['max_fan_angle']:.3f} {b['verdict']}")
