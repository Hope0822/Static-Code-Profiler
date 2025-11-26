from __future__ import annotations

import base64
import html
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple


# 阈值配置
CC_HIGH = 10
CC_MED = 7
LEN_HIGH = 60
LEN_MED = 40
NEST_HIGH = 5
NEST_MED = 3
DOC_LOW = 0.30
COMMENT_LOW = 0.02
LONG_LINE_HIGH = 0.10
NAMING_HIGH = 0.10


def _img_to_base64(img_path: Path) -> Optional[str]:
    if not img_path.exists():
        return None
    data = img_path.read_bytes()
    return base64.b64encode(data).decode("utf-8")


def _cc_bucket(cc: int) -> str:
    if cc <= 3:
        return "1-3"
    if cc <= 6:
        return "4-6"
    if cc <= 10:
        return "7-10"
    return "11+"


def _len_bucket(ln: int) -> str:
    if ln <= 20:
        return "1-20"
    if ln <= 40:
        return "21-40"
    if ln <= 60:
        return "41-60"
    return "61+"


def _file_anchor(file_path: str) -> str:
    safe = (
        file_path.replace("\\", "_")
        .replace("/", "_")
        .replace(".", "_")
        .replace(":", "")
    )
    return f"file_{safe}"


def _read_func_preview(
    file_path: str,
    lineno: Optional[int],
    length: int,
    max_lines: int = 30,
) -> str:
    """
    Read source preview of a function.
    - lineno: start line (1-based)
    - length: estimated function length
    - max_lines: show at most N lines
    """
    if lineno is None:
        return "(no lineno info)"

    try:
        lines = Path(file_path).read_text(encoding="utf-8").splitlines()
    except Exception:
        return "(failed to read source)"

    start = max(lineno - 1, 0)
    est_end = min(start + max(length, 1), len(lines))
    end = min(est_end, start + max_lines)

    snippet = lines[start:end]
    if end < est_end:
        snippet.append("... (truncated)")

    return "\n".join(snippet)


def _preview_block(preview_text: str) -> str:
    safe_text = html.escape(preview_text)
    return f"""
    <details>
      <summary style="cursor:pointer; color:#bcd2ff;">展开预览</summary>
      <pre style="white-space:pre-wrap; background:#0b1020; padding:10px; border-radius:8px; border:1px solid #222a4d;">
{safe_text}
      </pre>
    </details>
    """


def risk_level(cc: int, length: int, nest: int) -> Tuple[str, str]:
    score = 0
    reasons = []

    if cc >= CC_HIGH:
        score += 2
        reasons.append(f"CC≥{CC_HIGH}")
    elif cc >= CC_MED:
        score += 1
        reasons.append(f"CC≥{CC_MED}")

    if length >= LEN_HIGH:
        score += 2
        reasons.append(f"LEN≥{LEN_HIGH}")
    elif length >= LEN_MED:
        score += 1
        reasons.append(f"LEN≥{LEN_MED}")

    if nest >= NEST_HIGH:
        score += 2
        reasons.append(f"NEST≥{NEST_HIGH}")
    elif nest >= NEST_MED:
        score += 1
        reasons.append(f"NEST≥{NEST_MED}")

    if score >= 4:
        return "high", ", ".join(reasons) or "综合偏高"
    if score >= 2:
        return "medium", ", ".join(reasons) or "中等风险"
    return "low", ", ".join(reasons) or "低风险"


def build_summary(
    func_stats: List[Dict[str, Any]],
    file_stats: List[Dict[str, Any]],
) -> Dict[str, Any]:
    ccs = [f["cc"] for f in func_stats]
    lens = [f["length"] for f in func_stats]

    summary = {
        "num_files": len(file_stats),
        "num_functions": len(func_stats),
        "cc_avg": round(sum(ccs) / len(ccs), 2) if ccs else 0,
        "cc_max": max(ccs) if ccs else 0,
        "len_avg": round(sum(lens) / len(lens), 2) if lens else 0,
        "len_max": max(lens) if lens else 0,
        "cc_dist": {"1-3": 0, "4-6": 0, "7-10": 0, "11+": 0},
        "len_dist": {"1-20": 0, "21-40": 0, "41-60": 0, "61+": 0},
        "file_metric_avg": {
            "comment_ratio": 0,
            "docstring_coverage": 0,
            "long_line_ratio": 0,
            "naming_issue_ratio": 0,
            "unused_imports_count": 0,
        },
    }

    for cc in ccs:
        summary["cc_dist"][_cc_bucket(cc)] += 1
    for ln in lens:
        summary["len_dist"][_len_bucket(ln)] += 1

    if file_stats:
        for k in summary["file_metric_avg"].keys():
            summary["file_metric_avg"][k] = round(
                sum(fs.get(k, 0) for fs in file_stats) / len(file_stats), 3
            )

    return summary


def detect_smells(
    func_stats: List[Dict[str, Any]],
    file_stats: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    smells: List[Dict[str, Any]] = []

    # 函数级 smells
    for f in func_stats:
        cc, ln, nest = f["cc"], f["length"], f["nest"]
        file, name = f["file"], f["name"]

        if cc >= CC_HIGH:
            smells.append(
                {
                    "type": "高复杂度函数",
                    "level": "high",
                    "target": "function",
                    "file": file,
                    "name": name,
                    "detail": f"CC={cc}",
                }
            )
        elif cc >= CC_MED:
            smells.append(
                {
                    "type": "中高复杂度函数",
                    "level": "medium",
                    "target": "function",
                    "file": file,
                    "name": name,
                    "detail": f"CC={cc}",
                }
            )

        if ln >= LEN_HIGH:
            smells.append(
                {
                    "type": "超长函数",
                    "level": "high",
                    "target": "function",
                    "file": file,
                    "name": name,
                    "detail": f"LEN={ln}",
                }
            )
        elif ln >= LEN_MED:
            smells.append(
                {
                    "type": "较长函数",
                    "level": "medium",
                    "target": "function",
                    "file": file,
                    "name": name,
                    "detail": f"LEN={ln}",
                }
            )

        if nest >= NEST_HIGH:
            smells.append(
                {
                    "type": "深嵌套函数",
                    "level": "high",
                    "target": "function",
                    "file": file,
                    "name": name,
                    "detail": f"NEST={nest}",
                }
            )
        elif nest >= NEST_MED:
            smells.append(
                {
                    "type": "较深嵌套函数",
                    "level": "medium",
                    "target": "function",
                    "file": file,
                    "name": name,
                    "detail": f"NEST={nest}",
                }
            )

    # 文件级 smells
    for fs in file_stats:
        file = fs["file"]

        if fs["docstring_coverage"] < DOC_LOW:
            smells.append(
                {
                    "type": "Docstring覆盖偏低",
                    "level": "medium",
                    "target": "file",
                    "file": file,
                    "name": "",
                    "detail": f"DOC={fs['docstring_coverage']:.2f}",
                }
            )
        if fs["comment_ratio"] < COMMENT_LOW:
            smells.append(
                {
                    "type": "注释率偏低",
                    "level": "medium",
                    "target": "file",
                    "file": file,
                    "name": "",
                    "detail": f"COMMENT={fs['comment_ratio']:.2f}",
                }
            )
        if fs["long_line_ratio"] > LONG_LINE_HIGH:
            smells.append(
                {
                    "type": "长行比例偏高",
                    "level": "medium",
                    "target": "file",
                    "file": file,
                    "name": "",
                    "detail": f"LONG_LINE={fs['long_line_ratio']:.2f}",
                }
            )
        if fs["naming_issue_ratio"] > NAMING_HIGH:
            smells.append(
                {
                    "type": "命名问题偏多",
                    "level": "medium",
                    "target": "file",
                    "file": file,
                    "name": "",
                    "detail": f"NAMING={fs['naming_issue_ratio']:.2f}",
                }
            )

        # Unused imports
        if fs.get("unused_imports_count", 0) > 0:
            smells.append(
                {
                    "type": "未使用导入(Imports)",
                    "level": "medium",
                    "target": "file",
                    "file": file,
                    "name": "",
                    "detail": "unused=" + ", ".join(fs.get("unused_imports", [])),
                }
            )

    return smells


def build_file_risk_ranking(
    func_stats: List[Dict[str, Any]],
    smells: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    files: Dict[str, Dict[str, Any]] = {}

    for f in func_stats:
        file = f["file"]
        files.setdefault(
            file,
            {
                "file": file,
                "func_count": 0,
                "cc_sum": 0,
                "cc_max": 0,
                "len_sum": 0,
                "len_max": 0,
                "nest_sum": 0,
                "nest_max": 0,
                "high_smells": 0,
                "med_smells": 0,
            },
        )
        d = files[file]
        d["func_count"] += 1
        d["cc_sum"] += f["cc"]
        d["cc_max"] = max(d["cc_max"], f["cc"])
        d["len_sum"] += f["length"]
        d["len_max"] = max(d["len_max"], f["length"])
        d["nest_sum"] += f["nest"]
        d["nest_max"] = max(d["nest_max"], f["nest"])

    for s in smells:
        file = s["file"]
        if file not in files:
            files[file] = {
                "file": file,
                "func_count": 0,
                "cc_sum": 0,
                "cc_max": 0,
                "len_sum": 0,
                "len_max": 0,
                "nest_sum": 0,
                "nest_max": 0,
                "high_smells": 0,
                "med_smells": 0,
            }
        if s["level"] == "high":
            files[file]["high_smells"] += 1
        else:
            files[file]["med_smells"] += 1

    ranking = []
    for file, d in files.items():
        fc = d["func_count"] or 1
        ranking.append(
            {
                "file": file,
                "anchor": _file_anchor(file),
                "func_count": d["func_count"],
                "high_smells": d["high_smells"],
                "med_smells": d["med_smells"],
                "cc_avg": round(d["cc_sum"] / fc, 2),
                "cc_max": d["cc_max"],
                "len_avg": round(d["len_sum"] / fc, 2),
                "len_max": d["len_max"],
                "nest_avg": round(d["nest_sum"] / fc, 2),
                "nest_max": d["nest_max"],
            }
        )

    ranking.sort(
        key=lambda x: (x["high_smells"], x["med_smells"], x["cc_max"], x["len_max"]),
        reverse=True,
    )
    return ranking


def generate_html_report(
    func_stats: List[Dict[str, Any]],
    file_stats: List[Dict[str, Any]],
    charts_dir: Path,
    out_path: Path,
    top_n: int = 10,
) -> None:
    charts_dir.mkdir(parents=True, exist_ok=True)

    cc_img_b64 = _img_to_base64(charts_dir / "cc_distribution.png")
    len_img_b64 = _img_to_base64(charts_dir / "len_distribution.png")
    heat_img_b64 = _img_to_base64(charts_dir / "file_heatmap.png")

    summary = build_summary(func_stats, file_stats)
    smells = detect_smells(func_stats, file_stats)
    file_ranking = build_file_risk_ranking(func_stats, smells)

    high_smells = [s for s in smells if s["level"] == "high"]
    med_smells = [s for s in smells if s["level"] == "medium"]
    top_funcs = sorted(
        func_stats, key=lambda x: (x["cc"], x["length"]), reverse=True
    )[:top_n]

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def img_block(b64: Optional[str], title: str) -> str:
        if not b64:
            return f"<p><i>Chart not found: {title}</i></p>"
        return f"""
        <div class="card">
          <h3>{title}</h3>
          <img src="data:image/png;base64,{b64}" />
        </div>
        """

    def smell_badge(level: str) -> str:
        cls = "badge-high" if level == "high" else "badge-med"
        text = "High" if level == "high" else "Medium"
        return f"<span class='badge {cls}'>{text}</span>"

    html_doc = f"""
<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8"/>
  <title>CycloCalc Report</title>
  <style>
    body {{
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Arial, "PingFang SC", "Microsoft YaHei", sans-serif;
      background: #0b1020;
      color: #e6e9f2;
      margin: 0; padding: 0;
    }}
    header {{
      background: linear-gradient(90deg, #1b2a6b, #6b1b5b);
      padding: 24px 32px;
    }}
    header h1 {{ margin: 0; font-size: 26px; }}
    header .meta {{ opacity: .8; margin-top: 6px; font-size: 14px; }}
    .container {{ padding: 24px 32px; max-width: 1100px; margin: 0 auto; }}
    .grid {{
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 16px;
    }}
    .card {{
      background: #141a33;
      border: 1px solid #222a4d;
      border-radius: 14px;
      padding: 16px;
      box-shadow: 0 6px 18px rgba(0,0,0,.25);
    }}
    .card h2 {{ margin: 0 0 10px 0; font-size: 18px; }}
    .card h3 {{ margin: 0 0 10px 0; font-size: 16px; }}
    img {{ width: 100%; border-radius: 10px; background: #0b1020; }}
    table {{
      width: 100%;
      border-collapse: collapse;
      font-size: 14px;
      margin-top: 8px;
    }}
    th, td {{
      padding: 8px 10px;
      border-bottom: 1px solid #252d52;
      text-align: left;
      vertical-align: top;
    }}
    th {{
      position: sticky; top: 0;
      background: #141a33;
      z-index: 1;
    }}
    tr.risk-high td {{ background: rgba(255, 80, 80, 0.08); }}
    tr.risk-medium td {{ background: rgba(255, 200, 80, 0.08); }}
    tr.risk-low td {{ background: rgba(80, 255, 160, 0.06); }}

    .pill {{
      display: inline-block;
      padding: 2px 8px;
      border-radius: 999px;
      font-size: 12px;
      background: #252d52;
    }}
    .muted {{ opacity: .8; }}

    .badge {{
      display: inline-block;
      padding: 2px 8px;
      border-radius: 999px;
      font-size: 12px;
      margin-right: 6px;
    }}
    .badge-high {{ background: rgba(255, 80, 80, 0.22); color: #ffb1b1; }}
    .badge-med {{ background: rgba(255, 200, 80, 0.22); color: #ffe4a3; }}

    a.filelink {{ color: #bcd2ff; text-decoration: none; }}
    a.filelink:hover {{ text-decoration: underline; }}

    footer {{
      padding: 16px 32px;
      border-top: 1px solid #222a4d;
      font-size: 13px;
      opacity: .8;
    }}
    @media (max-width: 900px) {{
      .grid {{ grid-template-columns: 1fr; }}
    }}
  </style>
</head>
<body>
<header>
  <h1>CycloCalc 代码质量分析报告</h1>
  <div class="meta">Generated at {now}</div>
</header>

<div class="container">

  <div class="grid">
    <div class="card">
      <h2>项目汇总</h2>
      <p>文件数：<b>{summary["num_files"]}</b>　函数数：<b>{summary["num_functions"]}</b></p>
      <p>平均 CC：<b>{summary["cc_avg"]}</b>　最大 CC：<b>{summary["cc_max"]}</b></p>
      <p>平均 LEN：<b>{summary["len_avg"]}</b>　最大 LEN：<b>{summary["len_max"]}</b></p>
      <p class="muted">CC 分布：{summary["cc_dist"]}</p>
      <p class="muted">LEN 分布：{summary["len_dist"]}</p>
    </div>

    <div class="card">
      <h2>文件级指标均值</h2>
      <p><span class="pill">注释率</span> {summary["file_metric_avg"]["comment_ratio"]}</p>
      <p><span class="pill">Docstring 覆盖</span> {summary["file_metric_avg"]["docstring_coverage"]}</p>
      <p><span class="pill">长行比例</span> {summary["file_metric_avg"]["long_line_ratio"]}</p>
      <p><span class="pill">命名问题比例</span> {summary["file_metric_avg"]["naming_issue_ratio"]}</p>
      <p><span class="pill">Unused Imports</span> {summary["file_metric_avg"]["unused_imports_count"]}</p>
    </div>
  </div>

  <div style="height:14px"></div>

  <div class="card">
    <h2>自动结论</h2>
    <p>共检测到 <b>{len(smells)}</b> 条坏味道，其中
       <b>{len(high_smells)}</b> 条 High 风险，
       <b>{len(med_smells)}</b> 条 Medium 风险。</p>
  </div>

  <div style="height:14px"></div>

  <div class="card">
    <h2>Top 风险文件排行</h2>
    <table>
      <thead>
        <tr>
          <th>#</th><th>文件</th><th>High</th><th>Medium</th><th>#函数</th>
          <th>CC(avg/max)</th><th>LEN(avg/max)</th><th>NEST(avg/max)</th>
        </tr>
      </thead>
      <tbody>
        {''.join(
          f"<tr>"
          f"<td>{i+1}</td>"
          f"<td><a class='filelink' href='#{fr['anchor']}'>{fr['file']}</a></td>"
          f"<td>{fr['high_smells']}</td>"
          f"<td>{fr['med_smells']}</td>"
          f"<td>{fr['func_count']}</td>"
          f"<td>{fr['cc_avg']} / {fr['cc_max']}</td>"
          f"<td>{fr['len_avg']} / {fr['len_max']}</td>"
          f"<td>{fr['nest_avg']} / {fr['nest_max']}</td>"
          f"</tr>"
          for i, fr in enumerate(file_ranking)
        )}
      </tbody>
    </table>
  </div>

  <div style="height:14px"></div>

  <div class="grid">
    {img_block(cc_img_b64, "CC 圈复杂度分布")}
    {img_block(len_img_b64, "函数长度（LEN）分布")}
  </div>

  <div style="height:14px"></div>

  {img_block(heat_img_b64, "文件级风险热力图（Top Files）")}

  <div style="height:14px"></div>

  <div class="card">
    <h2>Top {top_n} 高风险函数（含源码预览）</h2>
    <table>
      <thead>
        <tr>
          <th>#</th>
          <th>函数</th>
          <th>文件</th>
          <th>CC</th>
          <th>LEN</th>
          <th>NEST</th>
          <th>风险</th>
          <th>原因</th>
          <th>行号</th>
          <th>Preview</th>
        </tr>
      </thead>
      <tbody>
        {''.join(
          (lambda i, f:
            (lambda level_reason:
              f"<tr class='risk-{level_reason[0]}'>"
              f"<td>{i+1}</td>"
              f"<td><code>{f['name']}</code></td>"
              f"<td class='muted'><a class='filelink' href='#{_file_anchor(f['file'])}'>{f['file']}</a></td>"
              f"<td>{f['cc']}</td>"
              f"<td>{f['length']}</td>"
              f"<td>{f['nest']}</td>"
              f"<td>{level_reason[0].upper()}</td>"
              f"<td class='muted'>{level_reason[1]}</td>"
              f"<td>{f.get('lineno','')}</td>"
              f"<td>{_preview_block(_read_func_preview(f['file'], f.get('lineno'), f['length']))}</td>"
              f"</tr>"
            )(risk_level(f['cc'], f['length'], f['nest']))
          )(*pair)
          for pair in enumerate(top_funcs)
        )}
      </tbody>
    </table>
  </div>

  <div style="height:14px"></div>

  <div class="card">
    <h2>坏味道（Smells）列表</h2>
    <table>
      <thead>
        <tr>
          <th>#</th><th>等级</th><th>类型</th><th>目标</th><th>文件</th><th>函数</th><th>详情</th>
        </tr>
      </thead>
      <tbody>
        {''.join(
          f"<tr>"
          f"<td>{i+1}</td>"
          f"<td>{smell_badge(s['level'])}</td>"
          f"<td>{s['type']}</td>"
          f"<td>{'函数' if s['target']=='function' else '文件'}</td>"
          f"<td class='muted'><a class='filelink' href='#{_file_anchor(s['file'])}'>{s['file']}</a></td>"
          f"<td><code>{s['name']}</code></td>"
          f"<td class='muted'>{s['detail']}</td>"
          f"</tr>"
          for i, s in enumerate(smells)
        )}
      </tbody>
    </table>
  </div>

  <div style="height:14px"></div>

  <div class="card">
    <h2>文件级质量明细</h2>
    <table>
      <thead>
        <tr>
          <th>文件</th><th>注释率</th><th>Docstring 覆盖</th><th>长行比例</th><th>命名问题</th><th>Unused Imports</th>
        </tr>
      </thead>
      <tbody>
        {''.join(
          f"<tr id='{_file_anchor(fs['file'])}'>"
          f"<td><code>{fs['file']}</code></td>"
          f"<td>{fs['comment_ratio']:.2f}</td>"
          f"<td>{fs['docstring_coverage']:.2f}</td>"
          f"<td>{fs['long_line_ratio']:.2f}</td>"
          f"<td>{fs['naming_issue_ratio']:.2f}</td>"
          f"<td>{fs.get('unused_imports_count',0)}</td>"
          f"</tr>"
          for fs in file_stats
        )}
      </tbody>
    </table>
  </div>

</div>

<footer>
  <div>Notes: 指标为静态分析近似估计，用于课程设计演示与风险提示。</div>
</footer>
</body>
</html>
"""

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(html_doc, encoding="utf-8")
