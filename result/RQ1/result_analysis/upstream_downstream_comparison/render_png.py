#!/usr/bin/env python3
"""Render the comparison-analysis PNGs with system Matplotlib; called by generate_comparison.py."""

from __future__ import annotations

import csv
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import PercentFormatter


HERE = Path(__file__).resolve().parent
UP_COLOR = "#2F6BFF"
DOWN_COLOR = "#F26B5B"
TEXT_COLOR = "#172033"
MUTED_COLOR = "#657187"
GRID_COLOR = "#DCE3EC"


def read_summary():
    with (HERE / "repair_rate_summary.csv").open(
        "r", encoding="utf-8-sig", newline=""
    ) as handle:
        rows = list(csv.DictReader(handle))
    numeric = [
        "upstream_rate",
        "upstream_ci_low",
        "upstream_ci_high",
        "downstream_macro_rate",
        "downstream_ci_low",
        "downstream_ci_high",
        "difference_upstream_minus_downstream",
    ]
    for row in rows:
        for key in numeric:
            row[key] = float(row[key])
    return rows


def configure():
    plt.rcParams.update(
        {
            "font.family": "sans-serif",
            "font.sans-serif": ["Noto Sans CJK SC", "Noto Sans CJK JP", "DejaVu Sans"],
            "axes.unicode_minus": False,
            "text.color": TEXT_COLOR,
            "axes.labelcolor": TEXT_COLOR,
            "xtick.color": MUTED_COLOR,
            "ytick.color": MUTED_COLOR,
        }
    )


def bar_chart(rows):
    figure, axis = plt.subplots(figsize=(10, 6.125), dpi=160)
    figure.patch.set_facecolor("white")
    names = [row["tool"] for row in rows]
    positions = list(range(len(rows)))
    width = 0.36
    upstream = [row["upstream_rate"] for row in rows]
    downstream = [row["downstream_macro_rate"] for row in rows]
    up_errors = [
        [value - row["upstream_ci_low"] for value, row in zip(upstream, rows)],
        [row["upstream_ci_high"] - value for value, row in zip(upstream, rows)],
    ]
    down_errors = [
        [value - row["downstream_ci_low"] for value, row in zip(downstream, rows)],
        [row["downstream_ci_high"] - value for value, row in zip(downstream, rows)],
    ]
    up_bars = axis.bar(
        [x - width / 2 for x in positions],
        upstream,
        width,
        yerr=up_errors,
        color=UP_COLOR,
        label="Upstream",
        capsize=3,
        error_kw={"elinewidth": 1, "capthick": 1},
        zorder=3,
    )
    down_bars = axis.bar(
        [x + width / 2 for x in positions],
        downstream,
        width,
        yerr=down_errors,
        color=DOWN_COLOR,
        label="Downstream",
        capsize=3,
        error_kw={"elinewidth": 1, "capthick": 1},
        zorder=3,
    )
    maximum = max(max(row["upstream_ci_high"], row["downstream_ci_high"]) for row in rows)
    axis.set_ylim(0, min(1.0, max(0.5, (int((maximum + 0.1499) * 10) / 10))))
    axis.yaxis.set_major_formatter(PercentFormatter(1.0, decimals=0))
    axis.set_ylabel("repair_rate", fontsize=11, fontweight="bold")
    axis.set_xticks(positions)
    axis.set_xticklabels(names, rotation=38, ha="right", fontsize=9)
    axis.grid(axis="y", color=GRID_COLOR, linewidth=0.7, zorder=0)
    axis.spines["top"].set_visible(False)
    axis.spines["right"].set_visible(False)
    axis.spines["left"].set_color(GRID_COLOR)
    axis.spines["bottom"].set_color(GRID_COLOR)
    axis.set_title(
        "upstream_vs_downstream_repair_rate_comparison", fontsize=18, fontweight="bold", pad=30
    )
    axis.text(
        0,
        1.035,
        "Common vulnerabilities, equally weighted per CVE; error bars are bootstrap 95% CI with CVE as the resampling unit",
        transform=axis.transAxes,
        color=MUTED_COLOR,
        fontsize=9,
    )
    axis.legend(frameon=False, ncol=2, loc="upper right", bbox_to_anchor=(1, 1.13))
    for bars, values in ((up_bars, upstream), (down_bars, downstream)):
        for bar, value in zip(bars, values):
            axis.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height() + 0.012,
                f"{value:.1%}",
                ha="center",
                va="bottom",
                fontsize=7,
                fontweight="bold",
            )
    axis.text(
        0,
        -0.29,
        "repair_rate = fixed/success; compile errors, unrepaired, and no-patch "
        "cases all count in the denominator.",
        color=MUTED_COLOR,
        fontsize=8,
    )
    figure.subplots_adjust(left=0.09, right=0.98, top=0.80, bottom=0.28)
    figure.savefig(HERE / "repair_rate_comparison.png", facecolor="white")
    plt.close(figure)


def dumbbell_chart(rows):
    tool_rows = sorted(
        [row for row in rows if row["tool"] != "overall"],
        key=lambda row: row["difference_upstream_minus_downstream"],
    )
    ordered = tool_rows + [next(row for row in rows if row["tool"] == "overall")]
    figure, axis = plt.subplots(figsize=(10, 6.125), dpi=160)
    figure.patch.set_facecolor("white")
    y_positions = list(range(len(ordered)))
    maximum = max(
        max(row["upstream_rate"], row["downstream_macro_rate"]) for row in ordered
    )
    axis_max = min(1.0, max(0.5, (int((maximum + 0.1499) * 10) / 10)))
    axis.axhspan(len(ordered) - 1.43, len(ordered) - 0.57, color="#F3F6FA", zorder=0)
    for y, row in zip(y_positions, ordered):
        upstream = row["upstream_rate"]
        downstream = row["downstream_macro_rate"]
        axis.plot(
            [upstream, downstream],
            [y, y],
            color="#AAB4C3",
            linewidth=3.2,
            solid_capstyle="round",
            zorder=2,
        )
        axis.scatter(downstream, y, s=85, color=DOWN_COLOR, zorder=3)
        axis.scatter(upstream, y, s=85, color=UP_COLOR, zorder=3)
        difference = row["difference_upstream_minus_downstream"]
        color = UP_COLOR if difference > 0 else DOWN_COLOR if difference < 0 else MUTED_COLOR
        axis.text(
            axis_max + 0.018,
            y,
            f"Δ {difference * 100:+.1f} pp",
            va="center",
            color=color,
            fontsize=9,
            fontweight="bold" if row["tool"] == "overall" else "normal",
            clip_on=False,
        )
    axis.set_xlim(0, axis_max)
    axis.set_ylim(-0.7, len(ordered) - 0.3)
    axis.set_yticks(y_positions)
    axis.set_yticklabels([row["tool"] for row in ordered], fontsize=10)
    axis.invert_yaxis()
    axis.xaxis.set_major_formatter(PercentFormatter(1.0, decimals=0))
    axis.xaxis.tick_top()
    axis.set_xlabel("")
    axis.text(
        0.5,
        -0.10,
        "repair_rate",
        transform=axis.transAxes,
        ha="center",
        va="top",
        fontsize=11,
        fontweight="bold",
    )
    axis.grid(axis="x", color=GRID_COLOR, linewidth=0.7, zorder=0)
    for spine in axis.spines.values():
        spine.set_visible(False)
    axis.set_title(
        "upstream_vs_downstream_repair_rate_diff_dumbbell", fontsize=15, fontweight="bold", pad=35
    )
    axis.text(
        0,
        1.055,
        "The further right a point sits, the higher the repair rate; Δ = upstream − downstream",
        transform=axis.transAxes,
        color=MUTED_COLOR,
        fontsize=9,
    )
    axis.scatter([], [], s=70, color=UP_COLOR, label="Upstream")
    axis.scatter([], [], s=70, color=DOWN_COLOR, label="Downstream")
    axis.legend(frameon=False, ncol=2, loc="upper right", bbox_to_anchor=(1, 1.16))
    figure.subplots_adjust(left=0.17, right=0.85, top=0.80, bottom=0.12)
    figure.savefig(HERE / "dumbbell_plot.png", facecolor="white")
    plt.close(figure)


def main():
    configure()
    rows = read_summary()
    bar_chart(rows)
    dumbbell_chart(rows)
    print("PNG figures generated")


if __name__ == "__main__":
    main()
