---
tags:
  - JSP
  - 学习路线
---

# JSSP 学习笔记

这套笔记用一个贯穿的 3×3 实例，从手算排程讲到图模型、搜索算法、最优性证明与可复现实验，最后衔接 FJSP。

共 14 节，已完成本轮内容与行文审校（2026-10-12），**各节仍待用户 review**。审校发现、修改和检查范围见 [本轮审校记录](assets/01_14_review.md)。

已有的 [JSP / FJSP 建模笔记](../JSP.md)保留三种 MIP 模型及柔性扩展，作为本专题的对照；工具说明见 [Heuristic 工作区](https://github.com/fengmaker/my-website/blob/main/Heuristic/README.md)。

## 阅读路线

目录按理解顺序组织，不表示后一种算法取代前一种。精确方法、分解方法和元启发式长期并行发展。

| 节次 | 主题 | 要回答的问题 |
|---|---|---|
| 01 | [问题定义与手算排程](01_JSSP的问题定义与手算排程.md) | 什么是合法排程？要决定什么？ |
| 02 | [机器顺序与析取图](02_机器顺序与析取图.md) | 怎样把资源冲突变成边？为什么环意味着不可行？ |
| 03 | [拓扑排序、最长路与 Decoder](03_拓扑排序_最长路与Decoder.md) | 给定机器顺序，怎样计算最早排程？ |
| 04 | [关键路径、head/tail、松弛量与关键块](04_关键路径_head_tail_松弛量与关键块.md) | 哪些约束链限制了完工时间？ |
| 05 | [构造启发式：SPT、LPT、MWKR](05_构造启发式_SPT_LPT_MWKR.md) | 怎样从空排程构造可行初始解？ |
| 06 | [局部搜索：移动与可行性](06_局部搜索_移动与可行性.md) | 怎样改进队列、避免环，并识别局部最优？ |
| 07 | [关键块邻域与 N5](07_关键块邻域与N5.md) | 怎样利用关键结构减少候选？会失去什么？ |
| 08 | [模拟退火（SA）](08_模拟退火_SA.md) | 为什么接受较差解？怎样管理温度与最好解？ |
| 09 | [禁忌搜索（TS）](09_禁忌搜索_TS.md) | 怎样用记忆、期限与特赦减少短期回退？ |
| 10 | [Shifting Bottleneck 与单机子问题](10_Shifting_Bottleneck与单机子问题.md) | 怎样逐台识别瓶颈、排序与重优化？ |
| 11 | [下界与精确求解：B&B、MILP、CP](11_下界与精确求解_BB_MILP_CP.md) | 怎样给出有效下界，并证明最优？ |
| 12 | [优秀解集合、Big Valley 与 Path Relinking](12_优秀解集合_Big_Valley与Path_Relinking.md) | 怎样利用多个好解的质量与结构差异？ |
| 13 | [标准数据集与可复现实验](13_标准数据集与可复现实验.md) | 怎样核对实例、参考值、预算与统计结果？ |
| 14 | [发展脉络回顾与 FJSP 扩展](14_发展脉络回顾与FJSP扩展.md) | FJSP 增加了什么？哪些 JSSP 方法可以迁移？ |

建议分四段阅读：01–04 建立模型与图的基础；05–09 学构造与搜索；10–13 学分解、证明与实验；14 回顾并转向 FJSP。每节先自己做手算和自检题，再看答案；遇到陌生符号时回查定义。

## 写作与 review

统一记号、公式格式和讲解约定见 [笔记写作准则](笔记写作准则.md)。各节保留必要前提、手算步骤、易错点、自检题与速记卡。

本轮按用户要求批量审校全部 14 节；审校完成不代表用户已认可。后续可以逐节反馈，直接引用小节编号或原句，说明哪里不清楚、过于冗长或需要补充推导。

## 核算与预览

正文与配图维护在本站专题目录，配图位于 `assets/`；绘图与校验脚本位于仓库的 `Heuristic/fjsp_learning/jssp/scripts/`，数值记录位于 `Heuristic/fjsp_learning/jssp/checks/`。第 2–6 节各有对应的 `*_build_figures.py`，可复算图模型、最长路、关键结构、构造轨迹与局部搜索示例。第 7–14 节的集中检查入口如下：

```text
python Heuristic/fjsp_learning/jssp/scripts/07_09_build_figures.py
python Heuristic/fjsp_learning/jssp/scripts/07_11_check_notes.py
python Heuristic/fjsp_learning/jssp/scripts/12_14_build_figures.py
python Heuristic/fjsp_learning/jssp/scripts/12_14_check_notes.py
```

脚本依赖 Python、Matplotlib 与 `markdown-it-py`。绘图脚本会重建 PNG、SVG 和数值记录；检查脚本会核对公式分隔符、加粗与本地链接，并在系统临时目录生成 CommonMark + MathJax HTML 预览。MathJax 需要网络。

此前的分批记录见 [第 7–11 节验收](验收记录.md)、[第 12–14 节验收](assets/12_14_validation.md)；本轮覆盖范围以 [全套审校记录](assets/01_14_review.md) 为准。论文来源的详细阅读范围另见 [第 12 节](assets/12_sources_verified.md)、[第 14 节](assets/14_sources_verified.md)。

数值与 Markdown 源码检查不等于完整视觉验收；用户 IDE 的实际公式渲染仍需在其预览环境中检查。第 13 节的 CSV 是明确标注的教学示意数据，不能用于算法排名；本轮没有运行公开实例性能实验或 MILP、CP-SAT 求解器。
