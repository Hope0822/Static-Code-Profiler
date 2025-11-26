from pathlib import Path
from typing import List, Dict, Any, Tuple
import matplotlib.pyplot as plt


def plot_cc_distribution(func_stats: List[Dict[str, Any]], out_dir: Path) -> None:
    ccs = [f["cc"] for f in func_stats]
    bins = ["1-3", "4-6", "7-10", "11+"]
    counts = [0, 0, 0, 0]

    for cc in ccs:
        if cc <= 3:
            counts[0] += 1
        elif cc <= 6:
            counts[1] += 1
        elif cc <= 10:
            counts[2] += 1
        else:
            counts[3] += 1

    plt.figure()
    plt.bar(bins, counts)
    plt.title("Cyclomatic Complexity (CC) Distribution")
    plt.xlabel("CC Range")
    plt.ylabel("Number of Functions")

    out_path = out_dir / "cc_distribution.png"
    plt.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close()


def plot_len_distribution(func_stats: List[Dict[str, Any]], out_dir: Path) -> None:
    lens = [f["length"] for f in func_stats]
    bins = ["1-20", "21-40", "41-60", "61+"]
    counts = [0, 0, 0, 0]

    for ln in lens:
        if ln <= 20:
            counts[0] += 1
        elif ln <= 40:
            counts[1] += 1
        elif ln <= 60:
            counts[2] += 1
        else:
            counts[3] += 1

    plt.figure()
    plt.bar(bins, counts)
    plt.title("Function Length (LOC) Distribution")
    plt.xlabel("Length Range (lines)")
    plt.ylabel("Number of Functions")

    out_path = out_dir / "len_distribution.png"
    plt.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close()


# ✅ 新增：文件级热力图
def plot_file_heatmap(
    func_stats: List[Dict[str, Any]],
    file_stats: List[Dict[str, Any]],
    out_dir: Path,
    top_k: int = 12,
) -> None:
    """
    Heatmap columns:
      CC_avg, CC_max, LEN_avg, LEN_max, NEST_avg, COMMENT_RATIO, DOCSTRING_COV
    Only show top_k risky files for readability.
    """
    # 聚合函数级到文件级
    agg: Dict[str, Dict[str, float]] = {}
    for f in func_stats:
        file = f["file"]
        a = agg.setdefault(file, {
            "cc_sum": 0, "cc_max": 0,
            "len_sum": 0, "len_max": 0,
            "nest_sum": 0, "nest_max": 0,
            "cnt": 0
        })
        a["cnt"] += 1
        a["cc_sum"] += f["cc"]; a["cc_max"] = max(a["cc_max"], f["cc"])
        a["len_sum"] += f["length"]; a["len_max"] = max(a["len_max"], f["length"])
        a["nest_sum"] += f["nest"]; a["nest_max"] = max(a["nest_max"], f["nest"])

    # 把 file_stats 合并进去
    rows: List[Tuple[str, List[float]]] = []
    for fs in file_stats:
        file = fs["file"]
        a = agg.get(file, {"cnt": 1, "cc_sum": 0, "cc_max": 0, "len_sum": 0, "len_max": 0, "nest_sum": 0, "nest_max": 0})
        cnt = max(a["cnt"], 1)

        cc_avg = a["cc_sum"] / cnt
        len_avg = a["len_sum"] / cnt
        nest_avg = a["nest_sum"] / cnt

        row = [
            cc_avg, a["cc_max"],
            len_avg, a["len_max"],
            nest_avg,
            fs["comment_ratio"],
            fs["docstring_coverage"],
        ]
        rows.append((file, row))

    # 按风险简单排序：cc_max + len_max + nest_max
    rows.sort(key=lambda x: (x[1][1] + x[1][3] + x[1][4]), reverse=True)
    rows = rows[:top_k]

    if not rows:
        return

    files = [r[0] for r in rows]
    data = [r[1] for r in rows]

    cols = ["CC_avg", "CC_max", "LEN_avg", "LEN_max", "NEST_avg", "COMMENT", "DOC"]

    plt.figure(figsize=(10, max(3, 0.5 * len(files))))
    im = plt.imshow(data, aspect="auto")

    plt.yticks(range(len(files)), files, fontsize=8)
    plt.xticks(range(len(cols)), cols, rotation=30, ha="right")

    plt.title("File-level Risk Heatmap (Top files)")
    plt.colorbar(im, fraction=0.03, pad=0.02)

    out_path = out_dir / "file_heatmap.png"
    plt.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close()
