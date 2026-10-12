# 第14节来源核验：JSSP发展脉络与FJSP扩展

核验日期：2026-10-12

本文件供第14节写作使用。年份指可核对的论文/期刊发表年份；不据此宣称相关方法或问题在该年首次发明。只采用论文出版方、作者机构库和 OR-Tools 官方源码/文档。若出版方页面只开放摘要，下面将结论限制在摘要明确支持的范围。

## 论文主张与边界

| 可写主张 | 一手来源 | 证据范围与表述边界 |
|---|---|---|
| Manne 的 1960 年论文提出将离散线性规划用于典型 JSSP，处理工艺顺序限制与设备互斥约束。 | [INFORMS 出版方论文页](https://pubsonline.informs.org/doi/10.1287/opre.8.2.219)；题录为 *Operations Research* 8(2), 219–223，1960。 | 出版方摘要明确写的是 “discrete linear programming”。该页未提供可读取的公式全文，因此正文宜用“离散线性规划建模方案”，不从摘要外推具体变量、约束写法或其优先权。摘要还列出 Bowman 1959 和 Wagner 1959 的相关方案，其中明确把 Wagner 的工作称为整数线性规划模型，不能把 Manne 1960 写成“JSSP 整数规划的首次发明”。同名的 [Manne 1959 Cowles 讨论稿记录](https://elischolar.library.yale.edu/cowles-discussion-paper-series/296/)也表明相关稿件在期刊发表前已有讨论稿；该机构库页面只核实题录，不据此声称其内容与期刊版完全相同。 |
| Adams、Balas、Zawack 的 1988 年论文描述了 shifting bottleneck procedure：逐台机器建立顺序，每步从未排机器中识别瓶颈；排入新机器后局部重优化已有顺序，核心子问题是单机排程。论文还实现了将该过程用于部分搜索树节点的枚举版本。 | [INFORMS 出版方论文页](https://pubsonline.informs.org/doi/10.1287/mnsc.34.3.391)；*Management Science* 34(3), 391–401，1988。 | 出版方摘要明确支持以上算法轮廓和计算实验结论。全文未在当前页面中开放读取；把它写作“该文描述/发表了该程序”比“1988 年首次发明瓶颈思想”准确。 |
| Nowicki、Smutnicki 的 1996 年论文给出一项快速、易实现的 JSSP 近似算法，基于 taboo search；其特定邻域使用关键路径与工序块概念。 | [INFORMS 出版方论文页](https://pubsonline.informs.org/doi/10.1287/mnsc.42.6.797)；*Management Science* 42(6), 797–813，1996。 | 摘要明确支持算法类型、邻域概念及作者报告的实验结论。可称“1996 年发表的快速 taboo search 算法”；不要将年份写成 tabu search 或 JSSP 邻域搜索的发明年份。性能数字是论文当时的实验报告，不等于当前硬件表现。 |
| Nowicki、Smutnicki 的 2005 年论文报告一项新的 JSSP 近似算法，依据 big valley 现象，使用部分 path relinking 技术和新的邻域性质。 | [Springer 出版方论文页](https://doi.org/10.1007/s10951-005-6364-5)；*Journal of Scheduling* 8, 145–159，2005。 | Springer 摘要支持这项算法的定位与构成；页面标明全文为订阅内容。可写“2005 年发表的高级 tabu search 工作/近似算法”，不要据“advanced”或“new”外推整个 tabu search 方法的发明权。 |
| Brandimarte 的 1993 年论文采用两层 FJSP 方法：routing 层为每道工序分配一台可选机器，形成后续 job-shop scheduling 子问题；两层均用 tabu search，并讨论两层之间的双向信息传递。 | [Springer 出版方论文页](https://link.springer.com/article/10.1007/BF02023073)；*Annals of Operations Research* 41, 157–183，1993 年 9 月。 | 摘要明确描述上述层次分解，并指出层次策略此前已在复杂排程文献中出现。可用作“机器选择/分配与工序排序的代表性两层方法”，不可写成 FJSP、层次分解或机器分配概念的起源。全文页为订阅预览，因此不要补充摘要未说明的具体邻域或实验细节。 |

## 固定机器分配后如何沿用 JSSP 图解码

对经典 FJSP，记工序 $O_{j,k}$ 的可选机器集合为 $A_{j,k}$。固定机器选择（MS）就是对每道工序选定一个 $\mu_{j,k}\in A_{j,k}$，同时确定该选择对应的处理时长 $p_{j,k}(\mu_{j,k})$。这一步消除了“去哪台机器加工”的选择，但通常还没有决定同一台机器上各工序的先后顺序。

若模型采用经典假设——每个 job 的工序链及先后关系固定；每道工序不可抢占；每台机器一次只加工一道工序；处理时长在选定机器后固定；没有未纳入图中的额外资源、换型或时间窗约束——那么固定 MS 后，剩下的正是固定机器路线的 JSSP 子问题。Brandimarte 的摘要将 FJSP 分解为 routing 与由机器分配产生的 job-shop scheduling 子问题；Google 的 [OR-Tools JSSP 官方说明](https://developers.google.com/optimization/scheduling/job_shop)列出工序先后和同机不重叠两类约束，支持这个标准子问题解释。

在该子问题中，以工序为节点，job 工序先后关系形成固定的工艺弧；确定每台机器的工序顺序后，再为同机工序加入有向机器弧。只有机器弧定向后形成 **无环图**，该顺序方案才可能可行。此时按拓扑序对前驱完成时刻取最大值，可得该给定 MS 与机器顺序下的最早开始时间（最长路解码）；对经典 makespan 目标，该解码给出该顺序的最早可行排程。这里的图解码是标准模型结构的推论，非 Brandimarte 摘要逐字陈述的解码实现细节。若存在序列相关换型、共享工人、运输资源、机器日历等额外限制，需把它们建入模型和解码器；未经处理不能直接沿用纯 JSSP 图模型。

## 为什么某一固定 MS 的机器负载不是全局 FJSP 下界

设 $a$ 是一种完整的机器分配，$C^*(a)$ 是固定该分配后的最优 makespan，而 $C^*_{FJSP}=\min_a C^*(a)$ 是允许机器选择时的全局最优值。因为固定 $a$ 限制了可选方案，$C^*(a)\ge C^*_{FJSP}$；因此在该 MS 下算出的完整可行排程是全局问题的 **上界候选**，而不是下界。

对固定 MS，机器负载 $L_m(a)=\sum_{O_{j,k}\mapsto M_m}p_{j,k}(a)$ 满足 $\max_m L_m(a)\le C^*(a)$，所以它是这个固定分配子问题的下界。但它可能高于另一机器分配的全局最优值，故不是全局 FJSP 的普遍下界。例如，唯一工序可选 $M_1$、耗时 100，或 $M_2$、耗时 1；若指定 $M_1$，其负载为 100，而 FJSP 全局最优值为 1。全局下界必须覆盖所有可行机器选择（例如对可行分配求松弛下界的最小值），不能直接拿任意一组固定 MS 的负载当全局下界。

## “JSSP 是 FJSP 特例”的准确条件

在经典 FJSP 定义下，若 **每道工序的可选机器集合都只有一台**，且 job 工序路线、处理时间、不可抢占/机器独占假设和目标函数与所讨论的经典 JSSP 一致，则机器选择变量消失，FJSP 退化为 JSSP。Brandimarte 摘要中的 FJSP 路由层正是从可选机器中为每道工序指定一台；OR-Tools 官方 [JSSP 说明](https://developers.google.com/optimization/scheduling/job_shop)则把经典 job shop 描述为每道任务使用指定机器并遵循 job 内固定顺序。

这个包含关系依赖于具体模型版本。若“FJSP”还允许工序跳过、工艺路线选择、并行加工、可抢占、额外共享资源或其他约束，只能在这些部分与 JSSP 模型一致或被消去后，才称为上述经典 JSSP 特例。仅仅把算法名称从 FJSP 换成 JSSP，或固定部分机器选择，不足以自动满足全部 JSSP 假设。

## OR-Tools 官方 stable 示例结构核验

核验对象为 Google 官方仓库的 [`examples/python/flexible_job_shop_sat.py`](https://github.com/google/or-tools/blob/stable/examples/python/flexible_job_shop_sat.py#L105-L162)，`stable` 分支页面于 2026-10-12 核验；分支名会随官方维护更新，引用时应保留核验日期。

| 源码结构 | 核验结果 |
|---|---|
| 全局工序变量与主区间 | 每道工序有全局 `start`、`duration`、`end` 变量及必选主 interval。job 内 precedence 使用相邻主区间的开始/结束变量（源码 105–121 行）。 |
| 备选区间与 presence | 多机器候选下，为每个 alternative 建立 Boolean `presence`、候选机器上的 optional interval；候选加工时间固定为该备选项给出的时长（122–134 行）。 |
| 全局变量与候选区间同步 | 仅在该候选 presence 为真时，添加主 `start/duration/end` 与候选局部变量相等的条件约束（135–138 行）。因此被选候选的起止时间、时长和主工序一致。 |
| 每道工序恰选一个 alternative | `model.add_exactly_one(l_presences)`（145–146 行）。 |
| 机器资源约束 | 每个候选 interval 按其机器 ID 放入资源 interval 列表（140–143 行）；每台机器的列表长度大于 1 时添加 `model.add_no_overlap(intervals)`（153–157 行）。单一备选工序直接将主 interval 放入对应机器列表，并把其 presence 设为常量 1（147–149 行）。 |
| 目标 | makespan 等于各 job 末工序结束时间的最大值，并被最小化（159–162 行）。 |

这是一个 CP-SAT 建模示例，不代表所有 FJSP 必须使用相同编码。特别地，多备选工序的资源不重叠施加在可选的机器局部 interval 上；全局主 interval 负责工序时间及 job precedence 的同步枢纽。
