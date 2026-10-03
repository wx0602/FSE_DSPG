#!/usr/bin/env python3
"""按 SE/AVR/APR 类别生成上下游严格修复集合韦恩图。

类别修复采用“全工具成功”口径：
1. 上游：类别内每一个工具都必须在该 CVE 上为 Fixed；
2. 下游：类别内每一个工具都必须修复该 CVE 的全部下游项目。
"""

from __future__ import annotations

import csv
from collections import defaultdict

from generate_exclusivity_plots import (
    DOWNSTREAM_COLOR,
    HERE,
    MUTED_COLOR,
    TEXT_COLOR,
    UPSTREAM_COLOR,
    build_records,
    configure_style,
)
from matplotlib import pyplot as plt
from matplotlib.patches import Circle, Patch


CATEGORIES = [
    (
        "SE",
        "通用软件工程工具",
        ["SWE-agent", "OpenHands"],
    ),
    (
        "AVR",
        "自动漏洞修复工具",
        ["San2Patch", "PatchAgent", "Appatch"],
    ),
    (
        "APR",
        "自动程序修复工具",
        ["Agentless", "RepairAgent", "PreMM", "ReInFix"],
    ),
]


def summarize(cell_records):
    by_cve_tool = defaultdict(dict)
    for row in cell_records:
        by_cve_tool[row["cve"]][row["tool"]] = (
            bool(row["upstream_fixed"]),
            bool(row["downstream_all_projects_fixed"]),
        )

    summaries = []
    membership_rows = []
    for category, category_name, tools in CATEGORIES:
        upstream_only_cves = []
        both_cves = []
        downstream_only_cves = []
        neither_cves = []
        for cve in sorted(by_cve_tool):
            results = by_cve_tool[cve]
            upstream_all = all(results[tool][0] for tool in tools)
            downstream_all = all(results[tool][1] for tool in tools)
            if upstream_all and downstream_all:
                state = "上下游均为类别全工具成功"
                both_cves.append(cve)
            elif upstream_all:
                state = "仅上游类别全工具成功"
                upstream_only_cves.append(cve)
            elif downstream_all:
                state = "仅下游类别全工具成功"
                downstream_only_cves.append(cve)
            else:
                state = "上下游均未达到类别全工具成功"
                neither_cves.append(cve)
            membership_rows.append(
                {
                    "category": category,
                    "category_name": category_name,
                    "tools": ";".join(tools),
                    "cve": cve,
                    "upstream_all_tools_fixed": int(upstream_all),
                    "downstream_all_tools_all_projects_fixed": int(downstream_all),
                    "state": state,
                }
            )

        summaries.append(
            {
                "category": category,
                "category_name": category_name,
                "tools": ";".join(tools),
                "total_cves": len(by_cve_tool),
                "upstream_only": len(upstream_only_cves),
                "both": len(both_cves),
                "downstream_only": len(downstream_only_cves),
                "neither": len(neither_cves),
                "upstream_total": len(upstream_only_cves) + len(both_cves),
                "downstream_total": len(downstream_only_cves) + len(both_cves),
                "upstream_only_cves": ";".join(upstream_only_cves),
                "both_cves": ";".join(both_cves),
                "downstream_only_cves": ";".join(downstream_only_cves),
                "neither_cves": ";".join(neither_cves),
            }
        )
    return summaries, membership_rows


def write_data(summaries, membership_rows):
    with (HERE / "tool_category_strict_venn_summary.csv").open(
        "w", encoding="utf-8-sig", newline=""
    ) as handle:
        writer = csv.DictWriter(handle, fieldnames=list(summaries[0]))
        writer.writeheader()
        writer.writerows(summaries)

    with (HERE / "tool_category_strict_venn_membership.csv").open(
        "w", encoding="utf-8-sig", newline=""
    ) as handle:
        writer = csv.DictWriter(handle, fieldnames=list(membership_rows[0]))
        writer.writeheader()
        writer.writerows(membership_rows)


def draw_venn_panel(axis, row):
    axis.set_xlim(0, 1)
    axis.set_ylim(0, 1)
    axis.set_aspect("equal")
    axis.axis("off")

    axis.add_patch(
        Circle(
            (0.40, 0.54),
            0.30,
            facecolor=UPSTREAM_COLOR,
            edgecolor=UPSTREAM_COLOR,
            alpha=0.34,
            linewidth=1.8,
        )
    )
    axis.add_patch(
        Circle(
            (0.60, 0.54),
            0.30,
            facecolor=DOWNSTREAM_COLOR,
            edgecolor=DOWNSTREAM_COLOR,
            alpha=0.34,
            linewidth=1.8,
        )
    )
    axis.text(
        0.5,
        0.98,
        f"{row['category']} · {row['category_name']}",
        ha="center",
        va="top",
        fontsize=12,
        fontweight="bold",
        color=TEXT_COLOR,
    )
    axis.text(
        0.5,
        0.90,
        row["tools"].replace(";", " · "),
        ha="center",
        va="top",
        fontsize=7.4,
        color=MUTED_COLOR,
    )
    axis.text(
        0.23,
        0.55,
        f"仅上游\n{row['upstream_only']}",
        ha="center",
        va="center",
        fontsize=10,
        fontweight="bold",
    )
    axis.text(
        0.50,
        0.55,
        f"交集\n{row['both']}",
        ha="center",
        va="center",
        fontsize=10,
        fontweight="bold",
    )
    axis.text(
        0.77,
        0.55,
        f"仅下游\n{row['downstream_only']}",
        ha="center",
        va="center",
        fontsize=10,
        fontweight="bold",
    )
    axis.text(
        0.50,
        0.15,
        f"均未达到全工具成功：{row['neither']}\n上游集合={row['upstream_total']}，下游集合={row['downstream_total']}",
        ha="center",
        va="center",
        fontsize=7.6,
        color=MUTED_COLOR,
    )


def make_figure(summaries):
    figure, axes = plt.subplots(1, 3, figsize=(20 / 2.54, 8 / 2.54), dpi=300)
    figure.patch.set_facecolor("white")
    for axis, row in zip(axes.flat, summaries):
        draw_venn_panel(axis, row)

    figure.text(
        0.04,
        0.975,
        "SE、AVR、APR 类别的上下游修复集合",
        ha="left",
        va="top",
        fontsize=15,
        fontweight="bold",
        color=TEXT_COLOR,
    )
    figure.text(
        0.04,
        0.908,
        "类别内全部工具都成功才计入集合；全集为40个共同漏洞（圆面积不按数量比例）",
        ha="left",
        va="top",
        fontsize=7.5,
        color=MUTED_COLOR,
    )
    figure.legend(
        handles=[
            Patch(facecolor=UPSTREAM_COLOR, alpha=0.45, label="上游：类别全工具成功"),
            Patch(facecolor=DOWNSTREAM_COLOR, alpha=0.45, label="下游：类别全工具且全部项目成功"),
        ],
        loc="upper right",
        bbox_to_anchor=(0.96, 0.968),
        ncol=2,
        frameon=False,
        fontsize=7.4,
    )
    figure.text(
        0.04,
        0.018,
        "下游严格口径：类别内每个工具都必须修复该 CVE 的每一个下游项目。",
        ha="left",
        va="bottom",
        fontsize=7.2,
        color=MUTED_COLOR,
    )
    figure.subplots_adjust(left=0.025, right=0.98, top=0.83, bottom=0.10, wspace=0.02)
    figure.savefig(
        HERE / "tool_category_strict_upstream_downstream_venn.png",
        dpi=300,
        facecolor="white",
    )
    figure.savefig(
        HERE / "tool_category_strict_upstream_downstream_venn.svg",
        facecolor="white",
    )
    plt.close(figure)


def main():
    configure_style()
    _, cell_records = build_records()
    summaries, membership_rows = summarize(cell_records)
    write_data(summaries, membership_rows)
    make_figure(summaries)
    for row in summaries:
        print(
            f"{row['category']}: 仅上游={row['upstream_only']}, "
            f"交集={row['both']}, 仅下游={row['downstream_only']}, "
            f"均未达到={row['neither']}"
        )


if __name__ == "__main__":
    main()
