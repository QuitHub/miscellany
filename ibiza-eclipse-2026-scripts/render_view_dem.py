#!/usr/bin/env python3
"""Expected view of the 12 Aug 2026 total solar eclipse from Es Codolar, Ibiza.

Terrain silhouette driven by real DEM horizon data (horizon.json); falls back to
the cone terrain model from render_view.py when the JSON is absent, so the script
can be tested standalone.

Usage: render_view_dem.py horizon.json out.png
"""
import json
import math
import os
import sys

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Ellipse

HERE = os.path.dirname(os.path.abspath(__file__))

# sun_position(jd, lat, lon) and jd_utc(...) from sunpos.py (functions only)
exec(open(os.path.join(HERE, "sunpos.py")).read().split("# Es Codolar")[0])

AZ0, AZ1 = 262.0, 312.0
YMIN, YMAX = -0.4, 7.0          # slight dip below -0.05 so the sea reads as sea
SEA_TOP = -0.045                # apparent dip of the sea horizon from 2 m eye height
SUN_AZ, SUN_ALT, SUN_R = 286.7, 3.12, 0.26
R_EARTH = 6371000.0

INK = "#e9e7dc"; INK2 = "#98a1b8"; INK3 = "#9aa0b4"; INK_FAINT = "#767e9e"
FEATURE_INK = "#b7bfd4"; TICK_WARM = "#f0c896"
GOOD = "#7fd4a0"; BAD = "#e8975f"


# ---------------------------------------------------------------- data loading

def load_spots(path):
    """Return (spots, terrain_note, dem_mode). Each spot is a dict with
    name/lat/lon/az/horizon/features; horizon and az are numpy arrays."""
    if os.path.exists(path):
        with open(path) as f:
            data = json.load(f)
        spots = []
        for s in data["spots"]:
            spots.append({
                "name": s["name"], "lat": float(s["lat"]), "lon": float(s["lon"]),
                "az": np.asarray(s["az"], dtype=float),
                "horizon": np.asarray(s["horizon"], dtype=float),
                "features": s.get("features", []),
            })
        note = f"terrain DEM-verified: {data.get('title_suffix', 'DEM')}"
        return spots[:3], note, True
    return cone_spots(), "cone terrain model — not DEM-verified", False


def cone_spots():
    """Fallback: rebuild the cone-model horizon from viewshed.py's HILLS."""
    ns = {}
    exec(open(os.path.join(HERE, "viewshed.py")).read().split('print(f"Sun at')[0], ns)
    hills = ns["HILLS"]
    az_grid = np.round(np.arange(AZ0 * 10, AZ1 * 10) / 10.0, 1)

    clouds = []
    for name, hlat, hlon, hgt, rad in hills:
        pts = [(hlat, hlon, hgt)]
        for fr in np.arange(0.04, 1.0, 0.04):
            n = max(60, int(2 * math.pi * fr * rad / 25))
            th = np.linspace(0, 2 * math.pi, n, endpoint=False)
            pts += [(hlat + fr * rad * math.cos(t) / 111190,
                     hlon + fr * rad * math.sin(t) / (111190 * math.cos(math.radians(hlat))),
                     hgt * (1 - fr)) for t in th]
        clouds.append((name, np.array(pts)))

    def horizon(olat, olon):
        h = np.full_like(az_grid, SEA_TOP)
        who = np.full(len(az_grid), "sea", dtype=object)
        for name, pts in clouds:
            la1, la2 = math.radians(olat), np.radians(pts[:, 0])
            dlon = np.radians(pts[:, 1] - olon)
            x = np.sin(dlon) * np.cos(la2)
            y = math.cos(la1) * np.sin(la2) - math.sin(la1) * np.cos(la2) * np.cos(dlon)
            br = np.degrees(np.arctan2(x, y)) % 360
            d = R_EARTH * np.arccos(np.clip(math.sin(la1) * np.sin(la2)
                                            + math.cos(la1) * np.cos(la2) * np.cos(dlon), -1, 1))
            drop = d * d / (2 * R_EARTH) * 0.87
            ang = np.degrees(np.arctan2(pts[:, 2] - 2 - drop, d))
            idx = np.round((br - AZ0) / 0.1).astype(int)
            ok = (idx >= 0) & (idx < len(az_grid))
            for i, a in zip(idx[ok], ang[ok]):
                if a > h[i]:
                    h[i] = a; who[i] = name
        h2 = h.copy()
        for k in (1, 2):
            h2[k:] = np.maximum(h2[k:], h[:-k])
            h2[:-k] = np.maximum(h2[:-k], h[k:])
        return h2, who

    spots = []
    for name, olat, olon in [("Your spot — NW corner (38.86512, 1.35555)", 38.865119, 1.355553),
                             ("Mid-beach — 1.6 km further south (38.8515, 1.3655)", 38.8515, 1.3655)]:
        h, who = horizon(olat, olon)
        feats, placed = [], []
        for hname, hlat, hlon, hgt, rad in hills:
            short = hname.split(" (")[0]
            mask = np.array([w == hname for w in who])
            if not mask.any():
                continue
            b = az_grid[mask][np.argmax(h[mask])]
            top = h[mask].max()
            if any(abs(b - p) < 6 for p in placed):
                continue
            if abs(b - SUN_AZ) < 3 and top < SUN_ALT:
                continue
            placed.append(b)
            feats.append({"az": float(b), "alt": float(top),
                          "label": f"{short} ({hgt} m)" if hgt >= 100 else short})
        spots.append({"name": name, "lat": olat, "lon": olon,
                      "az": az_grid, "horizon": h, "features": feats})
    return spots


# ------------------------------------------------------------------ sun track

def sun_path(olat, olon):
    """(az, apparent alt) every 2 min from 19:40 to 21:00 CEST."""
    out = []
    for mins in range(0, 82, 2):
        hh, mm = divmod(19 * 60 + 40 + mins, 60)
        a, alt, app = sun_position(jd_utc(2026, 8, 12, hh - 2, mm, 0), olat, olon)
        out.append((a, app))
    return np.array(out)


# --------------------------------------------------------------- scene layers

def sky_image():
    """Twilight gradient with a warm sunset wedge low around the Sun's azimuth
    and a whisper of extra darkness aloft near the Sun (the Moon's shadow)."""
    nx, ny = 560, 420
    A, Y = np.meshgrid(np.linspace(AZ0, AZ1, nx), np.linspace(YMIN, YMAX, ny))
    t = (Y - YMIN) / (YMAX - YMIN)
    stops = [0.0, 0.10, 0.28, 0.55, 1.0]
    cols = ["#c96a2e", "#8a4a52", "#3c3a66", "#181c38", "#0b0f1e"]
    img = np.zeros((ny, nx, 3))
    for c in range(3):
        vals = [int(h[1 + 2 * c:3 + 2 * c], 16) / 255 for h in cols]
        img[..., c] = np.interp(t, stops, vals)
    glow = np.exp(-((A - SUN_AZ) / 16.0) ** 2) * np.exp(-np.clip(Y - YMIN, 0, None) / 1.5)
    for c, g in enumerate((1.00, 0.52, 0.22)):
        img[..., c] += 0.26 * g * glow
    shadow = np.exp(-(((A - SUN_AZ) / 9.5) ** 2 + ((Y - 5.2) / 2.8) ** 2))
    img *= 1 - 0.15 * shadow[..., None]
    rng = np.random.default_rng(11)
    img += (rng.random((ny, nx, 1)) - 0.5) * (1.6 / 255)   # dither away banding
    return np.clip(img, 0, 1)


def sea_image():
    """Dusk sea: dark below, faintly lit toward the horizon, warmer toward the
    sunset azimuth."""
    nx, ny = 560, 64
    A, T = np.meshgrid(np.linspace(AZ0, AZ1, nx), np.linspace(0, 1, ny))
    bot, top = "#0c1428", "#2a3d60"
    img = np.zeros((ny, nx, 3))
    for c in range(3):
        v0 = int(bot[1 + 2 * c:3 + 2 * c], 16) / 255
        v1 = int(top[1 + 2 * c:3 + 2 * c], 16) / 255
        img[..., c] = v0 + (v1 - v0) * T ** 1.4
    warm = (np.exp(-((A - SUN_AZ) / 15.0) ** 2) * T ** 1.6
            + 0.7 * np.exp(-((A - SUN_AZ) / 2.6) ** 2) * T ** 2)   # dim glitter path
    for c, g in enumerate((0.34, 0.20, 0.07)):
        img[..., c] += 0.34 * g * warm
    return np.clip(img, 0, 1)


def corona_image(k):
    """Totality corona: steep K-corona falloff plus a handful of streamers laid
    out as radial gaussians, on a screen-circular grid. Returns (rgba, rmax_Rs)."""
    rmax, n = 8.0, 520                      # radius in solar radii
    u = np.linspace(-rmax, rmax, n)
    X, Y = np.meshgrid(u, u)
    r = np.hypot(X, Y)
    th = np.degrees(np.arctan2(Y, X))
    rr = np.maximum(r, 1.0)
    inten = 1.05 * rr ** -2.9 + 0.10 * np.exp(-(rr - 1) / 2.6)
    streamers = [                           # (position angle, width, length Rs, amp)
        (12, 11, 1.7, 0.55), (168, 13, 1.9, 0.60), (196, 9, 1.2, 0.35),
        (345, 10, 1.5, 0.48), (78, 7, 0.8, 0.28), (262, 8, 0.9, 0.26),
    ]
    for ang, sig, length, amp in streamers:
        dth = (th - ang + 180) % 360 - 180
        inten += amp * np.exp(-0.5 * (dth / sig) ** 2) * np.exp(-(rr - 1) / length) * rr ** -0.7
    inten *= np.clip((r - 0.98) / 0.22, 0, 1)      # nothing inside the Moon
    rgba = np.zeros((n, n, 4))
    rgba[..., 0], rgba[..., 1], rgba[..., 2] = 0.99, 0.975, 0.94
    rgba[..., 3] = np.clip(inten, 0, 1) * 0.95
    return rgba, rmax


def draw_stars(ax, k, rng):
    """Sparse faint stars above 4 deg, avoiding the corona; Mercury near 293/6."""
    n = 60
    saz = rng.uniform(AZ0 + 1.2, AZ1 - 1.2, n)
    salt = rng.uniform(4.05, YMAX - 0.15, n)
    keep = np.hypot((saz - SUN_AZ) / k, salt - SUN_ALT) > 0.62
    saz, salt = saz[keep], salt[keep]
    m = len(saz)
    sizes = rng.uniform(0.4, 1.7, m) ** 2 * 2.2
    cols = np.zeros((m, 4))
    warmish = rng.random(m) < 0.3
    cols[:, :3] = np.where(warmish[:, None], (0.91, 0.87, 0.78), (0.81, 0.85, 0.93))
    cols[:, 3] = rng.uniform(0.14, 0.55, m) * np.clip((salt - 3.6) / 3.0, 0.3, 1)
    ax.scatter(saz, salt, s=sizes, c=cols, lw=0, zorder=1.3)
    # Mercury, ~az 293 alt 6 during totality
    ax.scatter([292.9], [6.0], s=64, c=[(0.95, 0.91, 0.82, 0.10)], lw=0, zorder=1.4)
    ax.scatter([292.9], [6.0], s=8, c=[(0.95, 0.92, 0.84, 0.9)], lw=0, zorder=1.5)
    ax.annotate("Mercury", (292.9, 6.0), textcoords="offset points", xytext=(6, 4),
                color=INK_FAINT, fontsize=6.5, zorder=7)


# ------------------------------------------------------------------ main plot

def render(spots, terrain_note, out_png):
    n = len(spots)
    fig_w, fig_h = 13.0, 4.1 * n + 1.05
    fig, axes = plt.subplots(n, 1, figsize=(fig_w, fig_h), dpi=140)
    axes = np.atleast_1d(axes)
    fig.patch.set_facecolor("#0d1120")
    fig.subplots_adjust(left=0.054, right=0.988,
                        top=1 - 0.68 / fig_h, bottom=0.46 / fig_h, hspace=0.30)

    rng = np.random.default_rng(7)
    sky = sky_image()
    sea = sea_image()

    for ax, spot in zip(axes, spots):
        az, h = spot["az"], spot["horizon"]

        # screen aspect: degrees azimuth per degree altitude at equal pixels
        bb = ax.get_position()
        k = ((AZ1 - AZ0) / (bb.width * fig_w)) / ((YMAX - YMIN) / (bb.height * fig_h))

        ax.imshow(sky, extent=[AZ0, AZ1, YMIN, YMAX], origin="lower",
                  aspect="auto", interpolation="bilinear", zorder=0)

        # sea below the horizon dip, with lazy sheen streaks
        ax.imshow(sea, extent=[AZ0, AZ1, YMIN, SEA_TOP], origin="lower",
                  aspect="auto", interpolation="bilinear", zorder=2.55)
        for _ in range(14):
            y = YMIN + (SEA_TOP - YMIN) * rng.uniform(0.12, 0.92)
            xc = rng.uniform(AZ0 + 3, AZ1 - 3)
            half = rng.uniform(1.5, 6.0)
            warm = abs(xc - SUN_AZ) < 9
            ax.plot([xc - half, xc + half], [y, y], lw=rng.uniform(0.5, 0.9),
                    color="#d8b090" if warm else "#8fa3c8",
                    alpha=0.08 + 0.10 * rng.random(), zorder=2.65,
                    solid_capstyle="round")
        sea_line = np.where(h < 0.05, SEA_TOP, np.nan)
        ax.plot(az, sea_line, color="#7c8fb4", lw=0.7, alpha=0.5, zorder=2.7)

        # atmospheric glow where sky meets the silhouette
        for d, a in [(0.55, 0.030), (0.32, 0.045), (0.17, 0.065), (0.08, 0.095)]:
            ax.fill_between(az, h, h + d, color="#e7a56b", alpha=a, lw=0, zorder=2.8)

        draw_stars(ax, k, rng)

        # dotted descent of the Sun with time ticks (off-frame ones self-clip);
        # the sea occludes the path below the sea horizon
        sp = sun_path(spot["lat"], spot["lon"])
        path_alt = np.where(sp[:, 1] >= SEA_TOP, sp[:, 1], np.nan)
        ax.plot(sp[:, 0], path_alt, ls=":", color="#ffd9a0", lw=1.0,
                alpha=0.7, zorder=3.4)
        for mins, lab in [(0, "19:40"), (20, "20:00"), (40, "20:20"), (64, "20:44")]:
            a, al = sp[mins // 2]
            ax.plot(a, al, "o", ms=2.4, color="#ffd9a0", zorder=3.45)
            ax.annotate(lab, (a, al), textcoords="offset points", xytext=(6, 4),
                        color=TICK_WARM, fontsize=6.5, alpha=0.95, zorder=7)

        # eclipsed Sun: corona streamers + black Moon disc (circular on screen)
        cor, rmax = corona_image(k)
        ax.imshow(cor, extent=[SUN_AZ - rmax * SUN_R * k, SUN_AZ + rmax * SUN_R * k,
                               SUN_ALT - rmax * SUN_R, SUN_ALT + rmax * SUN_R],
                  origin="lower", aspect="auto", interpolation="bilinear", zorder=5)
        ax.add_patch(Ellipse((SUN_AZ, SUN_ALT), 2 * SUN_R * k, 2 * SUN_R,
                             facecolor="#020205", edgecolor="none", zorder=6))

        # terrain silhouette above the corona so real ridges genuinely occlude
        ax.fill_between(az, SEA_TOP, np.maximum(h, SEA_TOP),
                        color="#04060d", lw=0, zorder=6.4)
        ax.plot(az, np.maximum(h, SEA_TOP), color="black", lw=0.7, zorder=6.45)

        # margin between the Sun's lower limb and the terrain under it
        band = np.abs(az - SUN_AZ) <= 0.5
        hu = h[band].max() if band.any() else SEA_TOP
        limb = SUN_ALT - SUN_R
        margin = limb - hu
        col = GOOD if margin > 0 else BAD
        ax.annotate("", xy=(SUN_AZ, limb), xytext=(SUN_AZ, hu),
                    arrowprops=dict(arrowstyle="<->", color=col, lw=1.2,
                                    shrinkA=0, shrinkB=0), zorder=7)
        label = (f"margin {margin:.2f}°" if margin > 0
                 else f"limb {-margin:.2f}° behind ridge")
        ax.annotate(label, (SUN_AZ - 1.6, (limb + hu) / 2), ha="right", va="center",
                    color=col, fontsize=8.5, zorder=7)

        # named features from the DEM data; labels near the Sun dodge sideways
        # so they never collide with the disc, corona or margin arrow
        for f in spot["features"]:
            if abs(f["az"] - SUN_AZ) < 2.2:
                lx, ly, ha = SUN_AZ + 2.7, max(f["alt"] + 0.28, 2.1), "left"
                if abs(ly - SUN_ALT) < 0.55:
                    ly = SUN_ALT + 0.62
                ax.plot([f["az"] + 0.12, lx - 0.25], [f["alt"] + 0.06, ly - 0.03],
                        color=FEATURE_INK, lw=0.5, alpha=0.4, zorder=7.2)
            else:
                lx, ly, ha = f["az"], f["alt"] + 0.24, "center"
                ax.plot([f["az"], f["az"]], [f["alt"] + 0.05, ly - 0.07],
                        color=FEATURE_INK, lw=0.5, alpha=0.45, zorder=7.2)
            ax.annotate(f["label"], (lx, ly), ha=ha, va="center",
                        color=FEATURE_INK, fontsize=7, zorder=7.2)

        # frame furniture
        for a, t in [(270, "W"), (292.5, "WNW"), (307.5, "NW")]:
            ax.annotate(t, (a, 6.55), color=INK_FAINT, fontsize=7.5,
                        ha="center", zorder=7)
        ax.set_xlim(AZ0 + 0.5, AZ1 - 0.5)
        ax.set_ylim(YMIN, YMAX)
        ax.set_xticks(range(265, 311, 5))
        ax.set_xticks(range(263, 312), minor=True)
        ax.set_yticks(range(0, 8))
        ax.set_title(spot["name"], loc="left", color="#dfe0d9", fontsize=9.5,
                     fontweight="bold", pad=5)
        ax.set_ylabel("apparent altitude (°)", color=INK3, fontsize=8)
        ax.tick_params(colors=INK3, labelsize=7.5)
        ax.tick_params(which="minor", length=2, colors="#3a4060")
        for s in ax.spines.values():
            s.set_color("#3a4060")
        ax.grid(axis="y", color="#8891b0", alpha=0.08, lw=0.4, zorder=1.0)

    axes[-1].set_xlabel("azimuth (°)", color=INK3, fontsize=8)
    fig.text(0.5, 1 - 0.22 / fig_h,
             "Total solar eclipse over Es Codolar, Ibiza — 12 Aug 2026",
             ha="center", color=INK, fontsize=13)
    fig.text(0.5, 1 - 0.47 / fig_h,
             "expected view at totality 20:32:34–20:33:41 CEST (67 s) · "
             f"Sun az 286.7° alt 3.1° · {terrain_note}",
             ha="center", color=INK2, fontsize=8.5)
    fig.savefig(out_png, facecolor=fig.get_facecolor())
    print(f"saved {out_png}")


if __name__ == "__main__":
    json_path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "horizon.json")
    out_png = sys.argv[2] if len(sys.argv) > 2 else os.path.join(HERE, "es-codolar-dem-view.png")
    spots, note, dem = load_spots(json_path)
    render(spots, note, out_png)
