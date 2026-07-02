"""Render the two primary broad-evidence figures as dependency-free SVG.

Primary product 1 — direction map: per-route sign compatibility of the
source-adjudicated direction anchors, oriented to each channel's model
expectation.

Primary product 2 — yield meta-analysis: direct-route yield by screen group, and
the priority-vs-nonpriority enrichment forest (odds ratios, log scale).

Both figures are computed from committed inputs only, so they reproduce in the CI
environment with no third-party plotting dependency. They visualise a
deliberately small evidence base honestly: bar lengths are cluster counts, not
effect sizes, and no abstract or query count is drawn as a measured effect.

Usage:
    python scripts/plot_broad_evidence_primary_figures.py \
      empirical/broad_reality_evidence/broad_route_records.csv \
      empirical/broad_reality_evidence/priority_leak_audit/priority_leak_audit_yield_by_route_group_v1.csv \
      empirical/broad_reality_evidence/figures
"""

from __future__ import annotations

import argparse
import math
from collections import Counter
from pathlib import Path

from trait_architecture.broad_meta_analysis import (
    ROUTE_EXPECTED_SIGN,
    direction_map,
    read_csv_rows,
)
from trait_architecture.evidence_yield_meta_analysis import AUDIT_FIELDS, read_rows
from trait_architecture.evidence_yield_meta_model import priority_screen_meta

# Validated light-surface palette (dataviz reference instance).
SURFACE = "#fcfcfb"
INK = "#0b0b0b"
INK2 = "#52514e"
MUTED = "#8a8983"
GRID = "#e8e7e2"
AXIS = "#6f6e69"
COMPATIBLE = "#2a78d6"   # diverging cool pole
CONTRADICTORY = "#e34948"  # diverging warm pole
MIXED = "#b6b5af"        # neutral
UNINFORMATIVE = "#dcdbd5"
PRIORITY = "#2a78d6"     # categorical slot 1
NONPRIORITY = "#1baf7a"  # categorical slot 2

# Model display order and human labels for the four direct channels.
ROUTE_ORDER = ("A_to_pollination", "A_to_antagonism", "B_to_antagonism", "B_to_pollination")
ROUTE_LABEL = {
    "A_to_pollination": "A → pollinator",
    "A_to_antagonism": "A → antagonist",
    "B_to_antagonism": "B → antagonist",
    "B_to_pollination": "B → pollinator",
    "joint_channels": "joint channels",
}


def _esc(text: object) -> str:
    return str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _text(x: float, y: float, s: object, *, size: float = 13, fill: str = INK,
          anchor: str = "start", weight: str = "normal") -> str:
    return (
        f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" fill="{fill}" '
        f'text-anchor="{anchor}" font-weight="{weight}" '
        f'font-family="Helvetica, Arial, sans-serif">{_esc(s)}</text>'
    )


def _rect(x: float, y: float, w: float, h: float, fill: str, *, rx: float = 2) -> str:
    return f'<rect x="{x:.1f}" y="{y:.1f}" width="{max(0.0, w):.1f}" height="{h:.1f}" rx="{rx}" fill="{fill}"/>'


def _line(x1: float, y1: float, x2: float, y2: float, stroke: str, width: float = 1) -> str:
    return f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{stroke}" stroke-width="{width}"/>'


def _svg(width: int, height: int, body: str) -> str:
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" font-family="Helvetica, Arial, sans-serif">'
        f'<rect width="{width}" height="{height}" fill="{SURFACE}"/>{body}</svg>'
    )


# --------------------------------------------------------------------------- #
# Primary product 1: direction map
# --------------------------------------------------------------------------- #

def _route_sign_tallies(records: list[dict[str, str]]) -> dict[str, Counter]:
    """Count primary-sign independent clusters per route by model compatibility."""
    tallies: dict[str, Counter] = {route: Counter() for route in ROUTE_ORDER}
    for row in records:
        if row.get("record_status") != "included_for_direction_map":
            continue
        if row.get("is_primary_sign_record", "").lower() not in {"true", "1", "yes", "y"}:
            continue
        route = row.get("route", "")
        if route not in tallies:
            continue
        expected = ROUTE_EXPECTED_SIGN[route]
        direction = row.get("reported_direction", "")
        if direction == expected:
            tallies[route]["compatible"] += 1
        elif direction in {"positive", "negative"}:
            tallies[route]["contradictory"] += 1
        elif direction == "mixed":
            tallies[route]["mixed"] += 1
        else:  # null, not_reported
            tallies[route]["uninformative"] += 1
    return tallies


def figure_direction_map(records: list[dict[str, str]]) -> str:
    tallies = _route_sign_tallies(records)
    cells = {(c["route"], c["trait_class"], c["outcome_class"], c["design_class"]): c
             for c in direction_map(records)}
    read_cells = {route: [c for (r, *_), c in cells.items()
                          if r == route and c["direction_map_status"] != "insufficient_directional_clusters"]
                  for route in ROUTE_ORDER}

    width, top = 980, 92
    row_h, row_gap = 40, 18
    left, plot_w = 172, 380
    STATUS_SHORT = {
        "mostly_compatible_with_channel_assumption": "mostly compatible",
        "mostly_contradictory_to_channel_assumption": "mostly contradictory",
        "mixed_or_context_dependent": "mixed / context-dependent",
    }
    max_total = max(sum(t.values()) for t in tallies.values()) or 1
    segments = (("compatible", COMPATIBLE), ("contradictory", CONTRADICTORY),
                ("mixed", MIXED), ("uninformative", UNINFORMATIVE))

    body = [
        _text(36, 38, "Direction map: source-adjudicated sign compatibility by channel", size=18, weight="bold"),
        _text(36, 60, "Bars are independent study-cluster counts (not effect sizes). Colour = agreement with the channel's model-expected sign.",
              size=12, fill=INK2),
        _text(36, 76, "Fixed corpus; primary-sign records only. A sign is read only where a route×trait×outcome×design cell reaches k≥3 clusters.",
              size=12, fill=MUTED),
    ]

    # x gridlines at integer cluster counts
    axis_y = top + len(ROUTE_ORDER) * (row_h + row_gap)
    for k in range(max_total + 1):
        gx = left + plot_w * k / max_total
        body.append(_line(gx, top - 6, gx, axis_y, GRID))
        body.append(_text(gx, axis_y + 16, k, size=11, fill=MUTED, anchor="middle"))
    body.append(_text(left + plot_w / 2, axis_y + 34, "independent study clusters", size=12, fill=INK2, anchor="middle"))

    for i, route in enumerate(ROUTE_ORDER):
        y = top + i * (row_h + row_gap)
        expected = ROUTE_EXPECTED_SIGN[route]
        sign = "+" if expected == "positive" else "−"
        body.append(_text(36, y + row_h / 2 - 2, ROUTE_LABEL[route], size=14, weight="bold"))
        body.append(_text(36, y + row_h / 2 + 15, f"expected {sign}", size=11, fill=MUTED))
        x = left
        for name, colour in segments:
            n = tallies[route][name]
            if n == 0:
                continue
            seg_w = plot_w * n / max_total
            body.append(_rect(x + 1, y, seg_w - 2, row_h, colour))  # 2px surface gap between fills
            if seg_w > 16:
                lab_fill = "#ffffff" if name in {"compatible", "contradictory"} else INK
                body.append(_text(x + seg_w / 2, y + row_h / 2 + 4, n, size=12, fill=lab_fill, anchor="middle", weight="bold"))
            x += seg_w
        total = sum(tallies[route].values())
        passed = read_cells[route]
        note = (f"{STATUS_SHORT.get(passed[0]['direction_map_status'], passed[0]['direction_map_status'])} (k={passed[0]['independent_clusters']})"
                if passed else "no cell at k≥3")
        note_fill = COMPATIBLE if passed else MUTED
        body.append(_text(left + plot_w + 14, y + row_h / 2 - 2, f"n={total}", size=12, fill=INK2))
        body.append(_text(left + plot_w + 14, y + row_h / 2 + 15, note, size=11, fill=note_fill))

    # legend — fixed two-column grid so nothing overflows
    ly = axis_y + 56
    columns = [36, 300, 540, 760]
    labels = {"compatible": "compatible with expected sign", "contradictory": "contradictory",
              "mixed": "mixed / context-dependent", "uninformative": "null or not reported"}
    for (name, colour), lx in zip(segments, columns):
        body.append(_rect(lx, ly - 11, 14, 14, colour))
        body.append(_text(lx + 20, ly, labels[name], size=12, fill=INK2))

    return _svg(width, ly + 24, "".join(body))


# --------------------------------------------------------------------------- #
# Primary product 2: yield meta-analysis
# --------------------------------------------------------------------------- #

def figure_yield(audit_rows: list[dict[str, str]]) -> str:
    by_key = {(r["route_family_audit"], r["audit_group"]): r for r in audit_rows}
    routes = sorted({r for r, _ in by_key})

    def yield_of(route: str, group: str) -> float:
        row = by_key.get((route, group))
        if not row:
            return 0.0
        screenable = int(row["route_screenable_rows"])
        return int(row["direct_route_present_rows"]) / screenable if screenable else 0.0

    effects, summary = priority_screen_meta(audit_rows)
    effect_by_route = {e["route"]: e for e in effects}

    width = 1140
    top = 92
    row_h, row_gap = 26, 20
    n_rows = len(routes)
    block = row_h * 2 + row_gap
    axis_y = top + n_rows * block

    body = [
        _text(36, 38, "Yield meta-analysis: direct-route evidence yield and screen enrichment", size=18, weight="bold"),
        _text(36, 60, "Left: fraction of screenable audit rows with a direct route, by priority vs biological-nonpriority screen group.",
              size=12, fill=INK2),
        _text(36, 76, "Right: priority-vs-nonpriority odds ratio per route with 95% CI, and the random-effects pooled estimate. Methodological, not a biological effect.",
              size=12, fill=MUTED),
    ]

    # ---- Panel A: grouped yield bars ----
    aleft, aplot = 168, 250
    ymax = 0.32
    for frac in (0.0, 0.1, 0.2, 0.3):
        gx = aleft + aplot * frac / ymax
        body.append(_line(gx, top - 6, gx, axis_y, GRID))
        body.append(_text(gx, axis_y + 16, f"{frac:.1f}", size=11, fill=MUTED, anchor="middle"))
    body.append(_text(aleft + aplot / 2, axis_y + 34, "direct-route yield", size=12, fill=INK2, anchor="middle"))

    for i, route in enumerate(routes):
        y = top + i * block
        body.append(_text(36, y + row_h + 2, ROUTE_LABEL.get(route, route), size=13, weight="bold"))
        for j, (group, colour) in enumerate((("priority", PRIORITY), ("biological_nonpriority", NONPRIORITY))):
            val = yield_of(route, group)
            by = y + j * row_h
            bw = aplot * min(val, ymax) / ymax
            body.append(_rect(aleft, by + 2, bw, row_h - 4, colour))
            body.append(_text(aleft + bw + 6, by + row_h / 2 + 4, f"{val:.3f}", size=11, fill=INK2))

    # panel A legend
    ly = axis_y + 54
    for group, colour, label in (("priority", PRIORITY, "priority screen"),
                                 ("nonpriority", NONPRIORITY, "biological non-priority")):
        body.append(_rect(36 if group == "priority" else 200, ly - 11, 14, 14, colour))
        body.append(_text((36 if group == "priority" else 200) + 20, ly, label, size=12, fill=INK2))

    # ---- Panel B: enrichment forest (log-scale OR) ----
    bleft, bplot = 640, 250
    or_min, or_max = 0.03, 40.0

    def or_x(value: float) -> float:
        t = (math.log10(value) - math.log10(or_min)) / (math.log10(or_max) - math.log10(or_min))
        return bleft + bplot * min(1.0, max(0.0, t))

    for tick in (0.1, 1.0, 10.0):
        gx = or_x(tick)
        body.append(_line(gx, top - 6, gx, axis_y, GRID if tick != 1.0 else AXIS))
        body.append(_text(gx, axis_y + 16, f"{tick:g}", size=11, fill=MUTED, anchor="middle"))
    body.append(_text(bleft + bplot / 2, axis_y + 34, "odds ratio (log scale) — OR>1: enriched", size=12, fill=INK2, anchor="middle"))

    for i, route in enumerate(routes):
        y = top + i * block + row_h
        eff = effect_by_route.get(route, {})
        if eff.get("status") == "included" and eff.get("log_odds_ratio"):
            log_or = float(eff["log_odds_ratio"])
            se = float(eff["standard_error"])
            point = math.exp(log_or)
            lo = math.exp(log_or - 1.96 * se)
            hi = math.exp(log_or + 1.96 * se)
            body.append(_line(or_x(lo), y, or_x(hi), y, INK2, 1.5))
            cx = or_x(point)
            body.append(f'<circle cx="{cx:.1f}" cy="{y:.1f}" r="5" fill="{COMPATIBLE}" stroke="{SURFACE}" stroke-width="1.5"/>')
            body.append(_text(bleft + bplot + 14, y + 4, f"{point:.2f} [{lo:.2f}, {hi:.2f}]", size=11, fill=INK2))
        else:
            body.append(_text(or_x(1.0), y + 4, "double-zero — uninformative", size=11, fill=MUTED, anchor="middle"))

    # pooled diamond
    if summary.get("pooled_odds_ratio"):
        py = axis_y - 6
        pooled = float(summary["pooled_odds_ratio"])
        lo = float(summary["ci_low_odds_ratio"])
        hi = float(summary["ci_high_odds_ratio"])
        cx, xl, xr = or_x(pooled), or_x(lo), or_x(hi)
        body.append(f'<polygon points="{xl:.1f},{py:.1f} {cx:.1f},{py - 7:.1f} {xr:.1f},{py:.1f} {cx:.1f},{py + 7:.1f}" fill="{INK}"/>')
        body.append(_text(bleft + bplot + 14, py + 4, f"pooled {pooled:.2f} [{lo:.2f}, {hi:.2f}]", size=11, fill=INK, weight="bold"))
        body.append(_text(bleft, py + 4, "pooled", size=11, fill=INK, anchor="end", weight="bold"))

    return _svg(width, ly + 24, "".join(body))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("route_records_csv")
    parser.add_argument("audit_yield_csv")
    parser.add_argument("out_dir")
    args = parser.parse_args(argv)

    records = read_csv_rows(args.route_records_csv)
    audit_rows = read_rows(args.audit_yield_csv, AUDIT_FIELDS)

    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    (out / "fig1_direction_map.svg").write_text(figure_direction_map(records), encoding="utf-8")
    (out / "fig2_yield_meta_analysis.svg").write_text(figure_yield(audit_rows), encoding="utf-8")
    print(f"wrote {out/'fig1_direction_map.svg'}")
    print(f"wrote {out/'fig2_yield_meta_analysis.svg'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
