#!/usr/bin/env python3
"""Parse the data.gov.tw full-catalog XML export and generate statistics.

Input : export*.csv  (actually XML, exported from data.gov.tw)
Output:
  - gov_export_stats.md          ── overall statistics summary
  - topics_gov_export/           ── one markdown file per 服務分類
      README.md
      <category>.md  (datasets listed alphabetically within the category)
"""

from __future__ import annotations

import sys
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
import xml.etree.ElementTree as ET


# ──────────────────────────────────────────────
# Data model
# ──────────────────────────────────────────────

@dataclass
class Dataset:
    nid: str
    name: str
    service_cat: str       # 服務分類
    quality: str           # 品質檢測
    file_formats: list[str]  # 檔案格式（可多個，; 分隔）
    agency: str            # 提供機關
    update_freq: str       # 更新頻率
    charge: str            # 計費方式
    pubdate: str           # 上架日期
    meta_updated: str      # 詮釋資料更新時間
    data_count: str        # 資料量
    description: str       # 資料集描述


# ──────────────────────────────────────────────
# Parsing
# ──────────────────────────────────────────────

def _text(elem: ET.Element, tag: str) -> str:
    val = elem.findtext(tag)
    return (val or "").strip()


def parse_export(path: Path) -> list[Dataset]:
    """Stream-parse the XML export with iterparse (memory-efficient)."""
    datasets: list[Dataset] = []
    print(f"Parsing {path.name} …", flush=True)

    with open(path, "r", encoding="utf-8") as fh:
        context = ET.iterparse(fh, events=("end",))
        for event, elem in context:
            if elem.tag != "node":
                continue

            fmt_raw = _text(elem, "檔案格式")
            formats = sorted({f.strip() for f in fmt_raw.split(";") if f.strip()})

            datasets.append(Dataset(
                nid=_text(elem, "資料集識別碼"),
                name=_text(elem, "資料集名稱"),
                service_cat=_text(elem, "服務分類") or "未分類",
                quality=_text(elem, "品質檢測") or "無",
                file_formats=formats,
                agency=_text(elem, "提供機關") or "未知機關",
                update_freq=_text(elem, "更新頻率") or "未知",
                charge=_text(elem, "計費方式") or "免費",
                pubdate=_text(elem, "上架日期")[:10],
                meta_updated=_text(elem, "詮釋資料更新時間")[:10],
                data_count=_text(elem, "資料量"),
                description=_text(elem, "資料集描述"),
            ))
            elem.clear()

    print(f"  → {len(datasets):,} 筆資料集", flush=True)
    return datasets


# ──────────────────────────────────────────────
# Statistics helpers
# ──────────────────────────────────────────────

def _bar(count: int, total: int, width: int = 20) -> str:
    filled = round(width * count / total) if total else 0
    return "█" * filled + "░" * (width - filled)


def _pct(count: int, total: int) -> str:
    return f"{count / total * 100:.1f}%" if total else "0.0%"


def build_stats(datasets: list[Dataset]) -> dict:
    total = len(datasets)
    service_cat  = Counter(d.service_cat for d in datasets)
    quality      = Counter(d.quality for d in datasets)
    update_freq  = Counter(d.update_freq for d in datasets)
    charge       = Counter(d.charge for d in datasets)
    agency       = Counter(d.agency for d in datasets)

    fmt_counter: Counter[str] = Counter()
    for d in datasets:
        for fmt in d.file_formats:
            fmt_counter[fmt] += 1

    # Most recently metadata-updated datasets
    recent = sorted(
        [d for d in datasets if d.meta_updated],
        key=lambda d: d.meta_updated,
        reverse=True,
    )[:20]

    return dict(
        total=total,
        service_cat=service_cat,
        quality=quality,
        update_freq=update_freq,
        charge=charge,
        agency=agency,
        fmt_counter=fmt_counter,
        recent=recent,
    )


# ──────────────────────────────────────────────
# Markdown generation
# ──────────────────────────────────────────────

def render_stats_md(stats: dict, generated_at: str) -> str:
    total         = stats["total"]
    service_cat   = stats["service_cat"]
    quality       = stats["quality"]
    update_freq   = stats["update_freq"]
    charge        = stats["charge"]
    agency        = stats["agency"]
    fmt_counter   = stats["fmt_counter"]
    recent        = stats["recent"]

    lines: list[str] = [
        "# 政府資料開放平臺 資料集統計報告",
        "",
        f"- 來源檔案：export CSV（XML 格式）",
        f"- 產生時間：{generated_at}",
        f"- 總資料集數：**{total:,}** 筆",
        "",
    ]

    # ── 服務分類 ──────────────────────────────
    lines += [
        "## 一、服務分類（Service Category）",
        "",
        f"> 共 **{len(service_cat)}** 個分類，涵蓋 {total:,} 筆資料集",
        "",
        "| 排名 | 服務分類 | 資料集數 | 佔比 | 分佈 |",
        "|---:|---|---:|---:|---|",
    ]
    for rank, (cat, cnt) in enumerate(service_cat.most_common(), start=1):
        lines.append(
            f"| {rank} | {cat} | {cnt:,} | {_pct(cnt, total)} | {_bar(cnt, total)} |"
        )
    lines.append("")

    # ── 品質標章 ──────────────────────────────
    quality_order = ["白金", "金", "銀", "銅", "無(白名單)", "無"]
    lines += [
        "## 二、品質標章（Quality Badge）",
        "",
        "| 標章等級 | 資料集數 | 佔比 |",
        "|---|---:|---:|",
    ]
    for lvl in quality_order:
        cnt = quality.get(lvl, 0)
        if cnt:
            lines.append(f"| {lvl} | {cnt:,} | {_pct(cnt, total)} |")
    # any leftover keys
    for lvl, cnt in quality.most_common():
        if lvl not in quality_order:
            lines.append(f"| {lvl} | {cnt:,} | {_pct(cnt, total)} |")
    lines.append("")

    # ── 檔案格式 ──────────────────────────────
    lines += [
        "## 三、提供檔案格式",
        "",
        "> 同一資料集可提供多種格式，故合計可能超過總數",
        "",
        "| 排名 | 格式 | 資源數 | 佔資料集比 |",
        "|---:|---|---:|---:|",
    ]
    for rank, (fmt, cnt) in enumerate(fmt_counter.most_common(15), start=1):
        lines.append(f"| {rank} | {fmt} | {cnt:,} | {_pct(cnt, total)} |")
    lines.append("")

    # ── 更新頻率 ──────────────────────────────
    lines += [
        "## 四、更新頻率",
        "",
        "| 排名 | 更新頻率 | 資料集數 | 佔比 |",
        "|---:|---|---:|---:|",
    ]
    for rank, (freq, cnt) in enumerate(update_freq.most_common(15), start=1):
        lines.append(f"| {rank} | {freq} | {cnt:,} | {_pct(cnt, total)} |")
    lines.append("")

    # ── 提供機關 Top 30 ─────────────────────
    lines += [
        "## 五、提供機關 Top 30",
        "",
        "| 排名 | 機關名稱 | 資料集數 | 佔比 |",
        "|---:|---|---:|---:|",
    ]
    for rank, (ag, cnt) in enumerate(agency.most_common(30), start=1):
        lines.append(f"| {rank} | {ag} | {cnt:,} | {_pct(cnt, total)} |")
    lines.append("")

    # ── 計費方式 ──────────────────────────────
    lines += [
        "## 六、計費方式",
        "",
        "| 計費方式 | 資料集數 | 佔比 |",
        "|---|---:|---:|",
    ]
    for method, cnt in charge.most_common():
        lines.append(f"| {method} | {cnt:,} | {_pct(cnt, total)} |")
    lines.append("")

    # ── 最近更新 ──────────────────────────────
    lines += [
        "## 七、最近更新的 20 筆資料集",
        "",
        "| 更新日期 | 資料集名稱 | 服務分類 | 提供機關 |",
        "|---|---|---|---|",
    ]
    for d in recent:
        name = d.name.replace("|", "\\|")
        agency_s = d.agency.replace("|", "\\|")
        lines.append(f"| {d.meta_updated} | {name} | {d.service_cat} | {agency_s} |")
    lines.append("")

    return "\n".join(lines)


def render_category_md(
    cat: str,
    datasets: list[Dataset],
    generated_at: str,
) -> str:
    """Markdown for a single 服務分類 file."""
    # Sort: quality badge order, then name
    quality_rank = {"白金": 0, "金": 1, "銀": 2, "銅": 3, "無(白名單)": 4, "無": 5}
    sorted_ds = sorted(
        datasets,
        key=lambda d: (quality_rank.get(d.quality, 9), d.name),
    )

    lines = [
        f"# 政府資料開放平臺｜{cat}",
        "",
        f"- 產生時間：{generated_at}",
        f"- 資料集數：**{len(datasets):,}** 筆",
        "",
        "| 排名 | 資料集名稱 | 品質標章 | 檔案格式 | 提供機關 | 更新頻率 | 詮釋資料更新 |",
        "|---:|---|---|---|---|---|---|",
    ]
    for idx, d in enumerate(sorted_ds, start=1):
        name = d.name.replace("|", "\\|")
        agency_s = d.agency.replace("|", "\\|")
        fmts = "/".join(d.file_formats) or "—"
        lines.append(
            f"| {idx} | {name} | {d.quality} | {fmts} | {agency_s} | {d.update_freq} | {d.meta_updated} |"
        )
    lines.append("")
    return "\n".join(lines)


# ──────────────────────────────────────────────
# File writing
# ──────────────────────────────────────────────

def write_topic_files(datasets: list[Dataset], topic_dir: Path, generated_at: str) -> None:
    topic_dir.mkdir(exist_ok=True)

    by_cat: dict[str, list[Dataset]] = defaultdict(list)
    for d in datasets:
        by_cat[d.service_cat].append(d)

    sorted_cats = sorted(by_cat.items(), key=lambda kv: len(kv[1]), reverse=True)

    # Individual category files
    for cat, ds in sorted_cats:
        safe = cat.replace("/", "_").replace("\\", "_").replace(" ", "_")
        (topic_dir / f"{safe}.md").write_text(
            render_category_md(cat, ds, generated_at), encoding="utf-8"
        )

    # README index
    readme_lines = [
        "# 政府資料開放平臺 各服務分類索引",
        "",
        f"- 產生時間：{generated_at}",
        f"- 分類數：{len(sorted_cats)}",
        "",
        "| 排名 | 服務分類 | 資料集數 | 檔案連結 |",
        "|---:|---|---:|---|",
    ]
    for rank, (cat, ds) in enumerate(sorted_cats, start=1):
        safe = cat.replace("/", "_").replace("\\", "_").replace(" ", "_")
        readme_lines.append(f"| {rank} | {cat} | {len(ds):,} | [{cat}]({safe}.md) |")
    readme_lines.append("")
    (topic_dir / "README.md").write_text("\n".join(readme_lines), encoding="utf-8")

    print(f"  → topics_gov_export/ 共 {len(sorted_cats)} 個分類檔案", flush=True)


# ──────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────

def find_export(base_dir: Path) -> Path:
    """Find the first export*.csv in the project directory."""
    candidates = sorted(base_dir.glob("export*.csv"))
    if not candidates:
        raise FileNotFoundError(f"找不到 export*.csv 於 {base_dir}")
    if len(candidates) > 1:
        print(f"[警告] 找到多個匯出檔，使用最新的: {candidates[-1].name}")
    return candidates[-1]


def main(export_path: Path | None = None) -> None:
    base_dir = Path(__file__).parent
    if export_path is None:
        export_path = find_export(base_dir)

    print(f"來源檔案: {export_path.name}  ({export_path.stat().st_size / 1_048_576:.1f} MB)")

    datasets = parse_export(export_path)
    stats    = build_stats(datasets)
    now      = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # 1. Overall stats markdown
    stats_md_path = base_dir / "gov_export_stats.md"
    stats_md_path.write_text(render_stats_md(stats, now), encoding="utf-8")
    print(f"  → {stats_md_path.name}")

    # 2. Per-category files
    write_topic_files(datasets, base_dir / "topics_gov_export", now)

    print("完成！")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        main(Path(sys.argv[1]))
    else:
        main()
