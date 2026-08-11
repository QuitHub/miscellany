#!/usr/bin/env python3
"""Exact eclipse geometry for 38.865119, 1.355553 (Es Codolar, Ibiza).

Uses the same NOAA-style solar-position implementation as the existing
ibiza-eclipse-2026-scripts/sunpos.py in QuitHub/miscellany.

This script does NOT claim to solve the terrain horizon. It prints the
solar geometry and the maximum terrain elevation compatible with an
unobscured lower solar limb at a set of distances.
"""

import math

LAT = 38.865119
LON = 1.355553

# Mid-totality-ish evaluation time used in the chat calculation.
# CEST = UTC+2
LOCAL = (2026, 8, 12, 20, 33, 18)

# Approximate solar angular radius in degrees.
SOLAR_RADIUS_DEG = 0.266

# Observer eye height above local ground/sea level assumption.
EYE_HEIGHT_M = 2.0

# Effective Earth-curvature correction with terrestrial refraction.
# k=0.13 means effective curvature = (1-k) * geometric curvature.
REFRACTION_K = 0.13
EARTH_RADIUS_M = 6_371_000.0


def jd_utc(y, mo, d, h, mi, s):
    if mo <= 2:
        y, mo = y - 1, mo + 12
    A = y // 100
    B = 2 - A + A // 4
    return (
        int(365.25 * (y + 4716))
        + int(30.6001 * (mo + 1))
        + d + B - 1524.5
        + (h + mi / 60 + s / 3600) / 24
    )


def sun_position(jd, lat, lon):
    T = (jd - 2451545.0) / 36525.0
    L0 = (280.46646 + T * (36000.76983 + T * 0.0003032)) % 360
    M = 357.52911 + T * (35999.05029 - 0.0001537 * T)
    Mr = math.radians(M)
    C = (
        math.sin(Mr) * (1.914602 - T * (0.004817 + 0.000014 * T))
        + math.sin(2 * Mr) * (0.019993 - 0.000101 * T)
        + math.sin(3 * Mr) * 0.000289
    )
    true_long = L0 + C
    omega = 125.04 - 1934.136 * T
    lam = true_long - 0.00569 - 0.00478 * math.sin(math.radians(omega))
    eps0 = 23 + (
        26
        + (
            21.448
            - T * (46.8150 + T * (0.00059 - T * 0.001813))
        ) / 60
    ) / 60
    eps = eps0 + 0.00256 * math.cos(math.radians(omega))

    lam_r, eps_r = math.radians(lam), math.radians(eps)
    ra = math.degrees(
        math.atan2(math.cos(eps_r) * math.sin(lam_r), math.cos(lam_r))
    ) % 360
    dec = math.degrees(math.asin(math.sin(eps_r) * math.sin(lam_r)))

    gmst = (
        280.46061837
        + 360.98564736629 * (jd - 2451545.0)
        + 0.000387933 * T * T
        - T * T * T / 38710000.0
    ) % 360

    ha = (gmst + lon - ra) % 360
    if ha > 180:
        ha -= 360

    lat_r, dec_r, ha_r = map(math.radians, (lat, dec, ha))
    alt = math.degrees(
        math.asin(
            math.sin(lat_r) * math.sin(dec_r)
            + math.cos(lat_r) * math.cos(dec_r) * math.cos(ha_r)
        )
    )
    az = math.degrees(
        math.atan2(
            -math.sin(ha_r),
            math.tan(dec_r) * math.cos(lat_r)
            - math.sin(lat_r) * math.cos(ha_r),
        )
    ) % 360

    # Bennett refraction correction near the horizon.
    if alt > -1:
        R = 1.02 / math.tan(
            math.radians(alt + 10.3 / (alt + 5.11))
        ) / 60.0
    else:
        R = 0.0

    return az, alt, alt + R


def curvature_drop_m(distance_m, k=REFRACTION_K):
    """Effective drop of the local horizontal due to Earth curvature."""
    return (1 - k) * distance_m * distance_m / (2 * EARTH_RADIUS_M)


def max_terrain_elevation_m(distance_m, limb_altitude_deg):
    """Maximum terrain elevation (MSL-ish) that stays below the lower limb.

    Assumes observer eye height EYE_HEIGHT_M and applies a small effective
    Earth-curvature correction.
    """
    line_height = EYE_HEIGHT_M + distance_m * math.tan(
        math.radians(limb_altitude_deg)
    )
    return line_height + curvature_drop_m(distance_m)


def main():
    y, mo, d, hh, mm, ss = LOCAL
    jd = jd_utc(y, mo, d, hh - 2, mm, ss)  # CEST -> UTC
    az, geom_alt, apparent_alt = sun_position(jd, LAT, LON)
    lower_limb = apparent_alt - SOLAR_RADIUS_DEG

    print(f"Observer: {LAT:.6f}, {LON:.6f}")
    print(f"Local time: {y:04d}-{mo:02d}-{d:02d} {hh:02d}:{mm:02d}:{ss:02d} CEST")
    print(f"Sun azimuth: {az:.3f}°")
    print(f"Geometric centre altitude: {geom_alt:.3f}°")
    print(f"Apparent centre altitude: {apparent_alt:.3f}°")
    print(f"Approx. lower-limb altitude: {lower_limb:.3f}°")
    print()
    print("Distance   max terrain elevation below lower limb")
    for km in (0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 4.0, 5.0):
        d_m = km * 1000
        h = max_terrain_elevation_m(d_m, lower_limb)
        print(f"{km:4.1f} km   {h:7.1f} m")


if __name__ == "__main__":
    main()
