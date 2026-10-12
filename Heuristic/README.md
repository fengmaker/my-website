# 启发式与调度学习工作区

JSSP 正文和配图已统一迁入[网站专题](../docs/运筹优化/调度与生产/JSSP/index.md)。以后直接编辑 `docs/` 中的章节，本站导航位于“运筹优化 → 03 · 经典优化问题 → 调度与生产优化 → JSSP 学习笔记”。各节仍待 review。

本目录保留学习计划、参考资源和可以复算笔记例子的工具：

```text
Heuristic/
├── README.md
└── fjsp_learning/
    ├── AGENTS.md
    ├── plans/              # FJSP 学习路线
    ├── references/         # 参考资源及核验范围
    └── jssp/
        ├── requirements.txt
        ├── scripts/        # 绘图、解码、数值与 Markdown 检查
        └── checks/         # 可复算的 JSON 记录
```

## 阅读入口

- [JSSP 专题目录与 14 节笔记](../docs/运筹优化/调度与生产/JSSP/index.md)
- [FJSP 五周学习计划](fjsp_learning/plans/FJSP学习路线计划书.md)
- [FJSP 参考资源核验](fjsp_learning/references/resources_verified.md)
- [笔记写作准则](../docs/运筹优化/调度与生产/JSSP/笔记写作准则.md)
- [第 7–11 节验收记录](../docs/运筹优化/调度与生产/JSSP/验收记录.md)
- [全套审校记录](../docs/运筹优化/调度与生产/JSSP/assets/01_14_review.md)
- [第 12–14 节验收记录](../docs/运筹优化/调度与生产/JSSP/assets/12_14_validation.md)

## 复算与绘图

在仓库根目录安装工具依赖，然后运行所需脚本：

```text
python -m pip install -r Heuristic/fjsp_learning/jssp/requirements.txt
python Heuristic/fjsp_learning/jssp/scripts/07_09_build_figures.py
python Heuristic/fjsp_learning/jssp/scripts/07_11_check_notes.py
python Heuristic/fjsp_learning/jssp/scripts/12_14_build_figures.py
python Heuristic/fjsp_learning/jssp/scripts/12_14_check_notes.py
```

`02` 至 `06` 的绘图脚本也位于 `scripts/`。脚本从自身位置定位仓库，可在其他工作目录调用；PNG、SVG 输出至网站专题的 `assets/`，JSON 输出至 `checks/`。第 1 节甘特图保留原始 PNG、SVG。

`07_11_check_notes.py` 和 `12_14_check_notes.py` 另外在系统临时目录生成对应章节的 CommonMark + MathJax HTML 预览；MathJax 从 CDN 加载，需要网络。源码和数值检查的范围见验收记录。

## 原路径对应关系

| 原位置 | 新位置 |
| --- | --- |
| `fjsp_learning/jssp_notes/01_…md` 至 `14_…md` | `docs/运筹优化/调度与生产/JSSP/` |
| `fjsp_learning/jssp_notes/README.md` | 网站专题 `index.md` |
| `fjsp_learning/jssp_notes/assets/*.png`、`*.svg`、`*.csv` | 网站专题 `assets/` |
| `fjsp_learning/jssp_notes/assets/*.py` | `fjsp_learning/jssp/scripts/` |
| `fjsp_learning/jssp_notes/assets/*.json` | `fjsp_learning/jssp/checks/` |
| `fjsp_learning/jssp_notes/assets/07_11_validation.md` | 网站专题 `验收记录.md` |
| `fjsp_learning/jssp_notes/assets/01_14_review.md`、`12_14_validation.md`、`*_sources_verified.md` | 网站专题 `assets/` |
| `fjsp_learning/笔记写作准则.md` | 网站专题 `笔记写作准则.md` |
| `fjsp_learning/FJSP学习路线计划书.md` | `fjsp_learning/plans/` |
| `fjsp_learning/resources_verified.md` | `fjsp_learning/references/` |
