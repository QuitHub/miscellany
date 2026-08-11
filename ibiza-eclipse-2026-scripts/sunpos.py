#!/usr/bin/env python3
"""Sun azimuth/altitude at Es Codolar beach, Ibiza, around totality on 2026-08-12."""
import math

def sun_position(jd, lat, lon):
    # NOAA solar position algorithm (accuracy ~0.01 deg)
    T = (jd - 2451545.0) / 36525.0
    L0 = (280.46646 + T * (36000.76983 + T * 0.0003032)) % 360
    M = 357.52911 + T * (35999.05029 - 0.0001537 * T)
    e = 0.016708634 - T * (0.000042037 + 0.0000001267 * T)
    Mr = math.radians(M)
    C = (math.sin(Mr) * (1.914602 - T * (0.004817 + 0.000014 * T))
         + math.sin(2 * Mr) * (0.019993 - 0.000101 * T)
         + math.sin(3 * Mr) * 0.000289)
    true_long = L0 + C
    omega = 125.04 - 1934.136 * T
    lam = true_long - 0.00569 - 0.00478 * math.sin(math.radians(omega))
    eps0 = 23 + (26 + ((21.448 - T * (46.8150 + T * (0.00059 - T * 0.001813)))) / 60) / 60
    eps = eps0 + 0.00256 * math.cos(math.radians(omega))
    lam_r, eps_r = math.radians(lam), math.radians(eps)
    ra = math.degrees(math.atan2(math.cos(eps_r) * math.sin(lam_r), math.cos(lam_r))) % 360
    dec = math.degrees(math.asin(math.sin(eps_r) * math.sin(lam_r)))
    # Greenwich mean sidereal time
    gmst = (280.46061837 + 360.98564736629 * (jd - 2451545.0)
            + 0.000387933 * T * T - T * T * T / 38710000.0) % 360
    ha = (gmst + lon - ra) % 360
    if ha > 180: ha -= 360
    lat_r, dec_r, ha_r = map(math.radians, (lat, dec, ha))
    alt = math.degrees(math.asin(math.sin(lat_r) * math.sin(dec_r)
                                 + math.cos(lat_r) * math.cos(dec_r) * math.cos(ha_r)))
    az = math.degrees(math.atan2(-math.sin(ha_r),
                                 math.tan(dec_r) * math.cos(lat_r)
                                 - math.sin(lat_r) * math.cos(ha_r))) % 360
    # refraction correction (Bennett), for apparent altitude near horizon
    if alt > -1:
        R = 1.02 / math.tan(math.radians(alt + 10.3 / (alt + 5.11))) / 60.0
    else:
        R = 0
    return az, alt, alt + R

def jd_utc(y, mo, d, h, mi, s):
    if mo <= 2: y, mo = y - 1, mo + 12
    A = y // 100
    B = 2 - A + A // 4
    return (int(365.25 * (y + 4716)) + int(30.6001 * (mo + 1)) + d + B - 1524.5
            + (h + mi / 60 + s / 3600) / 24)

# Es Codolar beach (mid-beach, near the waterline)
LAT, LON = 38.8645, 1.3540

print("CEST time   azimuth   geom.alt  apparent.alt")
for (h, mi, sec, label) in [(20, 32, 34, "totality start"),
                            (20, 33, 8, "max eclipse"),
                            (20, 33, 41, "totality end"),
                            (20, 52, 0, "~sunset")]:
    # CEST = UTC+2
    jd = jd_utc(2026, 8, 12, h - 2, mi, sec)
    az, alt, app = sun_position(jd, LAT, LON)
    print(f"{h:02d}:{mi:02d}:{sec:02d}  {az:7.2f}   {alt:7.2f}   {app:7.2f}   {label}")
