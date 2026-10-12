# JSSP 全套笔记审校记录

日期：2026-10-12。范围：第 01–14 节及目录。各节修改后仍待用户 review；本记录不代表用户已认可内容。

本轮检查概念与算法前提、符号和公式、手算与伪代码、章节衔接及行文。现有手算的核心数值均通过复核；修改重点是补清适用条件、消除记号混淆、完善算法约定，并压缩重复说明。

## 逐章修改

| 节次 | 审阅结论与修改 |
|---|---|
| 01 | 区分开始时间变量与同机排序决策；补全 makespan、FJSP 的首次解释，精简表述。 |
| 02 | 析取图、完整/相邻机器弧及有环反例核算一致；将交付说明移入本记录。 |
| 03 | 明确固定队列最早排程具有半主动性；用第 5 节承接主动、无延迟排程，避免混用。 |
| 04 | 将关键路径上相邻工序“无等待”的论证明确放在最早排程下；完善关键工序、关键弧与紧弧的解释。 |
| 05 | 压缩优先级规则与生成框架的重复说明、易错点与速记卡；保留完整构造、GT 冲突集与等待反例。 |
| 06 | 核对移动、判环、全部邻居表及局部最优定义；补充本节目标，保留正确的主体推导。 |
| 07 | 核实 N5 长度为 2 的首尾块保留唯一交换；补充单块或全为单工序块时的下界停止理由。 |
| 08 | SA 接受概率、对称提议、current/best、初温与降温解释正确；改用中文优先的小节标题。 |
| 09 | 用中文先解释禁忌期限、特赦与可选移动；补齐伪代码的可选时间上限及预算行为。 |
| 10 | 已固定机器集合统一记为 $\mathcal F$；区分首次排序与重优化用图，集中解释扩展下界和全局下界的范围。 |
| 11 | 保留完整 B&B、Big-M 与 CP 建模；精简重复提醒，明确 `OPTIMAL` 可能来自配置的 gap 容差。 |
| 12 | 补齐优秀解集合中距离、质量并列时的确定规则；保留 Big Valley 的经验性质及 PR 的可行性、预算条件。 |
| 13 | 核对实例来源、参考界、指标和统计；把人工示意数据的说明写得更直接。 |
| 14 | 核对 FJSP 决策、OS/MS、下界与区间建模；精简重复的核验说明，保留最优值 7 的手算证明。 |

目录合并了重复的进度表与内容表，并给出四段阅读顺序。各节统一为“本轮审校完成，待用户 review”；章节末尾统一链接本记录，原有分批验收记录作为历史材料保留。

## 实际核算

本轮调用既有脚本的核算函数，并运行两份集中检查脚本；没有重建配图。

| 范围 | 复算结果 |
|---|---|
| 01–04：图与时间 | 原排程 $C_{\max}=11$；有环反例不可行；拓扑递推、全部路径、head/tail、总/自由松弛量及多关键路径变体一致。 |
| 05：构造 | 追加式 SPT/LPT/MWKR 为 15/12/11；GT 为 15/13/11；并列变体、空隙左移与无延迟反例 22/14 一致。 |
| 06：局部搜索 | 216 组队列中 64 组可行，最小值 11，恰有两组队列达到；384 个相邻移动的可达性判据与判环一致；平台路径为 12→12→11。 |
| 07–09：搜索机制 | 检查全部 88 条关键路径上的 179 个 N5 候选；SA 概率、温度与 current/best 轨迹、TS 三轮候选及到期编号均一致。 |
| 10–11：分解与界 | 初始单机最优值为 11/8/9；SB 各轮与重优化一致；全局 LB=UB=11，安全时域 $H=22$，示例排程满足 Big-M 约束。 |
| 12–13：重连与统计 | PR 距离 4→3→2→1→0，目标值 12→12→11→13→11；两组示意均值为 11.8/11.2，样本标准差均约 0.4472。 |
| 14：FJSP | 8 种分配、60 组队列中 26 组可行，最优值 7；两种 OS 解码为 8/7，最快机器/分流反例为 6/4，入门全局下界为 5。 |

对应程序：第 2–6 节的 `*_build_figures.py`，以及 [07–09 核算](https://github.com/fengmaker/my-website/blob/main/Heuristic/fjsp_learning/jssp/scripts/07_09_build_figures.py)、[07–11 检查](https://github.com/fengmaker/my-website/blob/main/Heuristic/fjsp_learning/jssp/scripts/07_11_check_notes.py)、[12–14 核算](https://github.com/fengmaker/my-website/blob/main/Heuristic/fjsp_learning/jssp/scripts/12_14_build_figures.py)、[12–14 检查](https://github.com/fengmaker/my-website/blob/main/Heuristic/fjsp_learning/jssp/scripts/12_14_check_notes.py)。最后一份检查脚本的状态检查已调整为识别“待用户 review”，避免将正常的版本更新误判为失败。

## 来源与格式

- 排程分类与 GT 性质复核了 [Giffler–Thompson 原论文摘要](https://pubsonline.informs.org/doi/10.1287/opre.8.4.487)及 [Artigues 等人的研究稿](https://arxiv.org/pdf/cs/0606043)。后者讨论含换型时间的扩展，笔记只采用与无换型基础模型对应的定义和性质。
- N5 首尾块及长度为 2 的规则，复核了 [Jain 等分析稿的第 3.2 节](https://www.researchgate.net/publication/220403549_New_and_Stronger_Job-Shop_Neighbourhoods_A_Focus_on_the_Method_of_Nowicki_and_Smutnicki_1996)。它对 Nowicki–Smutnicki 算法作逐项分析；正文已区分原算法归属与这一具体规则出处。
- SB 的逐机选择与重优化流程只按 [Adams 等原论文的出版页与摘要](https://pubsonline.informs.org/doi/abs/10.1287/mnsc.34.3.391)核对；未取得该文全文。第 10 节的 head/tail、松弛界与例题由正文定义的图模型独立推导和枚举。
- 数据格式与实例说明对照 [OR-Library](https://people.brunel.ac.uk/~mastjjb/jeb/orlib/jobshopinfo.html)；区间模型与状态对照 [OR-Tools 官方教程](https://developers.google.com/optimization/scheduling/job_shop)和 [gap 参数定义](https://or-tools.github.io/docs/javadoc/com/google/ortools/sat/SatParameters.html)。第 12、14 节其余历史来源的阅读边界沿用 [第 12 节来源记录](12_sources_verified.md)、[第 14 节来源记录](14_sources_verified.md)。

全部 14 节及专题目录 通过 CommonMark 加粗、表格、数学分隔符、TeX 花括号、代码围栏与本地相对链接检查；每节保留目标、自检题、答案和速记卡。用现有解析工具生成了全套临时 HTML 预览。主代理另查看了第 1 节甘特图、第 4 节 head/tail 图、第 7 节关键块图和第 14 节 FJSP 对照图，数据、下标与正文一致。

未覆盖：当前浏览器工具未发现可用浏览器，因此没有完成本轮 MathJax 浏览器渲染或用户 IDE 预览的视觉验收。源码解析与 PNG 抽查不等于完整渲染验收。本轮也未运行 MILP、CP-SAT 或公开实例性能实验；第 13 节仍是人工示意统计。

## 网站目录适配

网站版正文与图表位于 `docs/运筹优化/调度与生产/JSSP/`，绘图与校验脚本位于 `Heuristic/fjsp_learning/jssp/scripts/`，JSON 核算记录位于 `Heuristic/fjsp_learning/jssp/checks/`。上面的审校结论与视觉检查范围沿用原始记录；迁移不代表各节已通过用户 review。
