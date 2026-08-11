# DEM verification prompt — Ibiza eclipse, Es Codolar beach

Paste everything below the rule into a Claude session with unrestricted internet
access. Companion report: `ibiza-eclipse-2026-es-codolar.md`. Reference scripts
(solar position + cone-model viewshed): `ibiza-eclipse-2026-scripts/`.

---

I'm watching the total solar eclipse this evening (12 Aug 2026) from Es Codolar
beach, Ibiza (the long pebble beach just west of the airport), and I must catch a
22:25 flight from Ibiza airport afterwards. A prior analysis (coastline data +
published summit heights, no DEM) produced verdicts that need checking against a
real DEM. You have internet access — use real elevation data, not estimates.
Open-Meteo needs no API key and is the preferred source.

## Fixed astronomical facts (already computed and cross-checked — don't re-derive)

- Totality: 20:32:34 → 20:33:41 CEST; maximum eclipse 20:33:08; partial phase
  from ~19:39; sea-horizon sunset ~20:52.
- Sun at maximum eclipse: azimuth **286.7°**, apparent altitude of disk center
  **3.12°**; solar angular radius 0.26°, so the **lower limb is at 2.86°**.
- During totality the azimuth drifts 286.6° → 286.8°.
- After totality the Sun descends ~0.168°/min while azimuth increases
  ~0.155°/min.
- Terrain taller than **2.86°** on the sightline hides part of totality; taller
  than **3.38°** hides all of it.

## Task 1 — terrain profiles (Open-Meteo elevation API, Copernicus GLO-90)

Endpoint (up to 100 points per call, comma-separated lists):

    https://api.open-meteo.com/v1/elevation?latitude=LAT1,LAT2,...&longitude=LON1,LON2,...

For each observer below (eye height 2 m), build the terrain profile along
azimuth 286.7°, and also sweep 286.2°–287.2° in 0.1° steps (disk width + drift).
Per km travelled from the observer: Δlat = +0.00263°, Δlon = −0.01104°.
Sample every 100 m from 0.2 km to 12 km. For each sample:

    drop  = dist² / (2·6371000) · (1 − 0.13)      # curvature minus refraction
    angle = atan2(elev − 2 − drop, dist)           # degrees

Observers (south → north):

1. South end (Cap des Falcó): 38.8400, 1.3690
2. South-mid: 38.8470, 1.3690
3. Mid-beach: 38.8515, 1.3655
4. North-mid: 38.8565, 1.3625
5. North end (airport-road access): 38.8615, 1.3592
6. **MY PLANNED SPOT (NW corner): 38.865119, 1.355553** — highest priority

Sanity checks before trusting results: Sa Talaiassa (38.9114, 1.2742) must
return ≈475 m; profiles from observers 1–3 must be ≈0 m (open sea) for most of
their length. GLO-90 is 90 m resolution and can shave sharp ridge crests: if a
verdict lands in an ambiguous band, cross-check the critical samples against a
30 m source (OpenTopoData `srtm30m` or `eudem25m`: 
`https://api.opentopodata.org/v1/srtm30m?locations=lat,lon|lat,lon|...`) and
take the pessimistic (higher-terrain) reading.

**Gold standard, if you can reach it:** Spain's IGN **PNOA MDT05** (5 m lidar
DEM, via the IGN download centre or WCS services at ign.es). At 5 m resolution
the Jondal-shoulder question stops being ambiguous entirely. Use Open-Meteo
for the full sweep, MDT05 for the decisive 1–3 km window from observer 6.

**Clearance ladder for observer 6** (from `exact_point.py`, lower limb 2.828°
at 20:33:18 CEST, eye 2 m, curvature k=0.13): terrain on the eclipse bearing
must stay below **26.7 m @ 0.5 km · 51.5 m @ 1.0 km · 76.3 m @ 1.5 km ·
101.1 m @ 2.0 km · 125.9 m @ 2.5 km · 150.8 m @ 3.0 km · 200.7 m @ 4.0 km ·
250.7 m @ 5.0 km** for the whole solar disc to stay visible. Compare DEM
samples directly against this table — no angle math needed. Run
`ibiza-eclipse-2026-scripts/exact_point.py` to regenerate it for any distance.

**Do not check a single ray.** The solar disc is 0.53° wide and drifts
286.6°→286.8° during totality: a verdict requires the terrain maximum across
the full **286.2°–287.2° fan**, not just the 286.74° centreline — a notch in
the ridge can pass one ray while the ridge still clips the limb.

## Task 2 — verdicts

Per observer report: max terrain angle in the Sun's azimuth window, the
feature/distance causing it, verdict (**CLEAR** < 2.86° with stated margin,
**CLIPPED** 2.86–3.38°, **BLOCKED** > 3.38°), and the post-totality time at
which the descending Sun (rates above) drops behind the terrain profile.

Hypotheses to confirm or falsify (from the prior no-DEM analysis):

- Observer 6 (my spot): worst obstruction ≈1.9° from the **north shoulder of
  the Cala Jondal promontory at 1.9–2.2 km** (near 38.871, 1.331). Decision
  rule: max elevation in the 1.5–2.5 km window ≲95 m at 1.9 km / ≲110 m at
  2.2 km → CLEAR; ≥115 m → BLOCKED. This sightline is over land the whole way,
  so it carries the largest model risk — this is the main thing I need checked.
- Observer 4 (north-mid): Puig des Jondal summit (160 m, ~2.9 km, az ≈286.5°)
  crests ≈3.1° → clipped/blocked. The blocked zone is expected to be
  non-monotonic along the beach: my NW corner clears the hill's low flank,
  500–1200 m south of it the summit aligns with the Sun, and the reliably safe
  water-horizon stretch starts ~1.6 km south of my spot (south of ≈38.852).
- Observers 1–3: horizon ≤1.5° (sea, then Es Cubells/Puig d'en Serra ridge
  271 m at 8–9 km) → CLEAR by ≥1.4°; Sun visible until ~20:42–20:50.
- Sa Talaiassa (475 m) bears ≈300°+ from the whole beach → irrelevant.

Also locate the safe/blocked boundary along the beach as "metres north of Cap
des Falcó (38.8304, 1.3708)".

## Task 3 — cloud forecast for the eclipse hour

    https://api.open-meteo.com/v1/forecast?latitude=38.865&longitude=1.356&hourly=cloud_cover,cloud_cover_low,cloud_cover_mid,cloud_cover_high&timezone=Europe%2FMadrid&start_date=2026-08-12&end_date=2026-08-12

Report 19:00–21:00 CEST. Because the Sun is only 3° high, cloud ON THE WNW
HORIZON matters more than cloud overhead: pull the same forecast for a point
~30–50 km WNW along the sightline (e.g. 38.95, 0.95, over the sea toward
Valencia) — that is the sky the eclipse actually happens in. Distant cirrus can
kill a 3°-altitude eclipse under a locally clear sky. Say explicitly whether
high cloud threatens the 20:30 sightline.

## Task 4 — re-render the expected view from real terrain

`ibiza-eclipse-2026-scripts/render_view.py` draws a two-panel panorama of the
totality view (horizon silhouette, eclipsed Sun with corona, Sun descent path
with time ticks, terrain-margin arrows). It currently uses the cone terrain
model via its `horizon()` function — the only model-dependent part. Replace
`horizon()` with one that returns (azimuth_grid, horizon_angles) computed from
your DEM profiles over the same 262°–312° azimuth range (0.1° steps, same
angle formula as Task 1), then regenerate the PNG for observer 6 and
mid-beach. Needs only `numpy` and `matplotlib` (`pip install numpy
matplotlib`); the scripts are otherwise stdlib. Save as
`ibiza-eclipse-2026-expected-view-dem.png`, show it to me, and note visually
where the Sun sits relative to the real skyline.

## Task 5 — final recommendation

I am at the airport at 22:25 (gate closes ~21:55–22:05; bag drop ~21:40 if I
can't drop luggage earlier). Walking my spot → terminal is ~30–35 min; from
mid-beach add ~15–20 min of slow pebble walking; taxi from the north access is
~5 min if pre-booked. Weigh the DEM verdicts against the exit logistics and
tell me, in one line, exactly where to stand (coordinates), when to start
walking back, and whether my planned spot at 38.865119, 1.355553 is safe.
