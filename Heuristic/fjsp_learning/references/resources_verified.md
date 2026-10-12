# FJSP 学习路线参考资源核验

核验日期：2026-10-07。范围按标准静态、单目标、最小化 makespan 的 FJSP 理解。

## 1. OR-Tools 官方 Job Shop 教学

[The Job Shop Problem](https://developers.google.com/optimization/scheduling/job_shop) 可访问。先读页面中的 **Example Problem**、**Variables and constraints**、**Objective** 和 **Program solution**。它逐步说明工件内先后约束、机器互斥、区间变量和 makespan，适合路线开头建立调度模型直觉，或在进入 FJSP 前作为 JSP 对照。

纠正：该教程的问题数据给每道工序指定唯一机器，是普通 JSP；它本身没有工序的备选机器选择。不要将它作为 FJSP optional interval 的实现示例。

## 2. OR-Tools 官方 FJSP CP-SAT 示例

[官方示例源码](https://github.com/google/or-tools/blob/stable/examples/python/flexible_job_shop_sat.py) 可访问，当前 `stable` 分支源码页展示 2025 年版权标记。数据 `jobs` 中每个 operation 的候选项为 `(processing_time, machine_id)`。重点读 `flexible_jobshop()` 里的建模部分：

- `presence` 布尔变量和 `new_optional_interval_var()` 表示某机器上的候选工序区间；`add_exactly_one()` 选择一个备选。
- 每道工序的全局开始/结束变量与被选中的候选区间用条件约束关联；precedence 约束连接同一 job 的连续工序。
- `intervals_per_resources` 按机器收集区间，`add_no_overlap()` 保证机器互斥；makespan 用 `add_max_equality()` 约束为各 job 完工时间的最大值并最小化。
- 求解入口是 `status = solver.solve(model, solution_printer)`；示例只在 `OPTIMAL` 或 `FEASIBLE` 时读取解，并在末尾打印 `response_stats()`。

[官方 CP-SAT 状态说明](https://developers.google.com/optimization/cp/cp_solver#cp-sat-return-values) 区分 `OPTIMAL`（已证明最优）、`FEASIBLE`（有可行解但未证明最优）、`INFEASIBLE`、`MODEL_INVALID` 和 `UNKNOWN`。示例在任一 `OPTIMAL`/`FEASIBLE` 状态都打印 “Optimal objective value”，因此当状态只有 `FEASIBLE` 时，这句输出标签会夸大结论；实验代码应同时报告状态。该文件没有 pin OR-Tools 最低版本或依赖版本，并使用当前 Python 接口的小写方法名；复现实验时应记录实际安装版本和源码 commit，不要从 `stable` 推断固定版本。

适读阶段：CP-SAT 小实例对照。把它当作建模参照，早期先自己实现输入解析、可行性校验和 decoder，再比较输出。

## 3. FJSPLib 基准与上下界

[FJSPLib 页面](https://scheduleopt.github.io/benchmarks/fjsplib/) 和 [ScheduleOpt 源码仓库](https://github.com/ScheduleOpt/benchmarks/tree/main/flexible-jobshop) 均可访问。页面将库分为实例集合、标准化引擎比较和最佳已知上下界档案；标准 FJSP 部分列出 Brandimarte `mk` 15 个、Kacem 4 个、Fattahi 20 个等集合。整个页面还包括机器独立变体和柔性装配 job shop；五周主路线只需关注标准 FJSP。

可下载入口： [FJSPLib JSON instances](https://github.com/ScheduleOpt/benchmarks/tree/main/flexible-jobshop/instances/json)、[BKS 上下界 JSON](https://github.com/ScheduleOpt/benchmarks/blob/main/flexible-jobshop/solutions/bks.json)。页面提供的 text 链接在本次核验时指向不存在的 `instances/text` 路径并返回 404；初学路线优先选 JSON 或下一节的 SchedulingLab `.txt`，不要依赖这个失效链接。

BKS 条目的关键字段是 `instance`、`family`、`status`、`lower_bound`、`upper_bound`，并以 `lb_data` / `ub_data` 保存来源、日期、求解器、耗时、硬件及 `certificate` 信息。`status` 是档案的 `open` / `closed` 标记，不是 CP-SAT 的返回状态；页面将 `open` 解释为尚未证明最优，将 `closed` 解释为已宣称闭合，通常因 LB 与 UB 相等，但条目也可能没有形式化证书。BKS 会更新，因此路线不抄固定数值，实验时按同一实例 ID 从当时的 JSON 读取上下界。

页面的单实例 gap 是 `(UB - LB) / UB`；跨实例比较用 geometric shifted average gap，而不是先对普通 gap 做算术平均。报告时同时给出算法自身的可行解 makespan（作为候选 UB）、对应参考 LB、相对 gap 和实例 ID。若从不同库取实例和界，先确认实例内容完全相同再 join；仅凭相似的 family 名称不能假设同一数据。

## 4. SchedulingLab 实例、数量与文件格式

[SchedulingLab/fjsp-instances README](https://github.com/SchedulingLab/fjsp-instances) 可访问，且列出各集合、格式与原论文引用。仓库同时明确警告数据可能不准确，要求有疑问时回查原论文。具体目录： [Brandimarte](https://github.com/SchedulingLab/fjsp-instances/tree/main/brandimarte)、[Kacem](https://github.com/SchedulingLab/fjsp-instances/tree/main/kacem)、[Fattahi](https://github.com/SchedulingLab/fjsp-instances/tree/main/fattahi)。

当前仓库目录/README 数量是 Brandimarte 15、Kacem 4、Fattahi 20。Brandimarte 文件名确有 `mk01.txt` 至 `mk15.txt`；不过 FJSPLib 的 Brandimarte 表格特别注明 MK11–MK15 来自 Behnke–Geiger (2012) 的补充材料，并未出现在其他 benchmark 仓库中。SchedulingLab 把 15 个文件全部放在 `brandimarte/`，README 将其统称为 Brandimarte 15，同时声明数据可能有误。为避免来源混淆，路线中应称“常用 Brandimarte MK01–MK10；该汇总仓库还收录 MK11–MK15 扩展实例”，不要把“15”说成原论文标准 MK01–MK10 集合的数量。

SchedulingLab 的三类纯文本样例都可访问：[`mk01.txt`](https://raw.githubusercontent.com/SchedulingLab/fjsp-instances/main/brandimarte/mk01.txt)、[`k1.txt`](https://raw.githubusercontent.com/SchedulingLab/fjsp-instances/main/kacem/k1.txt)、[`mfjs01.txt`](https://raw.githubusercontent.com/SchedulingLab/fjsp-instances/main/fattahi/mfjs01.txt)；Fattahi 另有 [`sfjs01.txt`](https://raw.githubusercontent.com/SchedulingLab/fjsp-instances/main/fattahi/sfjs01.txt)。这些文件的头行均为两个整数 `J M`。每个后续 job 行以工序数 `n_ops` 开始；每道工序先给候选机器数，再给若干 `(machine_id, duration)` 对。机器编号从 0 开始。README 描述了相同格式；如需实现核心 parser，可只支持此格式，严格消费每行的 token 并检查工序数、候选数和机器编号范围。

关于“可选第三个头字段”：上述 SchedulingLab `.txt` 样例没有第三字段。FJSPLib 自己的 `fjsp` 格式则定义首行为 `#jobs #machines average_flexibility`，所以若以后导入它，需要在识别具体格式后将第三个数作为元数据处理，而不要把它误当作工件数、机器数或工序数。FJSPLib 的 `fjsp` 说明文字与模板对机器/时长顺序写法不一致：描述处称 machine-duration，模板注释写 duration-machine，示例解释又给出 `(machine, duration)`，其示例机器编号也呈 1-based；同页 `fajsp` / JSON 使用的机器编号是 `0..M-1`。不要把 FJSPLib 的纯文本格式直接套用 SchedulingLab parser。主路线只用 SchedulingLab 文件，边界清楚：`(machine_id, duration)`、0-based、头两字段 `J M`。

适读阶段：parser / validator 阶段用 `mk01.txt` 做首个基准；算法阶段按相同目录扩展到 MK01–MK10；Kacem/Fattahi 只做后续交叉数据检查，不把相似文件名当作同一 BKS 记录。

## 5. Brandimarte 原始论文

[Springer 原文信息与摘要](https://link.springer.com/article/10.1007/BF02023073) 可访问，全文为订阅内容。准确 DOI 是 [10.1007/BF02023073](https://doi.org/10.1007/BF02023073)。摘要描述基于 tabu search 的分层 FJSP 算法：将问题分为 routing 和 job-shop scheduling 两层，两层都使用 tabu search，并通过双向信息流协调；论文报告初步计算实验。适读阶段：了解 OS/MS 分解和 Tabu 选修背景。它是方法论文；复现标准 OS+MS decoder / SA 路线不需要完整实现文中分层算法。

## 6. 两项补充理论资源

- [Pinedo, *Scheduling: Theory, Algorithms, and Systems*, 第六版（Springer）](https://link.springer.com/book/10.1007/978-3-031-05921-6)：出版社目录列出 deterministic preliminaries、job shops 和实践中的通用程序。概念阶段可选读 deterministic preliminaries；全文可能需要机构访问。
- [Kirkpatrick, Gelatt & Vecchi, “Optimization by Simulated Annealing,” *Science*, 1983](https://doi.org/10.1126/science.220.4598.671)：期刊摘要介绍模拟退火与组合优化的联系。适读 SA 阶段，原始论文用于理解接受劣解与温度机制的理论动机；它不是 FJSP 专题论文。

## 7. 远期竞赛入口

[GECCO FJSSP-WU Competition](https://jrc-rodec.github.io/FJSSP-W-Competition/) 页面可访问，仅作为远期入口。页面主题含 worker flexibility 和 uncertainty，超出本路线的标准静态 FJSP 范围；现阶段不需读竞赛细节。
