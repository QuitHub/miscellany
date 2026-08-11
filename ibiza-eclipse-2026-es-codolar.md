# Will the 12 August 2026 total solar eclipse be visible from Es Codolar beach, Ibiza?

**Verdict: Yes — from the southern half of the beach. The north-central stretch
(nearest the airport access road) risks having totality blocked by a 160 m hill.**

Report date: 11 August 2026 (eclipse is the following evening).

---

## 1. The problem

Es Codolar is the long pebble beach immediately west of Ibiza airport, inside the
path of totality for the 12 August 2026 total solar eclipse. Totality there is
short and happens with the Sun almost on the horizon:

| Event | Time (CEST) | Sun azimuth | Sun apparent altitude |
|---|---|---|---|
| Totality begins | 20:32:34 | 286.6° | 3.23° |
| Maximum eclipse | 20:33:08 | 286.7° | 3.12° |
| Totality ends | 20:33:41 | 286.8° | 3.03° |
| Sunset (sea horizon) | ~20:52 | 289.7° | 0° |

Duration of totality: **~1 min 07–11 s**. Solar disk angular radius: 0.26°, so the
Sun's **lower limb sits at just 2.86°** at maximum eclipse.

Consequence: any terrain on the WNW skyline subtending more than ~2.9° hides
totality entirely. At 3 km range that is only a ~150 m hill; at 9 km, a ~450 m
mountain. The question is therefore entirely about the local horizon profile at
azimuth ≈ 287°.

## 2. Method

Elevation-tile APIs (OpenTopoData, Open-Elevation, OpenTopography) were not
reachable from the analysis environment, so the horizon was reconstructed from
first principles:

1. **Sun position** — NOAA solar position algorithm (accuracy ~0.01°), with
   Bennett refraction correction for apparent altitude, evaluated at
   38.8645° N, 1.3540° E for the published totality times. Results agree with
   timeanddate.com ("3° above the WNW horizon").
2. **Coastline geometry** — GSHHS *full-resolution* coastline (≈50–100 m detail),
   extracted from the `basemap-data-hires` PyPI package. This fixes the exact
   shape and orientation of the beach and the footprints of every promontory on
   the sightline.
3. **Terrain heights** — published, independently verifiable summit elevations
   (Wikipedia, PeakVisor), modelled as cones draped to the mapped coastal
   footprints. Earth curvature and terrestrial refraction (k = 0.13) included;
   observer eye height 2 m.
4. **Viewshed** — for five observer points along the mapped beach line, the
   maximum terrain angle inside the Sun's azimuth window (disk width + azimuth
   drift during totality) was computed, plus the post-totality time at which the
   descending Sun drops behind terrain.

### Terrain features on or near the sightline

| Feature | Height | Position | Bearing/role from beach |
|---|---|---|---|
| Sa Caleta headland | ~22 m | 38.8685° N, 1.3480° E | close, low — harmless |
| **Puig des Jondal** | **160 m** | ≈38.864° N, 1.330° E | **2.2–2.9 km WNW — the decisive obstruction** |
| Porroig peninsula | ~55 m | 38.866° N, 1.297° E | 5–6 km, ~0.5° — negligible |
| Puig d'en Serra / Es Cubells ridge | 271 m | ≈38.876° N, 1.268° E | 8–9 km, 1.1–1.7° — sets the far skyline |
| Sa Talaiassa (island high point) | 475 m | 38.9114° N, 1.2742° E | bears ~300°+, well north of the Sun — **not** a factor |
| Es Vedrà | 382 m | 38.8672° N, 1.1936° E | ~15 km at az ~277–281°, 1.4° high — scenic, left of the Sun |

A commonly repeated worry — that the setting Sun would sink behind the Sa
Talaiassa massif — does not survive the geometry: the summit bears ≈300°+ from
every point on the beach, more than 13° north of the Sun.

Note the beach's orientation: GSHHS shows the main strand trending NNW–SSE
(Sa Caleta headland down to Cap des Falcó), so the shore faces **WSW–W**, not
south as some beach guides state. The Sun at 287° is only ~20–50° right of the
shore normal — this is why the beach works at all.

## 3. Results

Horizon angle in the Sun's azimuth window at totality, by position on the beach
(south → north):

| Spot | WNW horizon | Limiting feature | Totality | Sun lost behind terrain |
|---|---|---|---|---|
| South end (Cap des Falcó) | 0.38° | Es Cubells ridge, 9.1 km | ✅ clear, margin 2.5° | ~20:50 |
| South-mid | 1.14° | Es Cubells ridge, 9.1 km | ✅ clear, margin 1.7° | ~20:45 |
| Mid-beach | 1.48° | Es Cubells ridge, 8.6 km | ✅ clear, margin 1.4° | ~20:42 |
| **North-mid** | **3.07°** | **Puig des Jondal, 2.9 km, az 286.5°** | ⚠️ **clipped/blocked** | ~20:38 |
| North end (airport access) | ~1–2° | model least reliable here | 🤏 marginal | ~20:41 |

The alignment of Puig des Jondal with the eclipse azimuth is nearly exact from
the north-central stretch of the beach: summit bearing 286.5° vs Sun at 286.7°,
angular height ≈ 3.1° vs solar lower limb 2.86°. That is the one part of Es
Codolar where a one-minute totality can vanish behind a hill.

From the very north end the sightline passes over the hill's lower northern
flank and is probably clear, but this is where the cone approximation of the
ridge is weakest — treat as unreliable rather than safe.

## 4. Recommendations

1. **Position in the southern half of the beach.** From the usual access at the
   airport roundabout, walk **south (left, toward Cap des Falcó) for 20–25
   minutes**. Margin against terrain grows monotonically southward, reaching
   ~2.5° at the south end — enough to absorb any modelling error.
2. **Field-check at ~20:15**: the partially eclipsed Sun must stand above open
   sea. If it stands above or near a hill, keep walking south — the Sun only
   gets lower from there.
3. The southern end also preserves the post-totality partial phase nearly to
   true sunset (~20:50), with the crescent Sun sinking into the sea.
4. Es Vedrà will be silhouetted a few degrees to the left of the eclipsed Sun —
   worth framing in photographs.
5. Certified eclipse glasses at all times except during totality itself.
6. Weather is the one variable geometry cannot fix — check cloud forecasts on
   the morning of the 12th; the fallback with the same open WNW sea horizon is
   the west coast (Cala Comte / Cala Bassa), ~30 min away.

Companion files: `ibiza-eclipse-2026-verification-prompt.md` (paste-ready DEM
verification prompt for a Claude session with internet access) and
`ibiza-eclipse-2026-scripts/` (solar position + viewshed scripts used here).

## 5. Uncertainty

- Individual horizon angles carry roughly ±0.3–0.5° from the cone terrain
  approximation and summit-placement precision; the qualitative picture (south =
  safe, north-central = at risk) is robust because the southern margins exceed
  the uncertainty severalfold.
- Sun-position and timing figures are good to ≲0.05° / seconds and cross-check
  against published circumstances.
- No ground-truth DEM was available in the analysis environment; a 30 m DEM
  profile along azimuth 286.7° would sharpen the boundary of the blocked zone
  but is unlikely to move it by more than a few hundred metres of beach.

## 6. Addendum: the NW-corner spot (38.865119, 1.355553)

A specific candidate spot at the beach's northwest corner (by the Sa Caleta
bend, ~1 min from the north access parking) was analysed separately:

- Worst obstruction: **1.86°** — the *northern shoulder* of the Cala Jondal
  promontory at only 1.9 km, az 286.8°. Nominal margin below the solar lower
  limb: **1.0°**.
- Unlike the southern half of the beach (critical sightline over open sea),
  this sightline runs **over land for its entire length**, where the cone
  terrain model is weakest. Decision threshold: if real terrain at the
  1.5–2.5 km crossing (near 38.871, 1.331) is ≤ ~95 m the spot is clear;
  ≥ ~115 m and totality is blocked. DEM verification required — see
  `ibiza-eclipse-2026-verification-prompt.md`.
- **The blocked zone is non-monotonic along the beach**: this corner looks over
  the hill's low north flank; 500–1200 m south of it the 160 m summit aligns
  exactly with the Sun (blocked); the reliably safe water-horizon stretch
  starts ~1.6 km south (south of ≈38.852 N). The worst mistake is standing in
  between.
- No same-day escape: the Sun only sinks to terrain-relevant altitudes ~2 min
  before totality, far too late to relocate. The choice must be made from DEM
  data beforehand; without data, default to the southern half.

## 7. Flight logistics (departure IBZ 22:25 the same evening)

Es Codolar's advantage: it is the only totality beach walkable to the terminal.

| Time | Action |
|---|---|
| Afternoon | Return rental car; drop checked bag early if the airline allows; online check-in. Carry-on only makes the plan trivial. |
| ~19:15 | Arrive north access; walk to chosen spot. |
| 19:39 | Partial phase begins — glasses on. |
| 20:32:34 | Totality (glasses off, 67 s). |
| 20:45 | Hard deadline to start walking back (20:35 if a bag must be dropped by ~21:40). |
| ~21:00–21:15 | Terminal via pre-booked taxi from north access (5 min) or on foot (~30–35 min from the NW corner). |
| ~21:50 | At gate. Gate closes ~21:55–22:05. |

Risks: security surge (every departing eclipse-watcher arrives at once) and
counting on an un-booked taxi. Road congestion is irrelevant if walking.

## 8. Sources

- [timeanddate.com — eclipse circumstances for Ibiza, 12 Aug 2026](https://www.timeanddate.com/eclipse/in/spain/ibiza?iso=20260812)
- [Instituto Geográfico Nacional (Spain) — total solar eclipse 12 Aug 2026](https://astronomia.ign.es/en/eclipses-de-sol-y-luna/eclipse-total-sol-de-12-de-agosto-2026)
- [Wikipedia — Solar eclipse of August 12, 2026](https://en.wikipedia.org/wiki/Solar_eclipse_of_August_12,_2026)
- [Wikipedia — Sa Talaiassa](https://en.wikipedia.org/wiki/Sa_Talaiassa)
- [PeakVisor — Puig d'en Serra](https://peakvisor.com/peak/puig-d-en-serra.html)
- [Welcome to Ibiza — Es Codolar beach](https://welcometoibiza.com/en/playas-calas/playa-es-codolar/)
- GSHHS full-resolution coastline via the `basemap-data-hires` package
- NOAA solar position algorithm (Meeus/NOAA formulation)
