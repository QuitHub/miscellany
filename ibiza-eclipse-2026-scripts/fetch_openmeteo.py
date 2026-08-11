#!/usr/bin/env python3
"""Fetch Open-Meteo (Copernicus GLO-90) terrain profiles for the eclipse fan.

Six observers, azimuths 286.2-287.2 in 0.1 deg steps, samples every 100 m
from 0.2 to 12 km. Writes openmeteo_profiles.json.
"""
import json
import math
import os
import time
import urllib.request

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "openmeteo_profiles.json")

OBSERVERS = [
    ("1 South end (Cap des Falco)", 38.8400, 1.3690),
    ("2 South-mid", 38.8470, 1.3690),
    ("3 Mid-beach", 38.8515, 1.3655),
    ("4 North-mid", 38.8565, 1.3625),
    ("5 North end (airport road)", 38.8615, 1.3592),
    ("6 PLANNED SPOT (NW corner)", 38.865119, 1.355553),
]
AZIMUTHS = [round(286.2 + 0.1 * i, 1) for i in range(11)]
DISTS = [round(200 + 100 * i) for i in range(119)]  # 0.2 .. 12.0 km

M_PER_DEG_LAT = 111190.0


def dest(lat0, lon0, az_deg, d_m):
    az = math.radians(az_deg)
    lat = lat0 + d_m * math.cos(az) / M_PER_DEG_LAT
    lon = lon0 + d_m * math.sin(az) / (M_PER_DEG_LAT * math.cos(math.radians(lat0)))
    return round(lat, 6), round(lon, 6)


def main():
    tasks = []  # (obs_idx, az, d, lat, lon)
    for oi, (_, lat0, lon0) in enumerate(OBSERVERS):
        for az in AZIMUTHS:
            for d in DISTS:
                lat, lon = dest(lat0, lon0, az, d)
                tasks.append((oi, az, d, lat, lon))

    elev = {}
    for i in range(0, len(tasks), 100):
        chunk = tasks[i : i + 100]
        lats = ",".join(str(t[3]) for t in chunk)
        lons = ",".join(str(t[4]) for t in chunk)
        url = f"https://api.open-meteo.com/v1/elevation?latitude={lats}&longitude={lons}"
        for attempt in range(10):
            try:
                with urllib.request.urlopen(url, timeout=30) as r:
                    data = json.load(r)
                break
            except urllib.error.HTTPError as e:
                if e.code == 429:
                    time.sleep(65)
                elif attempt == 9:
                    raise
                else:
                    time.sleep(5)
            except Exception:
                if attempt == 9:
                    raise
                time.sleep(5)
        for t, e in zip(chunk, data["elevation"]):
            elev[(t[0], t[1], t[2])] = e
        time.sleep(11)
        if (i // 100) % 10 == 0:
            print(f"{i + len(chunk)}/{len(tasks)}", flush=True)

    out = []
    for oi, (name, lat0, lon0) in enumerate(OBSERVERS):
        rays = {}
        for az in AZIMUTHS:
            rays[str(az)] = [elev[(oi, az, d)] for d in DISTS]
        out.append({"name": name, "lat": lat0, "lon": lon0, "rays": rays})
    with open(OUT, "w") as f:
        json.dump({"dists_m": DISTS, "azimuths": AZIMUTHS, "observers": out}, f)
    print("saved", OUT)


if __name__ == "__main__":
    main()
