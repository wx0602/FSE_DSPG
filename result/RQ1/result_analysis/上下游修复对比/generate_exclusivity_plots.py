#!/usr/bin/env python3
"""生成上下游独占修复蝴蝶图和 CVE×工具四状态热力图。

下游采用严格口径：对于一个“CVE × 工具”，该 CVE 对应的全部下游项目
都为 success 时，才认为该工具在下游修复了该 CVE。

默认 Python 缺少 Matplotlib 时，脚本会自动切换到 /usr/bin/python3。
"""

from __future__ import annotations

import csv
import os
import re
import sys
from collections import defaultdict
from pathlib import Path


def ensure_plotting_runtime() -> None:
    try:
        import matplotlib  # noqa: F401
        import numpy  # noqa: F401
    except ModuleNotFoundError:
        system_python = Path("/usr/bin/python3")
        current_python = Path(sys.executable).resolve()
        if system_python.exists() and current_python != system_python.resolve():
            os.execv(str(system_python), [str(system_python), *sys.argv])
        raise


ensure_plotting_runtime()

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import ListedColormap
from matplotlib.patches import Patch
from matplotlib.ticker import FuncFormatter, MultipleLocator


HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
DOWNSTREAM_CSV = ROOT / "CVE 描述验证结果_矩阵.csv"
UPSTREAM_CSV = ROOT / "上游漏洞修复结果" / "上游漏洞修复结果.csv"

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

ID_PATTERN = re.compile(
    r"(CVE-\d{4}-\d+|CODEC-\d+|IO-\d+|LANG-\d+|TEXT-\d+|Zip(?:4j)?-\d+)",
    re.IGNORECASE,
)

UPSTREAM_COLOR = "#2F6BFF"
DOWNSTREAM_COLOR = "#F26B5B"
BOTH_COLOR = "#39A878"
NEITHER_COLOR = "#E5EAF1"
TEXT_COLOR = "#172033"
MUTED_COLOR = "#657187"
GRID_COLOR = "#DCE3EC"


def configure_style() -> None:
    plt.rcParams.update(
        {
            "font.family": "sans-serif",
            "font.sans-serif": ["Noto Sans CJK SC", "Noto Sans CJK JP", "DejaVu Sans"],
            "axes.unicode_minus": False,
            "text.color": TEXT_COLOR,
            "axes.labelcolor": TEXT_COLOR,
            "xtick.color": MUTED_COLOR,
            "ytick.color": MUTED_COLOR,
            "svg.fonttype": "none",
        }
    )


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def vulnerability_id(raw: str) -> str:
    match = ID_PATTERN.match(raw.strip())
    if not match:
        raise ValueError(f"无法提取漏洞编号: {raw!r}")
    result = match.group(1).upper()
    return "ZIP4J-263" if result == "ZIP-263" else result


def build_records():
    downstream_rows = read_csv(DOWNSTREAM_CSV)
    upstream_rows = [
        row for row in read_csv(UPSTREAM_CSV) if row["CVE"].strip() != "Summary"
    ]

    downstream_by_cve = defaultdict(list)
    for row in downstream_rows:
        downstream_by_cve[vulnerability_id(row["target_id"])].append(row)
    upstream_by_cve = {
        vulnerability_id(row["CVE"]): row for row in upstream_rows
    }
    common_cves = sorted(set(downstream_by_cve) & set(upstream_by_cve))

    cve_records = []
    cell_records = []
    for cve in common_cves:
        upstream_count = 0
        downstream_count = 0
        states = []
        for display_name, downstream_column, upstream_column in TOOLS:
            upstream_fixed = upstream_by_cve[cve][upstream_column].strip() == "Fixed"
            downstream_fixed = all(
                row[downstream_column].strip() == "success"
                for row in downstream_by_cve[cve]
            )
            upstream_count += int(upstream_fixed)
            downstream_count += int(downstream_fixed)
            if upstream_fixed and downstream_fixed:
                state, state_code = "上下游均修复", 2
            elif upstream_fixed:
                state, state_code = "仅上游修复", 1
            elif downstream_fixed:
                state, state_code = "仅下游修复", 3
            else:
                state, state_code = "均未修复", 0
            states.append(state_code)
            cell_records.append(
                {
                    "cve": cve,
                    "tool": display_name,
                    "upstream_fixed": int(upstream_fixed),
                    "downstream_all_projects_fixed": int(downstream_fixed),
                    "state": state,
                }
            )

        if upstream_count > 0 and downstream_count == 0:
            category = "仅上游可修复"
        elif downstream_count > 0 and upstream_count == 0:
            category = "仅下游可修复"
        elif upstream_count > 0 and downstream_count > 0:
            category = "上下游均可修复"
        else:
            category = "上下游均不可修复"
        cve_records.append(
            {
                "cve": cve,
                "downstream_projects": len(downstream_by_cve[cve]),
                "upstream_fixed_tools": upstream_count,
                "downstream_fixed_tools": downstream_count,
                "difference": upstream_count - downstream_count,
                "category": category,
                "states": states,
            }
        )
    return cve_records, cell_records


def save_data(cve_records, cell_records) -> None:
    with (HERE / "cve_exclusivity_summary.csv").open(
        "w", encoding="utf-8-sig", newline=""
    ) as handle:
        fields = [
            "cve",
            "downstream_projects",
            "upstream_fixed_tools",
            "downstream_fixed_tools",
            "difference",
            "category",
        ]
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in cve_records:
            writer.writerow({key: row[key] for key in fields})

    with (HERE / "cve_tool_four_states.csv").open(
        "w", encoding="utf-8-sig", newline=""
    ) as handle:
        fields = list(cell_records[0])
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(cell_records)


def save_figure(figure, basename: str, dpi: int = 180) -> None:
    figure.savefig(HERE / f"{basename}.png", dpi=dpi, facecolor="white")
    figure.savefig(HERE / f"{basename}.svg", facecolor="white")
    plt.close(figure)


def make_butterfly(cve_records) -> None:
    upstream_only = sorted(
        [row for row in cve_records if row["category"] == "仅上游可修复"],
        key=lambda row: (-row["upstream_fixed_tools"], row["cve"]),
    )
    downstream_only = sorted(
        [row for row in cve_records if row["category"] == "仅下游可修复"],
        key=lambda row: (-row["downstream_fixed_tools"], row["cve"]),
    )
    rows = [*upstream_only, *downstream_only]
    y = np.arange(len(rows))
    upstream = np.array([row["upstream_fixed_tools"] for row in rows])
    downstream = -np.array([row["downstream_fixed_tools"] for row in rows])

    figure, axis = plt.subplots(figsize=(11, 8.2), dpi=160)
    figure.patch.set_facecolor("white")
    split = len(upstream_only)
    axis.axhspan(-0.5, split - 0.5, color="#EFF4FF", zorder=0)
    axis.axhspan(split - 0.5, len(rows) - 0.5, color="#FFF2F0", zorder=0)
    axis.barh(y, upstream, height=0.58, color=UPSTREAM_COLOR, zorder=3)
    axis.barh(y, downstream, height=0.58, color=DOWNSTREAM_COLOR, zorder=3)
    axis.axvline(0, color=TEXT_COLOR, linewidth=1.4, zorder=4)

    for index, row in enumerate(rows):
        up = row["upstream_fixed_tools"]
        down = row["downstream_fixed_tools"]
        if up:
            axis.text(up + 0.18, index, f"{up}/9", va="center", ha="left", fontsize=9, fontweight="bold")
        if down:
            axis.text(-down - 0.18, index, f"{down}/9", va="center", ha="right", fontsize=9, fontweight="bold")
        project_note = f"  ({row['downstream_projects']}个下游项目)" if row["downstream_projects"] > 1 else ""
        axis.text(
            0,
            index,
            f"  {row['cve']}{project_note}",
            va="center",
            ha="left",
            fontsize=9.2,
            color=TEXT_COLOR,
            fontweight="bold" if row["category"] == "仅上游可修复" else "normal",
            zorder=5,
        )

    axis.set_xlim(-9.8, 9.8)
    axis.set_ylim(-0.7, len(rows) - 0.3)
    axis.invert_yaxis()
    axis.set_yticks([])
    axis.xaxis.set_major_locator(MultipleLocator(1))
    axis.xaxis.set_major_formatter(FuncFormatter(lambda value, _: f"{abs(int(value))}"))
    axis.grid(axis="x", color=GRID_COLOR, linewidth=0.7, zorder=1)
    for spine in axis.spines.values():
        spine.set_visible(False)
    axis.tick_params(axis="x", length=0, labelsize=9)
    axis.set_xlabel("成功修复该 CVE 的工具数（共9个工具）", fontsize=11, fontweight="bold", labelpad=12)
    axis.set_title("上下游独占修复的漏洞", loc="left", fontsize=20, fontweight="bold", pad=48)
    axis.text(
        0,
        1.035,
        "仅展示一侧至少有一个工具成功、另一侧无任何工具成功的 CVE",
        transform=axis.transAxes,
        fontsize=10,
        color=MUTED_COLOR,
    )
    axis.text(
        0.02,
        0.995,
        f"仅下游可修复（{len(downstream_only)}个） ←",
        transform=axis.transAxes,
        ha="left",
        va="top",
        fontsize=10,
        color=DOWNSTREAM_COLOR,
        fontweight="bold",
    )
    axis.text(
        0.98,
        0.995,
        f"→ 仅上游可修复（{len(upstream_only)}个）",
        transform=axis.transAxes,
        ha="right",
        va="top",
        fontsize=10,
        color=UPSTREAM_COLOR,
        fontweight="bold",
    )
    axis.legend(
        handles=[
            Patch(facecolor=DOWNSTREAM_COLOR, label="仅下游"),
            Patch(facecolor=UPSTREAM_COLOR, label="仅上游"),
        ],
        frameon=False,
        ncol=2,
        loc="upper right",
        bbox_to_anchor=(1, 1.13),
    )
    figure.text(
        0.13,
        0.025,
        "严格下游口径：一个工具必须修复该 CVE 的全部下游项目，才记为下游成功。",
        fontsize=9,
        color=MUTED_COLOR,
    )
    figure.subplots_adjust(left=0.10, right=0.97, top=0.83, bottom=0.11)
    save_figure(figure, "cve_exclusivity_butterfly")


def make_heatmap(cve_records) -> None:
    priority = {
        "仅上游可修复": 0,
        "上下游均可修复": 1,
        "上下游均不可修复": 2,
        "仅下游可修复": 3,
    }
    rows = sorted(
        cve_records,
        key=lambda row: (
            priority[row["category"]],
            -row["difference"] if row["category"] != "仅下游可修复" else row["difference"],
            row["cve"],
        ),
    )
    if len(rows) != 40:
        raise ValueError(f"20×18 布局要求40个共同漏洞，实际为 {len(rows)} 个")
    blocks = [rows[:20], rows[20:]]
    cmap = ListedColormap([NEITHER_COLOR, UPSTREAM_COLOR, BOTH_COLOR, DOWNSTREAM_COLOR])

    # 两个20×9区块并排：整图为20行、18个工具状态列。
    # 同时保留20 cm × 18 cm的论文版面尺寸及300 dpi输出。
    figure, axes = plt.subplots(1, 2, figsize=(20 / 2.54, 18 / 2.54), dpi=300)
    figure.patch.set_facecolor("white")
    category_colors = {
        "仅上游可修复": UPSTREAM_COLOR,
        "仅下游可修复": DOWNSTREAM_COLOR,
        "上下游均可修复": BOTH_COLOR,
        "上下游均不可修复": MUTED_COLOR,
    }

    for block_index, (axis, block) in enumerate(zip(axes, blocks), start=1):
        matrix = np.array([row["states"] for row in block])
        axis.imshow(
            matrix,
            cmap=cmap,
            vmin=-0.5,
            vmax=3.5,
            aspect="auto",
            interpolation="none",
        )
        axis.set_xticks(np.arange(len(TOOLS)))
        axis.set_xticklabels(
            [tool[0] for tool in TOOLS], rotation=43, ha="left", fontsize=6.2
        )
        axis.xaxis.tick_top()
        axis.set_yticks(np.arange(len(block)))
        axis.set_yticklabels(
            [
                f"{row['cve']}  U{row['upstream_fixed_tools']}/D{row['downstream_fixed_tools']}"
                for row in block
            ],
            fontsize=5.7,
        )
        axis.tick_params(length=0)
        axis.set_xticks(np.arange(-0.5, len(TOOLS), 1), minor=True)
        axis.set_yticks(np.arange(-0.5, len(block), 1), minor=True)
        axis.grid(which="minor", color="white", linewidth=1.0)
        for spine in axis.spines.values():
            spine.set_visible(False)
        for label, row in zip(axis.get_yticklabels(), block):
            label.set_color(category_colors[row["category"]])
            if row["category"] in {"仅上游可修复", "仅下游可修复"}:
                label.set_fontweight("bold")

        # 仅在同一20行区块内部绘制类别分界线。
        for index in range(len(block) - 1):
            if block[index]["category"] != block[index + 1]["category"]:
                axis.axhline(index + 0.5, color=TEXT_COLOR, linewidth=1.2)

        axis.set_xlim(-0.5, len(TOOLS) - 0.5)
        axis.set_ylim(len(block) - 0.5, -0.5)
        axis.set_title(
            f"漏洞组 {block_index}（{(block_index-1)*20+1}–{block_index*20}）",
            fontsize=8,
            fontweight="bold",
            pad=38,
            color=MUTED_COLOR,
        )

    figure.text(
        0.08,
        0.975,
        "CVE × 工具的上下游修复状态（20行 × 18列）",
        ha="left",
        va="top",
        fontsize=15,
        fontweight="bold",
    )
    figure.text(
        0.08,
        0.948,
        "40个 CVE 分为两个20行区块并排展示；每个区块含9个工具列",
        ha="left",
        va="top",
        fontsize=7.5,
        color=MUTED_COLOR,
    )
    figure.legend(
        handles=[
            Patch(facecolor=UPSTREAM_COLOR, label="仅上游修复"),
            Patch(facecolor=DOWNSTREAM_COLOR, label="仅下游修复"),
            Patch(facecolor=BOTH_COLOR, label="上下游均修复"),
            Patch(facecolor=NEITHER_COLOR, edgecolor="#CAD2DE", label="均未修复"),
        ],
        frameon=False,
        ncol=4,
        loc="upper left",
        bbox_to_anchor=(0.075, 0.927),
        fontsize=7.2,
    )
    figure.text(
        0.08,
        0.018,
        "U/D：上游/下游成功工具数。严格下游口径：同一工具须修复该 CVE 的全部下游项目。",
        fontsize=7.0,
        color=MUTED_COLOR,
    )
    figure.subplots_adjust(left=0.20, right=0.98, top=0.78, bottom=0.07, wspace=0.68)
    save_figure(figure, "cve_tool_four_state_heatmap", dpi=300)


def main() -> None:
    configure_style()
    cve_records, cell_records = build_records()
    save_data(cve_records, cell_records)
    make_butterfly(cve_records)
    make_heatmap(cve_records)

    counts = defaultdict(int)
    for row in cve_records:
        counts[row["category"]] += 1
    print(f"共同漏洞: {len(cve_records)}")
    for category in ["仅上游可修复", "仅下游可修复", "上下游均可修复", "上下游均不可修复"]:
        print(f"{category}: {counts[category]}")
    print("已生成蝴蝶图、四状态热力图及对应 CSV。")


if __name__ == "__main__":
    main()
