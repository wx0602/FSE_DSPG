#!/usr/bin/env python3
"""比较上游与下游漏洞修复率，并生成 CSV、SVG 和 PNG 图。

主比较只使用两份数据中共同出现的漏洞。上游每个漏洞只有一个修复任务；
下游同一漏洞可能有多个项目，因此图中的下游修复率先在每个漏洞内计算，
再对漏洞等权平均（macro average），避免多项目漏洞获得更高权重。

本脚本只依赖 Python 标准库。若系统中有 Google Chrome，会自动把 SVG
转换成同名 PNG；没有 Chrome 时仍会完整生成 SVG。
"""

from __future__ import annotations

import csv
import html
import math
import random
import re
import shutil
import subprocess
from collections import defaultdict
from pathlib import Path
from typing import Iterable, Sequence


HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
DOWNSTREAM_CSV = ROOT / "cve_description_validation_matrix.csv"
UPSTREAM_CSV = ROOT / "upstream_vuln_repair_results" / "upstream_vuln_repair_results.csv"

# 展示名、下游列名、上游列名
TOOLS = [
    ("Agentless", "agentless", "Agentless"),
    ("Appatch", "appatch", "Appatch"),
    ("OpenHands", "openhands", "OpenHands"),
    ("PatchAgent", "patchagent", "PatchAgent"),
    ("PreMM", "premm", "PreMM"),
    ("ReInFix", "reinfix", "ReInFix"),
    ("RepairAgent", "repairagent", "RepairAgent"),
    ("San2Patch", "san2patch", "San2Agent"),
    ("SWE-agent", "sweagent", "SWE-agent"),
]

UPSTREAM_FIXED = "Fixed"
DOWNSTREAM_FIXED = "success"
BOOTSTRAP_SAMPLES = 10_000
RANDOM_SEED = 20260818

UP_COLOR = "#2F6BFF"
DOWN_COLOR = "#F26B5B"
GRID_COLOR = "#DCE3EC"
TEXT_COLOR = "#172033"
MUTED_COLOR = "#657187"
BG_COLOR = "#FFFFFF"
FONT = "Noto Sans CJK SC, Noto Sans CJK JP, Microsoft YaHei, sans-serif"

ID_PATTERN = re.compile(
    r"(CVE-\d{4}-\d+|CODEC-\d+|IO-\d+|LANG-\d+|TEXT-\d+|Zip(?:4j)?-\d+)",
    re.IGNORECASE,
)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def vulnerability_id(raw: str) -> str:
    """从 target_id/CVE 列提取统一的漏洞编号。"""
    match = ID_PATTERN.match(raw.strip())
    if not match:
        raise ValueError(f"无法从 {raw!r} 提取漏洞编号")
    result = match.group(1).upper()
    # 两张源表对此项目使用了不同简称。
    if result == "ZIP-263":
        return "ZIP4J-263"
    return result


def percentile(sorted_values: Sequence[float], probability: float) -> float:
    if not sorted_values:
        return math.nan
    position = (len(sorted_values) - 1) * probability
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return sorted_values[lower]
    weight = position - lower
    return sorted_values[lower] * (1 - weight) + sorted_values[upper] * weight


def bootstrap_mean_ci(
    values: Sequence[float], rng: random.Random, samples: int = BOOTSTRAP_SAMPLES
) -> tuple[float, float]:
    """以漏洞为抽样单位得到均值的 percentile bootstrap 95% CI。"""
    n = len(values)
    simulated = []
    for _ in range(samples):
        simulated.append(sum(values[rng.randrange(n)] for _ in range(n)) / n)
    simulated.sort()
    return percentile(simulated, 0.025), percentile(simulated, 0.975)


def pct(value: float, digits: int = 1) -> str:
    return f"{value * 100:.{digits}f}%"


def xml_text(value: object) -> str:
    return html.escape(str(value), quote=True)


def svg_text(
    x: float,
    y: float,
    value: object,
    *,
    size: int = 24,
    fill: str = TEXT_COLOR,
    anchor: str = "start",
    weight: int = 400,
    rotate: float | None = None,
) -> str:
    transform = f' transform="rotate({rotate} {x} {y})"' if rotate is not None else ""
    return (
        f'<text x="{x:.1f}" y="{y:.1f}" text-anchor="{anchor}" '
        f'font-family="{FONT}" font-size="{size}" font-weight="{weight}" '
        f'fill="{fill}"{transform}>{xml_text(value)}</text>'
    )


def svg_base(width: int, height: int, body: Iterable[str], title: str) -> str:
    return "\n".join(
        [
            '<?xml version="1.0" encoding="UTF-8"?>',
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
            f'viewBox="0 0 {width} {height}" role="img" aria-label="{xml_text(title)}">',
            f'<rect width="{width}" height="{height}" fill="{BG_COLOR}"/>',
            *body,
            "</svg>",
        ]
    )


def nice_axis_max(values: Iterable[float]) -> float:
    maximum = max(values)
    return min(1.0, max(0.5, math.ceil((maximum + 0.05) * 10) / 10))


def make_bar_chart(rows: Sequence[dict[str, object]], output: Path) -> None:
    width, height = 1600, 980
    left, right, top, bottom = 135, 55, 190, 185
    plot_w, plot_h = width - left - right, height - top - bottom
    axis_max = nice_axis_max(
        float(row[key])
        for row in rows
        for key in ("upstream_ci_high", "downstream_ci_high")
    )

    def y(value: float) -> float:
        return top + plot_h * (1 - value / axis_max)

    parts = [
        svg_text(left, 62, 'upstream_vs_downstream_repair_rate_comparison'ate_comparison'0),
        svg_text(
            left,
            108,
            "共同漏洞、按 CVE 等权；误差线为以 CVE 为单位的 bootstrap 95% CI",
            size=23,
            fill=MUTED_COLOR,
        ),
        f'<circle cx="{width - 430}" cy="67" r="9" fill="{UP_COLOR}"/>',
        svg_text(width - 410, 75, "上游", size=22),
        f'<circle cx="{width - 270}" cy="67" r="9" fill="{DOWN_COLOR}"/>',
        svg_text(width - 250, 75, "下游", size=22),
    ]

    tick_step = 0.1
    ticks = int(round(axis_max / tick_step))
    for tick in range(ticks + 1):
        value = tick * tick_step
        yy = y(value)
        parts.append(
            f'<line x1="{left}" y1="{yy:.1f}" x2="{width-right}" y2="{yy:.1f}" '
            f'stroke="{GRID_COLOR}" stroke-width="1"/>'
        )
        parts.append(svg_text(left - 18, yy + 8, pct(value, 0), size=20, fill=MUTED_COLOR, anchor="end"))

    group_w = plot_w / len(rows)
    bar_w = min(43, group_w * 0.30)
    for index, row in enumerate(rows):
        center = left + group_w * (index + 0.5)
        is_overall = str(row["tool"]) == 'overall''     if is_overall:
            parts.append(
                f'<rect x="{center - group_w/2 + 4:.1f}" y="{top}" width="{group_w - 8:.1f}" '
                f'height="{plot_h}" rx="10" fill="#F3F6FA"/>'
            )
        for offset, prefix, color in [
            (-bar_w * 0.58, "upstream", UP_COLOR),
            (bar_w * 0.58, "downstream", DOWN_COLOR),
        ]:
            value = float(row[f"{prefix}_rate"])
            low = float(row[f"{prefix}_ci_low"])
            high = float(row[f"{prefix}_ci_high"])
            xx = center + offset
            yy = y(value)
            parts.append(
                f'<rect x="{xx - bar_w/2:.1f}" y="{yy:.1f}" width="{bar_w:.1f}" '
                f'height="{top + plot_h - yy:.1f}" rx="5" fill="{color}"/>'
            )
            parts.append(
                f'<line x1="{xx:.1f}" y1="{y(high):.1f}" x2="{xx:.1f}" y2="{y(low):.1f}" '
                f'stroke="{TEXT_COLOR}" stroke-width="2"/>'
            )
            for cap in (low, high):
                parts.append(
                    f'<line x1="{xx-8:.1f}" y1="{y(cap):.1f}" x2="{xx+8:.1f}" y2="{y(cap):.1f}" '
                    f'stroke="{TEXT_COLOR}" stroke-width="2"/>'
                )
            parts.append(svg_text(xx, yy - 13, pct(value), size=17, anchor="middle", weight=600))
        parts.append(
            svg_text(
                center,
                top + plot_h + 34,
                row["tool"],
                size=19 if not is_overall else 21,
                anchor="end",
                weight=700 if is_overall else 500,
                rotate=-42,
            )
        )

    parts.extend(
        [
            f'<line x1="{left}" y1="{top + plot_h}" x2="{width-right}" y2="{top + plot_h}" '
            f'stroke="{TEXT_COLOR}" stroke-width="2"/>',
            svg_text(39, top + plot_h / 2, 'repair_rate'e'=25, anchor="middle", weight=600, rotate=-90),
            svg_text(
                left,
                height - 35,
                'repair_rate = fixed/success; compile errors, unrepaired, and no-patch cases all count in the denominator.'the denominator.'MUTED_COLOR,
            ),
        ]
    )
    output.write_text(svg_base(width, height, parts, 'upstream_vs_downstream_repair_rate_comparison'ate_comparison'


def make_dumbbell_chart(rows: Sequence[dict[str, object]], output: Path) -> None:
    # 总体固定放在最后，其余工具按“上游 - 下游”差值排序。
    tool_rows = sorted(
        (row for row in rows if row["tool"] != 'overall''       key=lambda row: float(row["difference"]),
    )
    overall = next(row for row in rows if row["tool"] == 'overall''  ordered = [*tool_rows, overall]

    width, height = 1600, 980
    left, right, top, bottom = 245, 185, 190, 95
    plot_w, plot_h = width - left - right, height - top - bottom
    axis_max = nice_axis_max(
        float(row[key]) for row in ordered for key in ("upstream_rate", "downstream_rate")
    )

    def x(value: float) -> float:
        return left + plot_w * value / axis_max

    row_h = plot_h / len(ordered)
    parts = [
        svg_text(left, 62, 'upstream_vs_downstream_repair_rate_diff_dumbbell'dumbbell'      svg_text(
            left,
            108,
            "点越靠右表示修复率越高；Δ = 上游 − 下游",
            size=23,
            fill=MUTED_COLOR,
        ),
        f'<circle cx="{width - 430}" cy="67" r="9" fill="{UP_COLOR}"/>',
        svg_text(width - 410, 75, "上游", size=22),
        f'<circle cx="{width - 270}" cy="67" r="9" fill="{DOWN_COLOR}"/>',
        svg_text(width - 250, 75, "下游", size=22),
    ]

    for tick in range(int(round(axis_max / 0.1)) + 1):
        value = tick * 0.1
        xx = x(value)
        parts.append(
            f'<line x1="{xx:.1f}" y1="{top}" x2="{xx:.1f}" y2="{top+plot_h}" '
            f'stroke="{GRID_COLOR}" stroke-width="1"/>'
        )
        parts.append(svg_text(xx, top - 18, pct(value, 0), size=20, fill=MUTED_COLOR, anchor="middle"))

    for index, row in enumerate(ordered):
        yy = top + row_h * (index + 0.5)
        upstream = float(row["upstream_rate"])
        downstream = float(row["downstream_rate"])
        difference = float(row["difference"])
        is_overall = str(row["tool"]) == 'overall''     if is_overall:
            parts.append(
                f'<rect x="35" y="{yy-row_h/2+3:.1f}" width="{width-70}" height="{row_h-6:.1f}" '
                f'rx="10" fill="#F3F6FA"/>'
            )
        parts.append(
            f'<line x1="{x(min(upstream, downstream)):.1f}" y1="{yy:.1f}" '
            f'x2="{x(max(upstream, downstream)):.1f}" y2="{yy:.1f}" '
            f'stroke="#AAB4C3" stroke-width="6" stroke-linecap="round"/>'
        )
        parts.append(f'<circle cx="{x(downstream):.1f}" cy="{yy:.1f}" r="13" fill="{DOWN_COLOR}"/>')
        parts.append(f'<circle cx="{x(upstream):.1f}" cy="{yy:.1f}" r="13" fill="{UP_COLOR}"/>')
        parts.append(
            svg_text(
                left - 25,
                yy + 8,
                row["tool"],
                size=22,
                anchor="end",
                weight=700 if is_overall else 500,
            )
        )
        delta_color = UP_COLOR if difference > 0 else DOWN_COLOR if difference < 0 else MUTED_COLOR
        sign = "+" if difference > 0 else ""
        parts.append(
            svg_text(
                width - right + 28,
                yy + 8,
                f"Δ {sign}{difference * 100:.1f} pp",
                size=20,
                fill=delta_color,
                weight=700 if is_overall else 500,
            )
        )

    parts.extend(
        [
            svg_text(left + plot_w / 2, height - 35, 'repair_rate'e'=25, anchor="middle", weight=600),
            svg_text(
                40,
                height - 35,
                "共同漏洞、按 CVE 等权",
                size=18,
                fill=MUTED_COLOR,
            ),
        ]
    )
    output.write_text(svg_base(width, height, parts, "上下游修复率差异哑铃图"), encoding="utf-8")


def svg_to_png(svg_path: Path, width: int = 1600, height: int = 980) -> bool:
    chrome = shutil.which("google-chrome") or shutil.which("chromium")
    if not chrome:
        return False
    png_path = svg_path.with_suffix(".png")
    command = [
        chrome,
        "--headless=new",
        "--disable-gpu",
        "--no-sandbox",
        "--hide-scrollbars",
        "--force-device-scale-factor=1",
        f"--window-size={width},{height}",
        f"--screenshot={png_path}",
        svg_path.as_uri(),
    ]
    result = subprocess.run(command, capture_output=True, text=True, timeout=60, check=False)
    return result.returncode == 0 and png_path.exists()


def matplotlib_png_fallback() -> bool:
    """默认 Python 无绘图库且 Chrome 受限时，使用系统 Python 的 Matplotlib。"""
    system_python = Path("/usr/bin/python3")
    renderer = HERE / "render_png.py"
    if not system_python.exists() or not renderer.exists():
        return False
    result = subprocess.run(
        [str(system_python), str(renderer)],
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )
    return (
        result.returncode == 0
        and (HERE / "repair_rate_comparison.png").exists()
        and (HERE / "dumbbell_plot.png").exists()
    )


def write_summary_csv(rows: Sequence[dict[str, object]]) -> None:
    fields = [
        "tool",
        "matched_cves",
        "downstream_projects",
        "upstream_fixed",
        "upstream_rate",
        "upstream_ci_low",
        "upstream_ci_high",
        "downstream_macro_rate",
        "downstream_ci_low",
        "downstream_ci_high",
        "difference_upstream_minus_downstream",
        "difference_ci_low",
        "difference_ci_high",
        "downstream_micro_fixed",
        "downstream_micro_total",
        "downstream_micro_rate",
    ]
    with (HERE / "repair_rate_summary.csv").open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {
                    "tool": row["tool"],
                    "matched_cves": row["matched_cves"],
                    "downstream_projects": row["downstream_projects"],
                    "upstream_fixed": row["upstream_fixed"],
                    "upstream_rate": f'{float(row["upstream_rate"]):.6f}',
                    "upstream_ci_low": f'{float(row["upstream_ci_low"]):.6f}',
                    "upstream_ci_high": f'{float(row["upstream_ci_high"]):.6f}',
                    "downstream_macro_rate": f'{float(row["downstream_rate"]):.6f}',
                    "downstream_ci_low": f'{float(row["downstream_ci_low"]):.6f}',
                    "downstream_ci_high": f'{float(row["downstream_ci_high"]):.6f}',
                    "difference_upstream_minus_downstream": f'{float(row["difference"]):.6f}',
                    "difference_ci_low": f'{float(row["difference_ci_low"]):.6f}',
                    "difference_ci_high": f'{float(row["difference_ci_high"]):.6f}',
                    "downstream_micro_fixed": row["downstream_micro_fixed"],
                    "downstream_micro_total": row["downstream_micro_total"],
                    "downstream_micro_rate": f'{float(row["downstream_micro_rate"]):.6f}',
                }
            )


def main() -> None:
    downstream_rows = read_csv(DOWNSTREAM_CSV)
    upstream_rows = [row for row in read_csv(UPSTREAM_CSV) if row["CVE"].strip() != "Summary"]

    downstream_by_cve: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in downstream_rows:
        downstream_by_cve[vulnerability_id(row["target_id"])].append(row)
    upstream_by_cve = {vulnerability_id(row["CVE"]): row for row in upstream_rows}

    common_cves = sorted(set(downstream_by_cve) & set(upstream_by_cve))
    upstream_only = sorted(set(upstream_by_cve) - set(downstream_by_cve))
    downstream_only = sorted(set(downstream_by_cve) - set(upstream_by_cve))
    if not common_cves:
        raise RuntimeError("两份数据中没有共同漏洞，无法比较")

    rng = random.Random(RANDOM_SEED)
    summary_rows: list[dict[str, object]] = []
    detail_rows: list[dict[str, object]] = []

    per_tool_values: list[tuple[str, list[float], list[float]]] = []
    for display_name, downstream_column, upstream_column in TOOLS:
        upstream_values = [
            float(upstream_by_cve[cve][upstream_column].strip() == UPSTREAM_FIXED)
            for cve in common_cves
        ]
        downstream_values = [
            sum(
                row[downstream_column].strip() == DOWNSTREAM_FIXED
                for row in downstream_by_cve[cve]
            )
            / len(downstream_by_cve[cve])
            for cve in common_cves
        ]
        per_tool_values.append((display_name, upstream_values, downstream_values))

        up_rate = sum(upstream_values) / len(upstream_values)
        down_rate = sum(downstream_values) / len(downstream_values)
        up_low, up_high = bootstrap_mean_ci(upstream_values, rng)
        down_low, down_high = bootstrap_mean_ci(downstream_values, rng)
        difference_values = [up - down for up, down in zip(upstream_values, downstream_values)]
        diff_low, diff_high = bootstrap_mean_ci(difference_values, rng)
        micro_fixed = sum(
            row[downstream_column].strip() == DOWNSTREAM_FIXED
            for cve in common_cves
            for row in downstream_by_cve[cve]
        )
        micro_total = sum(len(downstream_by_cve[cve]) for cve in common_cves)
        summary_rows.append(
            {
                "tool": display_name,
                "matched_cves": len(common_cves),
                "downstream_projects": micro_total,
                "upstream_fixed": int(sum(upstream_values)),
                "upstream_rate": up_rate,
                "upstream_ci_low": up_low,
                "upstream_ci_high": up_high,
                "downstream_rate": down_rate,
                "downstream_ci_low": down_low,
                "downstream_ci_high": down_high,
                "difference": up_rate - down_rate,
                "difference_ci_low": diff_low,
                "difference_ci_high": diff_high,
                "downstream_micro_fixed": micro_fixed,
                "downstream_micro_total": micro_total,
                "downstream_micro_rate": micro_fixed / micro_total,
            }
        )

        for cve, up, down in zip(common_cves, upstream_values, downstream_values):
            projects = downstream_by_cve[cve]
            detail_rows.append(
                {
                    "cve": cve,
                    "tool": display_name,
                    "upstream_status": upstream_by_cve[cve][upstream_column],
                    "upstream_fixed": int(up),
                    "downstream_fixed_projects": sum(
                        row[downstream_column].strip() == DOWNSTREAM_FIXED for row in projects
                    ),
                    "downstream_total_projects": len(projects),
                    "downstream_cve_rate": f"{down:.6f}",
                    "difference_upstream_minus_downstream": f"{up - down:.6f}",
                }
            )

    # “总体”先在每个 CVE 内跨工具平均，再对 CVE 等权平均；bootstrap 也以 CVE 为单位。
    overall_up_by_cve = [
        sum(values[index] for _, values, _ in per_tool_values) / len(TOOLS)
        for index in range(len(common_cves))
    ]
    overall_down_by_cve = [
        sum(values[index] for _, _, values in per_tool_values) / len(TOOLS)
        for index in range(len(common_cves))
    ]
    overall_diff_by_cve = [
        up - down for up, down in zip(overall_up_by_cve, overall_down_by_cve)
    ]
    overall_up = sum(overall_up_by_cve) / len(common_cves)
    overall_down = sum(overall_down_by_cve) / len(common_cves)
    overall_up_low, overall_up_high = bootstrap_mean_ci(overall_up_by_cve, rng)
    overall_down_low, overall_down_high = bootstrap_mean_ci(overall_down_by_cve, rng)
    overall_diff_low, overall_diff_high = bootstrap_mean_ci(overall_diff_by_cve, rng)
    total_micro_fixed = sum(int(row["downstream_micro_fixed"]) for row in summary_rows)
    total_micro = sum(int(row["downstream_micro_total"]) for row in summary_rows)
    summary_rows.append(
        {
            "tool": 'overall''          "matched_cves": len(common_cves),
            "downstream_projects": sum(len(downstream_by_cve[cve]) for cve in common_cves),
            "upstream_fixed": int(round(overall_up * len(common_cves) * len(TOOLS))),
            "upstream_rate": overall_up,
            "upstream_ci_low": overall_up_low,
            "upstream_ci_high": overall_up_high,
            "downstream_rate": overall_down,
            "downstream_ci_low": overall_down_low,
            "downstream_ci_high": overall_down_high,
            "difference": overall_up - overall_down,
            "difference_ci_low": overall_diff_low,
            "difference_ci_high": overall_diff_high,
            "downstream_micro_fixed": total_micro_fixed,
            "downstream_micro_total": total_micro,
            "downstream_micro_rate": total_micro_fixed / total_micro,
        }
    )

    write_summary_csv(summary_rows)
    with (HERE / "matched_cve_details.csv").open("w", encoding="utf-8-sig", newline="") as handle:
        fields = list(detail_rows[0])
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(detail_rows)

    bar_svg = HERE / "repair_rate_comparison.svg"
    dumbbell_svg = HERE / "dumbbell_plot.svg"
    make_bar_chart(summary_rows, bar_svg)
    make_dumbbell_chart(summary_rows, dumbbell_svg)
    bar_png = svg_to_png(bar_svg)
    dumbbell_png = svg_to_png(dumbbell_svg)
    if not (bar_png and dumbbell_png) and matplotlib_png_fallback():
        bar_png = True
        dumbbell_png = True

    tools_upstream_higher = sum(float(row["difference"]) > 0 for row in summary_rows[:-1])
    overall = summary_rows[-1]
    interpretation = (
        "现有结果不支持“上游更容易修复”这一推断。"
        if float(overall["difference"]) < 0
        else "现有结果在描述性统计上与“上游更容易修复”的推断一致。"
    )
    summary_md = f"""# 上下游漏洞修复对比

## 结果

- 共同漏洞：{len(common_cves)} 个；对应下游项目任务：{sum(len(downstream_by_cve[cve]) for cve in common_cves)} 个；工具：{len(TOOLS)} 个。
- 上游总体修复率：{pct(float(overall['upstream_rate']))}（bootstrap 95% CI {pct(float(overall['upstream_ci_low']))}–{pct(float(overall['upstream_ci_high']))}）。
- 下游总体修复率：{pct(float(overall['downstream_rate']))}（bootstrap 95% CI {pct(float(overall['downstream_ci_low']))}–{pct(float(overall['downstream_ci_high']))}）。
- 差值（上游 − 下游）：{float(overall['difference']) * 100:+.1f} 个百分点（配对 bootstrap 95% CI {float(overall['difference_ci_low']) * 100:+.1f} 至 {float(overall['difference_ci_high']) * 100:+.1f} 个百分点）。
- 9 个工具中有 {tools_upstream_higher} 个上游修复率更高，{len(TOOLS) - tools_upstream_higher} 个下游修复率更高。

{interpretation}当前点估计反而显示下游高 {abs(float(overall['difference'])) * 100:.1f} 个百分点；但差值置信区间跨越 0，因此也不能据此断言下游必然更容易修复。

## 统计口径

1. 仅比较两张表共同出现的漏洞。上游独有的 {len(upstream_only)} 个漏洞（{', '.join(upstream_only) if upstream_only else '无'}）不进入主比较；下游独有漏洞为 {', '.join(downstream_only'none''downstream_only else '无'}。
2. 对齐时将下游 `Zip-263` 与上游 `Zip4j-263` 视为同一漏洞，并将下游 `san2patch` 与上游 `San2Age'none''为同一工具，以 `San2Patch` 展示。
3. “修复”仅指上游 `Fixed` 或下游 `success`。`Compilation Failed/编译错误`、`Not Fixed/修复失败` 和 `No Patch/empty` 均计入分母。
4. 同一漏洞可能对应多个下游项目。主图先计算每个“漏洞 × 工具”的下游项目修复比例，再对 {len(common_cves)} 个漏洞等权平均；这样不会让下游项目更多的漏洞获得更高权重。
5. 置信区间通过以漏洞为单位、固定随机种子 {RANDOM_SEED} 的 {BOOTSTRAP_SAMPLES:,} 次 bootstrap 得到。它描述抽样不确定性，不构成上下游难度差异的因果证明。
6. `repair_rate_summary.csv` 还提供按下游任务直接加权的 micro 修复率，便于做敏感性检查。

## 文件

- `repair_rate_comparison.svg/.png`：分工具修复率柱状图及 95% CI。
- `dumbbell_plot.svg/.png`：分工具上下游差值哑铃图。
- `repair_rate_summary.csv`：汇总修复率、置信区间和两种下游加权口径。
- `matched_cve_details.csv`：共同漏洞的逐工具配对明细。
- `generate_comparison.py`：从两份原始 CSV 重新生成全部结果。
- `render_png.py`：默认 Python 无绘图库时使用的 PNG 回退渲染器。
"""
    (HERE / "analysis_summary.md").write_text(summary_md, encoding="utf-8")

    print(f"共同漏洞: {len(common_cves)}；下游任务: {sum(len(downstream_by_cve[cve]) for cve in common_cves)}")
    print(f"上游总体修复率: {pct(overall_up)}")
    print(f"下游总体修复率: {pct(overall_down)}")
    print(f"差值（上游 - 下游）: {(overall_up - overall_down) * 100:+.1f} pp")
    print(f"PNG: repair_rate_comparison={'success''bar_png else '未生成'not_generated'ted'_plot={'成功' if dumb'success'' else '未生成'}")


if __"not_generated"ted"