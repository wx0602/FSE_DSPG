#!/usr/bin/env python3
"""生成9个工具的上下游四状态水平堆叠柱状图。"""

from __future__ import annotations

import csv
from collections import defaultdict

from generate_exclusivity_plots import (
    BOTH_COLOR,
    DOWNSTREAM_COLOR,
    HERE,
    MUTED_COLOR,
    NEITHER_COLOR,
    TEXT_COLOR,
    UPSTREAM_COLOR,
    build_records,
    configure_style,
)
from matplotlib import pyplot as plt
from matplotlib.patches import Patch
from matplotlib.ticker import MultipleLocator


CATEGORIES = [
    ("SE", "#4C78A8", ["SWE-agent", "OpenHands"]),
    ("AVR", "#F58518", ["San2Patch", "PatchAgent", "Appatch"]),
    ("APR", "#54A24B", ["Agentless", "RepairAgent", "PreMM", "ReInFix"]),
]

STATE_SPECS = [
    ("upstream_only", "仅上游修复", UPSTREAM_COLOR),
    ("both", "上下游均修复", BOTH_COLOR),
    ("downstream_only", "仅下游修复", DOWNSTREAM_COLOR),
    ("neither", "均未修复", NEITHER_COLOR),
]


def summarize(cell_records):
    by_tool = defaultdict(list)
    for row in cell_records:
        by_tool[row["tool"]].append(row)

    category_by_tool = {
        tool: category for category, _, tools in CATEGORIES for tool in tools
    }
    order = [tool for _, _, tools in CATEGORIES for tool in tools]
    summaries = []
    for tool in order:
        rows = by_tool[tool]
        upstream_only = sum(
            bool(row["upstream_fixed"])
            and not bool(row["downstream_all_projects_fixed"])
            for row in rows
        )
        both = sum(
            bool(row["upstream_fixed"])
            and bool(row["downstream_all_projects_fixed"])
            for row in rows
        )
        downstream_only = sum(
            not bool(row["upstream_fixed"])
            and bool(row["downstream_all_projects_fixed"])
            for row in rows
        )
        neither = len(rows) - upstream_only - both - downstream_only
        summaries.append(
            {
                "category": category_by_tool[tool],
                "tool": tool,
                "total_cves": len(rows),
                "upstream_only": upstream_only,
                "both": both,
                "downstream_only": downstream_only,
                "neither": neither,
                "upstream_total": upstream_only + both,
                "downstream_total": downstream_only + both,
            }
        )
    return summaries


def write_summary(summaries):
    with (HERE / "tool_four_state_stacked_summary.csv").open(
        "w", encoding="utf-8-sig", newline=""
    ) as handle:
        writer = csv.DictWriter(handle, fieldnames=list(summaries[0]))
        writer.writeheader()
        writer.writerows(summaries)


def make_figure(summaries):
    # 类别间留空，使9个工具仍能直接对应SE/AVR/APR。
    y_positions = []
    current = 0.0
    category_centers = {}
    category_boundaries = []
    row_by_tool = {row["tool"]: row for row in summaries}
    ordered_rows = []
    for category_index, (category, _, tools) in enumerate(CATEGORIES):
        start = current
        for tool in tools:
            y_positions.append(current)
            ordered_rows.append(row_by_tool[tool])
            current += 1.0
        category_centers[category] = (start + current - 1.0) / 2
        if category_index < len(CATEGORIES) - 1:
            category_boundaries.append(current - 0.5 + 0.35)
            current += 0.7

    figure, axis = plt.subplots(figsize=(20 / 2.54, 10 / 2.54), dpi=300)
    figure.patch.set_facecolor("white")
    left_values = [0] * len(ordered_rows)
    for field, label, color in STATE_SPECS:
        values = [row[field] for row in ordered_rows]
        bars = axis.barh(
            y_positions,
            values,
            left=left_values,
            height=0.68,
            color=color,
            edgecolor="white",
            linewidth=0.8,
            label=label,
            zorder=3,
        )
        for bar, value in zip(bars, values):
            if value > 0:
                label_color = TEXT_COLOR if field == "neither" else "white"
                axis.text(
                    bar.get_x() + bar.get_width() / 2,
                    bar.get_y() + bar.get_height() / 2,
                    str(value),
                    ha="center",
                    va="center",
                    fontsize=7.3 if value >= 2 else 6.4,
                    fontweight="bold",
                    color=label_color,
                    zorder=4,
                )
        left_values = [left + value for left, value in zip(left_values, values)]

    axis.set_yticks(y_positions)
    axis.set_yticklabels([row["tool"] for row in ordered_rows], fontsize=8.5)
    axis.invert_yaxis()
    axis.set_xlim(0, 40)
    axis.xaxis.set_major_locator(MultipleLocator(5))
    axis.grid(axis="x", color="#DCE3EC", linewidth=0.7, zorder=0)
    axis.set_xlabel("CVE 数量（共40个共同漏洞）", fontsize=9.5, fontweight="bold", labelpad=8)
    axis.tick_params(axis="x", labelsize=8, length=0)
    axis.tick_params(axis="y", length=0, pad=7)
    for spine in axis.spines.values():
        spine.set_visible(False)
    for boundary in category_boundaries:
        axis.axhline(boundary, color="#B9C3D0", linewidth=0.9)

    category_colors = {category: color for category, color, _ in CATEGORIES}
    for category, center in category_centers.items():
        axis.text(
            -6.5,
            center,
            category,
            ha="center",
            va="center",
            fontsize=8.5,
            fontweight="bold",
            color=category_colors[category],
            clip_on=False,
        )

    axis.set_title(
        "9个工具的上下游修复状态分布",
        loc="left",
        fontsize=15,
        fontweight="bold",
        pad=42,
    )
    axis.text(
        0,
        1.055,
        "每条柱表示40个共同漏洞；柱内数字为对应状态的CVE数量",
        transform=axis.transAxes,
        fontsize=7.8,
        color=MUTED_COLOR,
    )
    axis.legend(
        handles=[Patch(facecolor=color, label=label) for _, label, color in STATE_SPECS],
        frameon=False,
        ncol=4,
        loc="upper left",
        bbox_to_anchor=(0, 1.16),
        fontsize=7.6,
    )
    figure.text(
        0.17,
        0.018,
        "严格下游口径：该工具必须修复同一 CVE 的全部下游项目，才记为下游成功。",
        fontsize=7.2,
        color=MUTED_COLOR,
    )
    figure.subplots_adjust(left=0.18, right=0.98, top=0.78, bottom=0.15)
    figure.savefig(HERE / "tool_four_state_stacked_bar.png", dpi=300, facecolor="white")
    figure.savefig(HERE / "tool_four_state_stacked_bar.svg", facecolor="white")
    plt.close(figure)


def main():
    configure_style()
    _, cell_records = build_records()
    summaries = summarize(cell_records)
    write_summary(summaries)
    make_figure(summaries)
    for row in summaries:
        print(
            f"{row['category']} {row['tool']}: 仅上游={row['upstream_only']}, "
            f"均修复={row['both']}, 仅下游={row['downstream_only']}, "
            f"均未修复={row['neither']}"
        )


if __name__ == "__main__":
    main()
