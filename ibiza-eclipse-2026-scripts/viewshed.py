#!/usr/bin/env python3
"""Will the eclipsed Sun (az 286.7, apparent alt 3.1) clear the terrain from Es Codolar?

Terrain model: verified summits (Wikipedia/PeakVisor heights) as cones draped to the
GSHHS full-res coastline footprints. Conservative hill radii chosen so slopes reach
sea level at the mapped coast.
"""
import math

R = 6371000.0
EYE = 2.0
SUN_AZ = 286.7          # max eclipse; drifts 286.6->286.8 during totality
SUN_ALT_APP = 3.12      # apparent altitude of sun CENTER at max eclipse
SUN_RADIUS = 0.26       # angular radius of solar disk

def bearing_dist(lat1, lon1, lat2, lon2):
    la1, la2 = math.radians(lat1), math.radians(lat2)
    dlon = math.radians(lon2 - lon1)
    x = math.sin(dlon) * math.cos(la2)
    y = math.cos(la1) * math.sin(la2) - math.sin(la1) * math.cos(la2) * math.cos(dlon)
    br = math.degrees(math.atan2(x, y)) % 360
    d = R * math.acos(min(1, math.sin(la1) * math.sin(la2) + math.cos(la1) * math.cos(la2) * math.cos(dlon)))
    return br, d

# (name, summit lat, lon, height m, footprint radius m)
HILLS = [
    ("Puig des Jondal (160m)",       38.8640, 1.3300, 160, 1300),
    ("Sa Caleta headland (~22m)",    38.8685, 1.3480,  22,  500),
    ("Porroig peninsula (~55m)",     38.8660, 1.2970,  55,  800),
    ("Puig d'en Serra/Es Cubells",   38.8760, 1.2680, 271, 1800),
    ("Sa Talaiassa (475m)",          38.9114, 1.2742, 475, 2200),
    ("Es Vedra (382m)",              38.8672, 1.1936, 382,  600),
]

# observers along the actual GSHHS beach line, S -> N
OBSERVERS = [
    ("south end, nr Cap des Falco",  38.8400, 1.3690),
    ("south-mid",                    38.8470, 1.3690),
    ("mid-beach",                    38.8515, 1.3655),
    ("north-mid",                    38.8565, 1.3625),
    ("north end (closest to airport)",38.8615, 1.3592),
]

def terrain_angle(olat, olon, az_lo, az_hi):
    """max apparent terrain angle within an azimuth window, sampling each hill cone"""
    worst = (0.0, "open sea")
    for name, hlat, hlon, hgt, rad in HILLS:
        # sample the cone on a polar grid around the summit
        for fr in [0, 0.15, 0.3, 0.45, 0.6, 0.75, 0.9]:
            n = 1 if fr == 0 else 24
            for k in range(n):
                th = 2 * math.pi * k / n
                plat = hlat + (fr * rad * math.cos(th)) / 111190
                plon = hlon + (fr * rad * math.sin(th)) / (111190 * math.cos(math.radians(hlat)))
                h = hgt * (1 - fr)
                br, d = bearing_dist(olat, olon, plat, plon)
                if not (az_lo <= br <= az_hi):
                    continue
                drop = d * d / (2 * R) * (1 - 0.13)   # curvature minus terrestrial refraction
                ang = math.degrees(math.atan2(h - EYE - drop, d))
                if ang > worst[0]:
                    worst = (ang, f"{name} @ {d/1000:.1f} km, az {br:.1f}")
    return worst

print(f"Sun at max eclipse: az {SUN_AZ}, center alt {SUN_ALT_APP}, lower limb {SUN_ALT_APP-SUN_RADIUS:.2f}\n")
band = (SUN_AZ - 0.45, SUN_AZ + 0.45)   # disk width + az drift during totality
for name, olat, olon in OBSERVERS:
    ang, what = terrain_angle(olat, olon, *band)
    margin = (SUN_ALT_APP - SUN_RADIUS) - ang
    verdict = ("TOTALITY BLOCKED" if ang > SUN_ALT_APP + SUN_RADIUS else
               "partially clipped" if ang > SUN_ALT_APP - SUN_RADIUS else
               f"CLEAR (margin {margin:.2f} deg below lower limb)")
    print(f"{name:34s} horizon {ang:4.2f} deg <- {what}")
    print(f"{'':34s} {verdict}\n")

# after totality: when does the sun vanish behind terrain? sun descends ~0.19 deg/min,
# az drifts +0.09 deg/min. Track from 20:33 onward.
print("--- post-totality: minutes of partial phase visible after 20:33 ---")
for name, olat, olon in OBSERVERS:
    for minutes in range(0, 20):
        alt = 3.12 - 0.168 * minutes          # apparent alt of center
        az = 286.7 + 0.155 * minutes
        ang, what = terrain_angle(olat, olon, az - 0.3, az + 0.3)
        if alt + SUN_RADIUS < ang or alt < -0.25:
            print(f"{name:34s} sun gone ~20:{33+minutes} ({'terrain: '+what if alt+SUN_RADIUS<ang and alt>=-0.25 else 'sea horizon sunset'})")
            break
    else:
        print(f"{name:34s} visible to sea-horizon sunset ~20:52")
