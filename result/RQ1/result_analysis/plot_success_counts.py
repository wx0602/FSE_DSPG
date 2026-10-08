#!/usr/bin/env python3
"""Read each experiment result matrix and draw a grouped bar chart (SVG) of repair-success counts for the 9 tools."""

from __future__ import annotations

import argparse
import csv
import html
import math
from pathlib import Path


EXPERIMENTS = (
    ("cve_description_validation_matrix.csv", "CVE description only", "#4C78A8"),
    ("with_vuln_chain_validation_matrix.csv", "+ vulnerability chain", "#F58518"),
    ("with_upstream_patch_matrix.csv", "+ upstream patch", "#54A24B"),
    (
        "with_selfgen_upstream_patch_matrix.csv",
        "+ self-generated upstream patch",
        "#B279A2",
    ),
    (
        "with_selfgen_upstream_patch_and_vuln_chain_matrix.csv",
        "self-generated patch + vulnerability chain",
        "#72B7B2",
    ),
    ("with_poc_validation_matrix.csv", "+ downstream PoC", "#E45756"),
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Draw a grouped bar chart of success counts for the 9 tools in each experiment group"
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parent,
        help="Directory containing the matrix CSVs (default: the script's directory)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Output SVG path (default: root/success_counts_per_tool.svg)",
    )
    return parser.parse_args()


def read_success_counts(path: Path) -> tuple[list[str], dict[str, int]]:
    with path.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        if not reader.fieldnames or reader.fieldnames[0] != "target_id":
            raise ValueError(f"the first CSV column must be target_id: {path}")
        tools = reader.fieldnames[1:]
        counts = {tool: 0 for tool in tools}
        for row in reader:
            for tool in tools:
                counts[tool] += row[tool] == "success"
    return tools, counts


def svg_text(
    x: float,
    y: float,
    text: object,
    *,
    size: int = 24,
    anchor: str = "middle",
    weight: str = "normal",
    fill: str = "#333333",
    transform: str | None = None,
) -> str:
    transform_attr = f' transform="{transform}"' if transform else ""
    return (
        f'<text x="{x:.1f}" y="{y:.1f}" text-anchor="{anchor}" '
        f'font-size="{size}" font-weight="{weight}" fill="{fill}"'
        f'{transform_attr}>{html.escape(str(text))}</text>'
    )


def draw_chart(
    output: Path,
    tools: list[str],
    series: list[tuple[str, str, dict[str, int]]],
) -> None:
    width, height = 1800, 1000
    left, right, top, bottom = 125, 55, 210, 155
    plot_width = width - left - right
    plot_height = height - top - bottom

    maximum = max(counts[tool] for _, _, counts in series for tool in tools)
    y_max = max(10, int(math.ceil(maximum / 10.0) * 10))
    group_width = plot_width / len(tools)
    series_count = len(series)
    bar_gap = 5
    bar_width = min(32, (group_width - 32) / series_count - bar_gap)
    bars_width = series_count * bar_width + (series_count - 1) * bar_gap

    def y_position(value: int) -> float:
        return top + plot_height - value / y_max * plot_height

    parts = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        (
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" '
            f'height="{height}" viewBox="0 0 {width} {height}">'
        ),
        "<style>",
        'text { font-family: "Noto Sans CJK SC", "Microsoft YaHei", sans-serif; }',
        "</style>",
        f'<rect width="{width}" height="{height}" fill="#FFFFFF"/>',
        svg_text(
            width / 2,
            58,
            f"Repair-success counts for the 9 tools across {len(series)} experiment groups",
            size=36,
            weight="bold",
            fill="#222222",
        ),
        svg_text(
            width / 2,
            98,
            "success: the patch compiles and the vulnerability occurrence count drops versus the baseline",
            size=20,
            fill="#666666",
        ),
    ]

    legend_item_width = 270
    legend_start = (width - legend_item_width * series_count) / 2
    for index, (label, color, _) in enumerate(series):
        x = legend_start + index * legend_item_width
        parts.append(
            f'<rect x="{x:.1f}" y="130" width="28" height="20" rx="3" fill="{color}"/>'
        )
        parts.append(
            svg_text(x + 40, 148, label, size=20, anchor="start", fill="#333333")
        )

    tick_step = 10
    for tick in range(0, y_max + 1, tick_step):
        y = y_position(tick)
        parts.append(
            f'<line x1="{left}" y1="{y:.1f}" x2="{width-right}" y2="{y:.1f}" '
            'stroke="#D9D9D9" stroke-width="1"/>'
        )
        parts.append(svg_text(left - 18, y + 8, tick, size=20, anchor="end"))

    axis_bottom = top + plot_height
    parts.extend(
        [
            f'<line x1="{left}" y1="{top}" x2="{left}" y2="{axis_bottom}" '
            'stroke="#444444" stroke-width="2"/>',
            f'<line x1="{left}" y1="{axis_bottom}" x2="{width-right}" '
            f'y2="{axis_bottom}" stroke="#444444" stroke-width="2"/>',
            svg_text(
                35,
                top + plot_height / 2,
                "Repair-success count",
                size=25,
                weight="bold",
                transform=f"rotate(-90 35 {top + plot_height / 2:.1f})",
            ),
            svg_text(
                left + plot_width / 2,
                height - 28,
                "tool",
                size=25,
                weight="bold",
            ),
        ]
    )

    for tool_index, tool in enumerate(tools):
        group_left = left + tool_index * group_width
        bars_left = group_left + (group_width - bars_width) / 2
        center = group_left + group_width / 2
        parts.append(svg_text(center, axis_bottom + 42, tool, size=19))

        for series_index, (_, color, counts) in enumerate(series):
            value = counts[tool]
            x = bars_left + series_index * (bar_width + bar_gap)
            y = y_position(value)
            bar_height = axis_bottom - y
            parts.append(
                f'<rect x="{x:.1f}" y="{y:.1f}" width="{bar_width:.1f}" '
                f'height="{bar_height:.1f}" rx="3" fill="{color}"/>'
            )
            parts.append(
                svg_text(
                    x + bar_width / 2,
                    y - 8,
                    value,
                    size=17,
                    weight="bold",
                    fill=color,
                )
            )

    parts.append("</svg>")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(parts) + "\n", encoding="utf-8")


def main() -> None:
    args = parse_args()
    root = args.root.resolve()
    output = (args.output or root / "success_counts_per_tool.svg").resolve()

    tools: list[str] | None = None
    series: list[tuple[str, str, dict[str, int]]] = []
    for filename, label, color in EXPERIMENTS:
        current_tools, counts = read_success_counts(root / filename)
        if tools is None:
            tools = current_tools
        elif current_tools != tools:
            raise ValueError(f"tool columns or their order differ: {filename}")
        series.append((label, color, counts))

    if not tools:
        raise ValueError("the matrix has no tool columns")
    draw_chart(output, tools, series)
    print(f"Generated {output}")
    for label, _, counts in series:
        print(label + ": " + ", ".join(f"{tool}={counts[tool]}" for tool in tools))


if __name__ == "__main__":
    main()
