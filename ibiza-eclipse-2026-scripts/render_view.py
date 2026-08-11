#!/usr/bin/env python3
"""Render the expected WNW view at totality from Es Codolar (cone terrain model)."""
import math
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle

exec(open("viewshed.py").read().split('print(f"Sun at')[0])   # HILLS, terrain_angle
exec(open("sunpos.py").read().split("# Es Codolar")[0])       # sun_position, jd_utc

SPOTS = [
    ("Your spot — NW corner (38.86512, 1.35555)", 38.865119, 1.355553),
    ("Mid-beach — 1.6 km further south (38.8515, 1.3655)", 38.8515, 1.3655),
]
AZ0, AZ1 = 262, 312
SUN_AZ, SUN_ALT, SUN_R = 286.7, 3.12, 0.26
R = 6371000.0

clouds = []
for name, hlat, hlon, hgt, rad in HILLS:
    pts = [(hlat, hlon, hgt)]
    for fr in np.arange(0.04, 1.0, 0.04):
        n = max(60, int(2 * math.pi * fr * rad / 25))
        th = np.linspace(0, 2 * math.pi, n, endpoint=False)
        pts += [(hlat + fr * rad * math.cos(t) / 111190,
                 hlon + fr * rad * math.sin(t) / (111190 * math.cos(math.radians(hlat))),
                 hgt * (1 - fr)) for t in th]
    clouds.append((name, np.array(pts)))

def horizon(olat, olon):
    az_grid = np.arange(AZ0, AZ1, 0.1)
    h = np.full_like(az_grid, -0.045)
    who = np.full(len(az_grid), "sea", dtype=object)
    for name, pts in clouds:
        la1, la2 = math.radians(olat), np.radians(pts[:, 0])
        dlon = np.radians(pts[:, 1] - olon)
        x = np.sin(dlon) * np.cos(la2)
        y = math.cos(la1) * np.sin(la2) - math.sin(la1) * np.cos(la2) * np.cos(dlon)
        br = np.degrees(np.arctan2(x, y)) % 360
        d = R * np.arccos(np.clip(math.sin(la1) * np.sin(la2)
                                  + math.cos(la1) * np.cos(la2) * np.cos(dlon), -1, 1))
        drop = d * d / (2 * R) * 0.87
        ang = np.degrees(np.arctan2(pts[:, 2] - 2 - drop, d))
        idx = np.round((br - AZ0) / 0.1).astype(int)
        ok = (idx >= 0) & (idx < len(az_grid))
        for i, a in zip(idx[ok], ang[ok]):
            if a > h[i]:
                h[i] = a; who[i] = name
    h2 = h.copy()                       # close inter-ring gaps, no wraparound
    for k in (1, 2):
        h2[k:] = np.maximum(h2[k:], h[:-k])
        h2[:-k] = np.maximum(h2[:-k], h[k:])
    return az_grid, h2, who

def sun_path(olat, olon):
    out = []
    for mins in range(0, 82, 2):
        hh, mm = divmod(19 * 60 + 40 + mins, 60)
        a, alt, app = sun_position(jd_utc(2026, 8, 12, hh - 2, mm, 0), olat, olon)
        out.append((a, app))
    return np.array(out)

fig, axes = plt.subplots(2, 1, figsize=(13, 8.6), dpi=140)
fig.patch.set_facecolor("#0d1120")

for ax, (title, olat, olon) in zip(axes, SPOTS):
    az, h, who = horizon(olat, olon)
    grad = np.linspace(0, 1, 256).reshape(-1, 1)
    ax.imshow(grad, extent=[AZ0, AZ1, -0.05, 7], origin="lower", aspect="auto",
              cmap=matplotlib.colors.LinearSegmentedColormap.from_list(
                  "tw", ["#c96a2e", "#8a4a52", "#3c3a66", "#181c38", "#0d1120"]))
    ax.fill_between(az, -0.05, h, color="#05070f", zorder=3)
    ax.plot(az, h, color="black", lw=0.7, zorder=3)
    sp = sun_path(olat, olon)
    ax.plot(sp[:, 0], sp[:, 1], ls=":", color="#ffd9a0", lw=1.1, alpha=0.75, zorder=4)
    for mins, lab in [(0, "19:40"), (20, "20:00"), (40, "20:20"), (64, "20:44")]:
        a, al = sp[mins // 2]
        ax.plot(a, al, "o", ms=2.5, color="#ffd9a0", zorder=4)
        ax.annotate(lab, (a, al), textcoords="offset points", xytext=(7, 3),
                    color="#ffd9a0", fontsize=7, alpha=0.9)
    for r, alpha in [(1.7, 0.05), (1.2, 0.09), (0.85, 0.16), (0.6, 0.28), (0.42, 0.5), (0.33, 0.85)]:
        ax.add_patch(Circle((SUN_AZ, SUN_ALT), r, color="#f5f2e8", alpha=alpha, zorder=5))
    ax.add_patch(Circle((SUN_AZ, SUN_ALT), SUN_R, color="#020204", zorder=6))
    i0 = np.argmin(np.abs(az - SUN_AZ))
    hu = h[max(0, i0 - 5):i0 + 5].max()
    ax.annotate("", xy=(SUN_AZ, SUN_ALT - SUN_R), xytext=(SUN_AZ, hu),
                arrowprops=dict(arrowstyle="<->", color="#7fd4a0", lw=1.2), zorder=7)
    ax.annotate(f"margin {SUN_ALT - SUN_R - hu:.1f}°",
                (SUN_AZ - 5.6, (SUN_ALT - SUN_R + hu) / 2 + 0.05),
                color="#7fd4a0", fontsize=9, zorder=7)
    placed = []
    for name, hlat, hlon, hgt, rad in HILLS:
        short = name.split(" (")[0]
        mask = np.array([w == name for w in who])
        if not mask.any(): continue
        b = az[mask][np.argmax(h[mask])]
        top = h[mask].max()
        if any(abs(b - p) < 6 for p in placed): continue
        if abs(b - SUN_AZ) < 3 and top < SUN_ALT: continue
        placed.append(b)
        ax.annotate(f"{short} ({hgt} m)" if hgt >= 100 else short, (b, top + 0.22),
                    color="#c9cede", fontsize=7.5, ha="center", zorder=7)
    ax.set_xlim(AZ0 + 0.5, AZ1 - 0.5); ax.set_ylim(-0.05, 7)
    ax.set_title(title + "  —  totality 20:33, Sun az 286.7° alt 3.1°",
                 color="#e8e6df", fontsize=10.5, pad=6)
    ax.set_ylabel("altitude (°)", color="#9aa0b4", fontsize=8.5)
    ax.tick_params(colors="#9aa0b4", labelsize=8)
    for s in ax.spines.values(): s.set_color("#3a4060")
    ax.grid(alpha=0.12, color="#8891b0", lw=0.4)
    for a, t in [(270, "W"), (292.5, "WNW"), (307.5, "NW")]:
        ax.annotate(t, (a, 6.6), color="#7880a0", fontsize=8, ha="center")

axes[1].set_xlabel("azimuth (°)", color="#9aa0b4", fontsize=8.5)
fig.suptitle("Es Codolar, Ibiza — expected view at totality, 12 Aug 2026 (cone terrain model, not DEM-verified)",
             color="#c9cede", fontsize=11, y=0.985)
fig.tight_layout(rect=[0, 0, 1, 0.965])
fig.savefig("es-codolar-expected-view.png", facecolor=fig.get_facecolor())
print("saved")
