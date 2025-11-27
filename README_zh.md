[English](README.md) | [中文](README_zh.md)


# SCP（Static Code Profiler）

**SCP** 是一个基于 Python `ast` 的静态代码分析工具，面向 Python 项目。  
它会使用**多种指标**对代码复杂度与质量风险进行画像，生成可视化结果，并输出**交互式 HTML 报告**。

> SCP = **Static Code Profiler**  
> 一个轻量但实用的多指标 Python 源码风险分析器。

---

## ✨ 亮点

- **纯静态分析**：基于 Python `ast`，无需运行代码
- **多指标 Profiling**
  - 函数级：**CC / LEN / NEST**
  - 文件级：**注释率 / Docstring 覆盖率 / 超长行比例 / 命名问题 / 未使用导入**
- **风险分级 + Smells 提示**（低 / 中 / 高）
- **可视化分析**
  - CC 分布图  
  - LEN 分布图  
  - **文件风险热力图**
- **交互式 HTML 报告**
  - Top 高风险文件与函数  
  - Smells 列表  
  - 内嵌图表  
  - **Top 函数源码可展开预览**
- **工程化 CLI**
  - 阈值过滤、忽略路径、JSON 导出、图表/报告输出
- **Windows 可执行程序**
  - 命令行版 `cyclocalc.exe`
  - 可选 GUI 启动器（适合不熟悉命令行的用户）

---

## 📌 SCP 会测量什么

### 函数级指标

| 指标 | 含义 | 计算方式（AST） |
|---|---|---|
| **CC**（圈复杂度） | 分支/路径复杂度，值越高越易出错 | 统计决策节点（`if/for/while/try/except/with/...`）+ 逻辑运算 |
| **LEN**（长度） | 函数 LOC，越长越难维护 | `end_lineno - lineno + 1` |
| **NEST**（最大嵌套深度） | 控制结构嵌套层级 | 对 `If/For/While/Try/With/...` 做 DFS |

### 文件级指标

| 指标 | 含义 |
|---|---|
| **COMMENT_RATIO** | 注释行比例 |
| **DOCSTRING_COV** | 模块/类/函数 Docstring 覆盖率 |
| **LONG_LINE_RATIO** | 超过 79 字符行比例（PEP8） |
| **NAMING_ISSUE_RATIO** | 命名不规范比例（snake_case / CapWords） |
| **UNUSED_IMPORTS** | 未被引用的导入（潜在语义风险） |

---

## 🧠 风险等级与 Smells

SCP 会将多指标映射为**风险等级**并生成 “smells”：

- **高风险**
  - `CC ≥ 10`  
  - `LEN ≥ 60`
  - `NEST ≥ 5`

- **中风险**
  - `CC ≥ 7`
  - `LEN ≥ 40`
  - `NEST ≥ 3`
  - Docstring/注释不足、超长行、命名问题、未使用导入等

- **低风险**
  - 其余情况

Smells 会在 CLI 输出和 HTML 报告中展示，便于快速定位问题。

---

## 🚀 快速开始

### 1）安装依赖（Poetry）

```bash
poetry install
```

### 2）运行分析

```bash
poetry run cyclocalc <项目或文件路径> -t 5 --plots --html
```

示例：

```bash
poetry run cyclocalc cyclocalc/ -t 5 --plots --html --json output/result.json
```

---

## 🖥️ 命令行参数（CLI）

```bash
cyclocalc [PATHS...] [OPTIONS]
```

| 参数 | 说明 |
|---|---|
| `-t, --threshold` | 只展示 CC ≥ threshold 的函数 |
| `--plots` | 生成图表（CC/LEN 分布 + 热力图） |
| `--charts-dir` | 图表输出目录（默认 `output/charts`） |
| `--html` | 生成交互式 HTML 报告 |
| `--html-path` | HTML 输出路径（默认 `output/report.html`） |
| `--json` | 导出 JSON 结构化结果 |
| `--ignore` | 忽略包含某子串的文件/目录（可重复） |
| `--top` | HTML 中展示 Top N 高风险函数 |
| `-o, --output` | 将 CLI 文本输出保存到文件 |

---

## 📊 输出内容

当同时使用 `--plots --html --json` 时，会生成：

```
output/
 ├─ charts/
 │   ├─ cc_distribution.png
 │   ├─ len_distribution.png
 │   └─ file_heatmap.png
 ├─ report.html
 └─ result.json
```

### 报告截图（示例）

- **CC 分布**

  ![cc](output/charts/cc_distribution.png)

- **LEN 分布**

  ![len](output/charts/len_distribution.png)

- **文件风险热力图**

  ![heatmap](output/charts/file_heatmap.png)

---

## 🖥️ Windows 可执行程序（exe）

Windows 用户如果不想安装 Python 环境，可在 **GitHub Releases** 页面下载可执行包。

发布包包含：

```
CycloCalc_release/
  cyclocalc.exe        # 命令行版
  CycloCalc_GUI.exe    # 可选 GUI 启动器
```

### 使用 cyclocalc.exe（命令行）

```bat
cyclocalc.exe <PATHS...> -t 10 --plots --html --json report.json
```

### 使用 CycloCalc_GUI.exe（图形界面）

双击 `CycloCalc_GUI.exe`，选择要分析的路径与参数，点击 **Run** 即可。
请确保 `CycloCalc_GUI.exe` 与 `cyclocalc.exe` **放在同一目录下**。

---

## 🧩 项目结构

```
cyclocalc/
 ├─ analyzer/
 │   └─ metrics.py            # AST 指标提取
 ├─ report/
 │   ├─ visualizer.py         # 图表/热力图（matplotlib）
 │   └─ report_generator.py   # HTML 生成 + smells + 源码预览
 ├─ cli.py                    # Typer CLI 入口
 └─ __init__.py
run_cli.py                    # 打包/CLI 执行入口包装
packaging/                    # 可选：GUI 与打包辅助脚本
```

---

## 🔍 为什么用 Python（以及为什么做 SCP）

本项目展示了 Python 在**静态分析与工程工具链**上的优势：

- `ast`：类编译前端的语法树解析  
- `dataclasses`：指标建模与结构化数据  
- `typer`：现代化 CLI 工程  
- `matplotlib`：科学可视化  
- 内置 `json/html/pathlib`：实用的报告与数据输出

SCP 形成完整流程：

**analyze → evaluate → visualize → report → locate risk**

---

## 🛠️ 开发与测试

本地运行：

```bash
poetry run cyclocalc cyclocalc/ -t 5
```

运行测试：

```bash
poetry run pytest
```

### 打包说明（开发者）

打包命令行 exe：

```bat
poetry run pyinstaller -F -n cyclocalc --hidden-import typer run_cli.py
```

打包 GUI exe：

```bat
poetry run pyinstaller -F -w -n CycloCalc_GUI packaging/gui_cyclocalc.py
```

---

## 🧭 Roadmap（可选）

- 更多语义 smells（如 broad except、可变默认参数等）
- 趋势对比（`--compare old.json new.json`）
- HTML 中可交互排序/筛选

---

## 🙏 致谢

- 基础脚手架来自 **CycloCalc**（Typer CLI + CC analyzer）
- 扩展为 SCP：增加多指标 Profiling、可视化与交互式报告

---

## 📄 License

GPL-2.0-only
