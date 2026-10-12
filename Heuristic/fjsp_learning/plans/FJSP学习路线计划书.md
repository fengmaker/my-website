# FJSP 学习路线计划书：5 周集中版

编制日期：2026-10-07<br>
投入：每周 12–15 小时，共约 60–75 小时<br>
范围：标准、静态、确定性、单目标 FJSP；对应原路线的 L0–L2<br>
默认工具：C++ 实现启发式算法；Python 实现 CP-SAT 对照、独立校验和可视化

## 1. 这轮学习要做到什么

这轮的目标是：**从零完成一个可验证、可复现实验的 FJSP 小型求解器，并用标准实例解释自己的算法为什么有效、哪里还不够好。**

完成后，你应该能回答五个问题：

1. 一个 FJSP 解由哪些决策组成？怎样判断它可行？
2. 工序顺序和机器分配怎样共同影响最大完工时间？
3. 为什么“每道工序都选最快机器”仍可能得到很差的排程？
4. 局部搜索和模拟退火分别改善了什么？
5. 相同计算预算下，你的算法比自己的 Greedy 基线好多少，距公开参考解还有多远？

交付物控制在一个小项目内：parser、decoder、独立 validator、Greedy、局部搜索、SA、关键路径分析、CP-SAT 小实例对照、甘特图和一份实验报告。

**本轮完成标准不是追平所有 best known solutions，也不要求做成工业 APS。** 工人约束、AGV、订单动态到达、机器故障、鲁棒优化和多目标优化暂时不排进日程。Tabu Search、LNS/ALNS 放在本轮结束后的选修中。

本计划假设你已能写 C++ 的数组、结构体、排序和随机数，能运行简单 Python 脚本。数学上先会“约束、目标函数、图、最长路”的基本概念即可；不必先完整学习运筹学、MILP 或遗传算法。

## 2. 五周总安排

每周安排四次约 3 小时的学习/实现，再留 0–3 小时读资料、复盘或处理卡点。按阶段验收推进，日历只是建议。

| 周次 | 四次主要工作 | 周末应当拿到的成果 |
|---|---|---|
| 第 1 周 | 概念与手算；parser；validator 与甘特图；尾部追加 decoder | 一个小实例从输入到可行排程、校验、画图的完整流程 |
| 第 2 周 | 空隙插入 decoder；Greedy；CP-SAT 建模；小实例对照与初步局部搜索 | 能解释机器选择与排序的区别，并用另一套模型核对正确性 |
| 第 3 周 | 完成邻域；SA 主循环；温度与重启；固定预算小实验 | 可复现的 Greedy、LS、SA 三条基线和收敛日志 |
| 第 4 周 | 排程图与关键路径；关键工序偏置；接入 MK01–MK10；批量实验脚本 | 能定位排程瓶颈，且完整跑通标准实例集 |
| 第 5 周 | 正式重复实验；统计和画图；分析与报告；整理复现入口 | 一份可信的结果表、改进前后甘特图和项目 README |

如果某阶段卡住，先完成它的最低验收条件，再压缩后面的选修任务。最先压缩“关键路径偏置的复杂实现”和“额外数据集”，保留校验、SA 与实验报告。

## 3. 先固定问题定义

先使用以下简化模型，后续所有程序和参考结果都必须对应相同语义：

- 一个 job 是按顺序加工的工件，包含一条工序链。
- 每道工序有一个非空的可选机器集合；加工时间可以随机器变化。
- 每道工序选且只选一台机器，一次加工完成，不能中断。
- 同一 job 的下一道工序只能在上一道结束后开始。
- 一台机器同一时刻最多加工一道工序。
- 所有 job 在时间 0 可用，机器一直可用；不加入运输、换型、工人或交期约束。
- 目标是最小化最大完工时间：`Cmax = max(所有工序的结束时间)`。

所以一个解至少要同时描述：**在哪台机器上加工，以及何时开始加工。** “只输出一个工序排列”还没有完成排程，必须通过 decoder 生成具体时间。

### 手算练习：贯穿前两周的小实例

这里用 M1、M2 展示，输入文件内部则统一用 0、1 编号。

| 工件 | 工序 | 可选机器与加工时间 |
|---|---|---|
| J1 | O11 | M1：3；M2：5 |
| J1 | O12 | M2：2 |
| J2 | O21 | M1：2；M2：4 |
| J2 | O22 | M1：4；M2：3 |

先自己画两个排程，再核对：

- 排程 A：M1 加工 O11 `[0,3)`、O21 `[3,5)`；M2 加工 O12 `[3,5)`、O22 `[5,8)`。`Cmax=8`。
- 排程 B：M1 加工 O21 `[0,2)`、O11 `[2,5)`；M2 加工 O22 `[2,5)`、O12 `[5,7)`。`Cmax=7`。

两者都可行；它们说明同样的机器分配也可能因排序不同而产生不同结果。先不要把“手算找到的最好结果”叫作已证明最优，阶段 3 再通过 CP-SAT 核对。

另做一个机器分配练习：三个 job 都只有一道工序，可选 M1：2 或 M2：3。全部选最快的 M1 得到 `Cmax=6`；让两个去 M1、一个去 M2 可以得到 `Cmax=4`。这就是最快加工时间与机器负载之间的取舍。

## 4. 每个阶段具体做什么

### 阶段 0：理解 JSSP 和 FJSP，先手算

**安排：第 1 周第一次学习。**

要学的内容：job、operation、machine、precedence、机器冲突、可行解、makespan。JSSP 的机器通常预先给定；FJSP 增加每道工序的机器选择。

要做的事情：

1. 阅读 [OR-Tools 官方 Job Shop 教程](https://developers.google.com/optimization/scheduling/job_shop) 的问题定义、约束说明和示例输出。先看它如何描述问题，再看程序。
2. 手算上面的两个排程，检查每道工序的起止时间。
3. 故意画出一次机器重叠、一次工序顺序违反，写下为什么不合法。
4. 写一页 `notes/model.md`：记录本轮问题假设和自己的术语解释。

验收：给你一张小甘特图，你能指出是否合法、算出 Cmax，并说明 FJSP 相比 JSSP 多了什么决策。

**到这里就开始 FJSP，不必先刷完整 Taillard JSSP 数据集。**

### 阶段 1：读懂数据，先把校验器写出来

**安排：第 1 周第二、三次学习。**

主数据入口：[SchedulingLab/fjsp-instances](https://github.com/SchedulingLab/fjsp-instances)。先读 README 的 Format，再直接打开一个实例，不要同时接入多个文本格式。

该仓库当前规定：第一行是 job 数和机器数；后续每个 job 一行，依次给出工序数、每道工序的可选机器数和 `(machine, processing_time)` 对；**机器编号从 0 开始**。[格式说明](https://github.com/SchedulingLab/fjsp-instances/blob/main/README.md)

本阶段只处理这个约定。其他仓库可能采用 1-based 编号、多一个头部字段或不同格式，之后用单独的适配器转换，不能凭 `.txt` 后缀认为语义一致。

要做的事情：

1. 定义 `Instance -> Jobs -> Operations -> Options(machine, duration)`。为每道工序同时保存 `(job_id, operation_index)` 和全局编号。
2. 写 parser，打印每个 job 的工序数、每道工序的备选项和总工序数；检查机器编号范围、非空备选集合、正加工时间和每行 token 是否恰好用完。
3. 先解析手写 toy，再解析 Kacem 的 `k1.txt`、Fattahi 的 `sfjs01.txt`，最后试 `mk01.txt`。这里的“Kacem 用于调试”是指用途，不代表它的全部实例都非常小。
4. 定义统一输出：每条记录至少包含 `job, operation, machine, start, end`。
5. 用另一条代码路径写 validator，直接读取实例和输出排程，检查下面六项。
6. 用 Python 画最简单的甘特图：横轴时间、纵轴机器、颜色区分 job；图用于观察，合法性由 validator 判断。

validator 必须检查：工序恰好出现一次；所选机器合法；`end-start` 等于该机器的加工时间；`start>=0`；job 前后工序不重叠且顺序正确；同一机器的区间不重叠。使用半开区间 `[start,end)`，允许一道结束后另一道在同一时刻开始。Cmax 从输出重新计算，不能直接相信求解器声称的分数。

验收：parser 的统计与手查一致；validator 接受正确 toy 排程，并能拒绝遗漏工序、非法机器、错误时长、机器冲突、前后顺序违反五种故意构造的坏排程。

### 阶段 2：写 OS/MS 编码、decoder 和 Greedy

**安排：第 1 周第四次学习及第 2 周前两次学习。**

先使用一套容易保持可行性的表达：

- **MS（机器选择）**：按固定的全局工序编号，为每道工序选一个合法机器。
- **OS（工序优先序）**：保存 job 编号；一个 job 有几道工序，就出现几次。第 k 次出现解释为该 job 的第 k 道工序。

toy 的 `OS=[J2,J1,J2,J1]` 依次表示 O21、O11、O22、O12。只要 job 出现次数正确，遍历时就不会把 O12 当作 J1 的第一道工序。注意：OS 改变后，位置与具体工序的对应关系也要重新计算。

先写尾部追加 decoder：遍历 OS，为当前工序取 MS 指定的机器，计算 `start=max(job_ready[j], machine_ready[m])`，再更新两者。这一版直观、容易手算，用于建立可靠基线。

随后实现空隙插入 decoder：维护每台机器按时间排序的已占用区间，在满足前序完成时间的条件下，找到能容纳当前工序的最早空隙；找不到就追加到末尾。插入版需要检查整段加工时间是否放得下，不能只找一个空的开始时刻。

资源怎么用：重新看 [Job Shop 教程中的排程输出](https://developers.google.com/optimization/scheduling/job_shop)，把“变量和约束”与你的具体排程对应起来。官方 [flexible_job_shop_sat.py](https://github.com/google/or-tools/blob/stable/examples/python/flexible_job_shop_sat.py) 可用于理解“备选机器和工序”的表示；它是 CP 建模示例，本阶段的 OS/MS decoder 由你自己实现。

要做的事情：

1. 用手算 toy 逐行核对尾部追加版；再构造一个“中间有空隙”的实例验证插入版。
2. 做一个随机合法 OS/MS 生成器，用 validator 检查至少 1000 个随机解。
3. 实现 Greedy A：就绪工序按最短可选加工时间排序，机器选加工时间最短者。这里“就绪”指该 job 的前序工序已经排定，可以安排下一道；候选工序的实际可开始时间仍可能不同。
4. 实现 Greedy B：在就绪工序及其机器选项中，选择预计结束时间最早的 `(工序,机器)`，安排后更新可用工序。最早结束时间的计算要与当前 decoder 的空隙处理保持一致。
5. 加一个随机初始解作为参照。固定 tie-break，例如先比结束时间，再比工序和机器编号。
6. 输出 makespan、可行性、每台机器的加工负载和空闲情况。

验收：每种方法都输出可行排程；你能解释 toy 的分数；在不同实例上比较两种 Greedy，接受它们可能各有胜负。更换 decoder 后重新跑基线，后续实验尽量固定同一 decoder。

### 阶段 3：用 CP-SAT 做小实例的独立对照

**安排：第 2 周第三、四次学习。**

资源只用两份：

- [Python 安装说明](https://developers.google.com/optimization/install/python)：建立虚拟环境并安装 OR-Tools，记录实际安装版本。
- [官方 Flexible Job Shop 示例](https://github.com/google/or-tools/blob/stable/examples/python/flexible_job_shop_sat.py)：重点看备选项的 presence、optional interval、选项唯一性、机器 no-overlap、工序先后约束和 makespan 目标。

你需要理解的建模对应关系：每道工序的机器选项对应可选区间；选中恰好一个选项；每台机器上的被选区间互不重叠；后一工序开始不早于前一工序结束；最小化所有 job 的最终结束时间。官方示例就是学习这些对应关系的入口。

要做的事情：

1. 先运行官方示例，再将输入替换成自己的统一实例表示。官方示例的候选项顺序是 `(processing_time, machine_id)`，与本项目的 `(machine, duration)` 不同，适配时显式转换，别直接照搬二元组。
2. 导出与 C++ 相同格式的排程，经过同一个独立 validator。
3. 求解 toy 和 5–10 个自己生成的微型实例，起步规模控制在 2–4 个 job、2–3 台机器、每个 job 1–3 道工序。
4. 每个实例设置一个小时间上限，例如 30 秒；记录 `status`、目标值、`best_objective_bound`、耗时和版本。
5. 对已返回 OPTIMAL 的实例，确认启发式结果不会小于已证明最优值；出现这种情况就查语义、输入和校验器。启发式比最优值差是正常现象。

**FEASIBLE 表示找到可行解，不能据此宣布最优；UNKNOWN 也不能当作不可行。** 只在 OPTIMAL 或 FEASIBLE 时读取解。[官方状态说明](https://developers.google.com/optimization/cp/cp_solver)

验收：toy 和至少几个微型实例得到已证明最优的参考值；两条独立建模路径的输出均通过校验。对限时仍未证明最优的实例保留状态，不要求所有实例都闭合。

到这里，你已有一套“小实例正确性参考”。本轮不需要同时学 Gurobi、Cplex 和 MiniZinc。

### 阶段 4：三种邻域与基本局部搜索

**安排：第 2 周末开始，第 3 周第一次学习完成。**

先实现三个邻域，不急着引入复杂的增量评分：

| 邻域 | 修改什么 | 应观察什么 |
|---|---|---|
| MS-change | 为一道工序换另一个合法机器 | 是否缓解瓶颈，是否牺牲了加工时间 |
| OS-swap | 交换 OS 中两个不同 job 的位置 | 是否改变了机器上形成的加工顺序 |
| OS-insert | 移出一个 job 符号，再插到另一位置 | 是否让等待中的工序更早获得资源 |

OS 操作必须保持每个 job 的出现次数。对当前只有一台可选机器的工序跳过 MS-change；对无法产生变化的操作重新采样。每次移动后都重新解码，不能直接以“更早出现在 OS 中”判断分数一定更好。

要做的事情：从 Greedy 初始化；用 first-improvement 或随机抽样接受严格改善；停止于规定预算或一段时间无改善；加上多起点版本，避免把单次很快停止的 LS 与持续搜索的 SA 放在不同预算下比较。

资源怎么用：主要复用前面的模型和自己的甘特图，不额外开一门算法课。如果要看研究入口，可以浏览 [Brandimarte 1993 原始论文页面](https://doi.org/10.1007/BF02023073) 的摘要，了解机器选择与排序为什么需要共同搜索；本阶段不依赖付费全文。

验收：一次局部搜索的当前分数单调不增；记录每种移动的尝试、改善次数和耗时；所有最终结果可行；你能举出一次有效的 machine move 和一次有效的 sequence move。

### 阶段 5：实现 SA，并认真做一次参数实验

**安排：第 3 周第二至第四次学习。**

以 LS 的三个邻域为基础。设 `delta = candidate_Cmax - current_Cmax`：改善或持平就接受；变差时按 `exp(-delta/T)` 的概率接受。分别维护 current 和 best，始终返回 best。

要做的事情：

1. 实现温度、降温、随机种子、截止时间和 best-so-far 日志。
2. 先用简单几何降温。按预计候选数设置温度步数；实际停止仍由时间预算控制，避免不同实例因速度不同而完全走不到降温后期。
3. 对一批随机邻居采样正的 delta，以约 80% 的初始接受率做起点：`T0=-mean(positive_delta)/log(0.8)`。它只是调参起点；没有正 delta 时使用明确的备用值。
4. 在开发实例上比较两种初温/降温设置，不进行无上限参数搜索。
5. 比较“只改 MS”“只改 OS”“混合三种邻域”。根据日志调节混合概率，先使用均匀或简单固定权重。
6. 可选加入一次停滞重启或再加热；先保证基本 SA 正确，再加策略。

阅读资源：公式与本阶段任务已足够开工。需要背景时，选读 [Kirkpatrick、Gelatt、Vecchi 的 SA 原始论文页面](https://doi.org/10.1126/science.220.4598.671)，无需把论文全文精读设为前置条件。

验收：相同种子和固定候选预算下结果可复现；按墙钟时间截止时允许细微运行差异，必须记录预算与实际耗时；best 分数始终不变差；至少保存一条“时间—最好 Cmax”的收敛曲线。若 SA 没有优于 LS，先排查接受概率、温度尺度和搜索速度，再解释实验结果。

### 阶段 6：看懂关键路径，尝试有方向的移动

**安排：第 4 周前两次学习。**

先把概念分清：机器忙得久是负载信息；**关键路径是固定机器分配和机器顺序后，约束链对最早完工时间的限制**。不能直接把加工时间最长的机器当作关键路径。

要做的事情：

1. 将工序作为节点。加入 job 的前后边，以及每台机器上相邻工序的顺序边。
2. 对图做拓扑排序。正确可行排程所诱导的顺序图应无环。
3. 按实际机器上的加工时间计算最早开始/结束，以及到终点的最长剩余路径；找出零松弛工序，并回溯一条关键路径。关键路径可能不止一条。
4. 将固定机器顺序按最早可行时间重新排程，再核对图的最长路径长度与 Cmax。一般有意留空的排程可能比图的最早排程更长，不能不加条件就断言二者相等。
5. 在甘特图里突出关键工序，解释哪些等待关系决定了末尾结束时间。
6. 给 SA 加一个简单偏置：更常选择关键工序换机，或选择其在当前 OS 中的对应位置参与排序移动，同时保留一部分随机移动。

资源：本阶段主要阅读自己的排程图与前面的工序/机器约束。若准备继续学 Tabu，再读 Brandimarte 论文的机器选择与排序思路；“经典 JSSP 的某种关键块邻域”不能未经检查直接当作 FJSP 的完整邻域。

验收：toy 的图计算与时间计算一致；能用一张图解释一个较差解的瓶颈；有“普通 SA / 关键工序偏置 SA”的同预算对照。**偏置方法没有稳定改善也可以通过验收，只要实现正确、对照清楚。**

如果这一步花费太多时间，只完成关键路径分析和图示，保留普通 SA 进入正式实验。直接操作机器顺序、维护无环性和增量最长路可以以后再做。

### 阶段 7：跑标准数据，产出可信报告

**安排：第 4 周后两次学习与第 5 周。**

数据先控制在三层：

| 数据 | 本轮选取 | 用途 |
|---|---|---|
| 自制 toy / 微型随机数据 | 贯穿全程 | 手算、校验、CP-SAT 对照 |
| Kacem / Fattahi | 先 k1 和 sfjs01–sfjs05；需要时增加 | 格式与算法调试；不是正式调参无限扩展的目标 |
| Brandimarte | MK01–MK10 | 本轮正式结果集 |

从 [SchedulingLab Brandimarte 目录](https://github.com/SchedulingLab/fjsp-instances/tree/main/brandimarte) 下载 `mk01.txt` 至 `mk10.txt`。本轮使用经典十个；库中另有 MK11–MK15，FJSPLib 将后五个追溯到 Behnke–Geiger 的补充材料，不将“仓库有 15 个文件”写成“1993 原始集有 15 个”。[FJSPLib 实例说明](https://scheduleopt.github.io/benchmarks/fjsplib/)

参考结果从 [FJSPLib](https://scheduleopt.github.io/benchmarks/fjsplib/) 与其 [bks.json](https://github.com/ScheduleOpt/benchmarks/blob/main/flexible-jobshop/solutions/bks.json) 读取。那里区分下界、上界和问题状态；**公开 best known upper bound 不能一律当作已证明最优值。**

先建立两份清单：

- `data/manifest.csv`：来源链接、下载日期/提交、文件哈希、机器编号约定、job/机器/工序数量。
- `experiments/reference.csv`：自己的实例 ID、参考库 ID、LB、UB、来源快照、最优性说明。

不同仓库之间先核对规范化后的工序链、机器选项和时长；机器编号转换后应该逐项一致。不能只凭两个文件都叫 mk01 就比较分数。遇到来源数据差异时，优先让实例和上下界来自同一配套来源，必要时单独适配 FJSPLib JSON。文本 parser 先不扩成“自动猜各种格式”。

正式实验协议建议如下：

1. 用 MK01–MK03 做开发调参；确定设置后冻结参数，MK04–MK10 留作未参与调参的检验。报告可以展示全部十个，但须标明前面三个参与过开发。
2. 比较 Greedy、multi-start LS、SA；关键工序偏置 SA 作为可选第四项。
3. Greedy 若完全确定性，每实例运行一次即可；随机算法每实例用种子 0–9，共 10 次。
4. 随机算法使用每实例每次 1 秒、10 秒两档预算。将初始化和搜索计入，统一排除读取文件与画图；这些边界写进报告。使用同一台电脑、同一编译模式、同样线程数。
5. 记录实际耗时和候选评价次数。搜索前与最终输出运行 validator；调试阶段可以更频繁检查，正式计时避免把不同算法的额外调试开销混入比较。
6. CP-SAT 在本轮主要用于小实例正确性参考。若加入正式性能对比，要另设同预算、固定线程和版本的实验；阶段 3 的 30 秒参考不能直接与 10 秒 SA 宣称公平排名。
7. 不要求每个实例都改善；统计结果应保留失败和持平，不只挑最好看的实例。

指标统一命名：

- `RPD_BKS = 100 * (Cmax - BKS) / BKS`，其中 BKS 使用所保存快照的公开最好上界。
- `Gap_LB = 100 * (Cmax - LB) / LB`，这是本项目约定的相对下界距离，LB 必须正且有效；它不等于已知的真实次优程度。
- FJSPLib 页面自身还有以 UB 为分母的 gap 定义，引用它的原表时保留原定义，不与本项目的 `Gap_LB` 混为同一列。
- 相对自己 Greedy 的改善率：`100 * (Greedy_Cmax - algorithm_Cmax) / Greedy_Cmax`。

RPD 可以为负：先复核实例、合法性和参考快照，再判断是否改善了旧上界。结果小于有效 LB 则应立即排查。聚合跨实例表现时平均各实例的 RPD 或改善率，不直接用不同规模实例的 Cmax 平均值代表总体质量。

如果暂时没有配套的公开 LB，可以先算两个简单下界。令每道工序的最短可选加工时间为 `p_min`，则 `LB_job=max_j(sum_{该job所有工序} p_min)`，`LB_work=ceil(sum_{全部工序} p_min / 机器数)`，取二者最大值。它们通常较弱，但对本轮的整数加工时间模型有效。当前某个 MS 方案的最大机器负载，只是该固定分配下的下界，不能直接称为整个 FJSP 的通用下界。

每实例结果表至少含：算法、预算、最好值、均值、标准差、LB、参考 UB、平均 RPD 和可行率。保留原始逐次日志，别只保存汇总。

验收：MK01–MK10 全部可行；正式随机实验有 10 次重复；结果表可从原始 CSV 再生成；有至少两张甘特图、一张收敛曲线、一张算法对比图，以及一份 3–5 页或等量 Markdown 的分析。

报告需要解释：SA 相比 Greedy/LS 的收益；机器与排序邻域谁更有效；关键工序偏置是否有效；哪些实例还差；下一个要改的具体瓶颈是什么。没有达到 BKS 也能写出合格报告。

## 5. 资源清单：按需要打开，不堆阅读量

| 资源 | 什么时候看 | 本轮只看什么 |
|---|---|---|
| [OR-Tools Job Shop 教程](https://developers.google.com/optimization/scheduling/job_shop) | 第 1 周 | 问题定义、precedence/no-overlap、示例排程 |
| [SchedulingLab 数据和格式](https://github.com/SchedulingLab/fjsp-instances) | 第 1 周 | README Format，toy 与少量实例文件 |
| [OR-Tools Python 安装](https://developers.google.com/optimization/install/python) | 第 2 周 | pip 安装与版本记录 |
| [官方 FJSP CP-SAT 示例](https://github.com/google/or-tools/blob/stable/examples/python/flexible_job_shop_sat.py) | 第 2 周 | 机器选项、optional interval、exactly-one、no-overlap、makespan |
| [CP-SAT 状态说明](https://developers.google.com/optimization/cp/cp_solver) | 第 2 周 | OPTIMAL、FEASIBLE、UNKNOWN 等状态的区别 |
| [FJSPLib](https://scheduleopt.github.io/benchmarks/fjsplib/) | 第 4–5 周 | 实例说明、配套上下界、最优性状态和格式 |
| [Brandimarte 1993](https://doi.org/10.1007/BF02023073) | 完成本轮后选读 | FJSP 机器分配与排序的联合搜索、Tabu 思路 |
| [SA 原始论文](https://doi.org/10.1126/science.220.4598.671) | 第 3 周可选 | 模拟退火的基本动机；不作为开工前置 |

本轮不需要找一套很长的“FJSP 全家桶”视频。先用官方教程理解问题，用数据和程序建立直觉，卡在具体术语时再针对性补课。论文全文不能公开访问时，跳过可选阅读，继续主线任务。

## 6. 最小项目结构

以下是学习项目的目标结构，不要求第一天就建齐；用到哪个模块再创建哪个。

```text
fjsp_solver/
├── data/
│   ├── toy/
│   ├── selected_instances/
│   └── manifest.csv
├── src/
│   ├── instance.hpp
│   ├── schedule.hpp
│   ├── decoder.cpp
│   ├── greedy.cpp
│   ├── local_search.cpp
│   ├── sa.cpp
│   ├── critical_path.cpp
│   └── main.cpp
├── tools/
│   ├── validate.py
│   ├── cpsat_reference.py
│   ├── gantt.py
│   └── run_benchmarks.py
├── experiments/
│   ├── reference.csv
│   ├── runs.csv
│   ├── summary.csv
│   └── report.md
├── notes/model.md
└── README.md
```

时间与 makespan 建议使用 64 位整数。统一所有算法的输入、排程输出和评价方式，避免每实现一种算法就重写一套接口。

期望最终具有这样的命令接口；这是实现目标，不代表当前已有这些程序：

```text
solver --instance <path> --algorithm greedy --output schedule.json
solver --instance <path> --algorithm sa --seed 0 --time-limit 10 --output schedule.json
python tools/validate.py <instance> schedule.json
python tools/gantt.py schedule.json
python tools/run_benchmarks.py <config>
```

`runs.csv` 至少包含 `instance, algorithm, seed, time_budget, elapsed, evaluations, makespan, feasible`；编译参数、CPU、线程数、版本与参数配置写入实验元信息。CP-SAT 额外保留 status 和 best bound。

## 7. 每周检查表

- [ ] 第 1 周：能手算；parser 正确；坏排程会被拒绝；追加 decoder 输出可行解。
- [ ] 第 2 周：插入 decoder 和 Greedy 跑通；CP-SAT 微型对照与独立校验一致；理解返回状态。
- [ ] 第 3 周：三个邻域可用；LS 与 SA 可复现；best 记录正确；有收敛日志。
- [ ] 第 4 周：能解释关键路径；MK01–MK10 全部接入；实例与参考值映射经过核对。
- [ ] 第 5 周：按固定协议重复实验；保存原始结果；报告能解释收益和不足；README 可复现。

每次学习结束花 10 分钟记录：今天实现了什么、哪张图/哪条日志证明它正确、还有什么问题、下次第一件事做什么。

卡点的处理顺序：不合法 → 查 parser/decoder/validator；分数异常好 → 查约束和参考映射；SA 不改善 → 查温度/接受/邻域；算法太慢 → 先测 decoder 的耗时比例，再决定是否做增量优化。

## 8. 本轮之后再决定的内容

完成五周并复盘后，只从下面选一个近期开支：

- **Tabu Search（约 1–2 周）**：适合你希望研究邻域和搜索记忆。学习 tabu 属性、tenure、aspiration，与已完成的 SA 同预算比较。
- **简单 LNS（约 1–2 周）**：适合你发现小移动经常卡住。先破坏少量工序的机器选择或优先序并重建，不急着做完整 ALNS 自适应权重系统。
- **少量 Hurink 实例（约 1 周）**：适合你想研究柔性大小对搜索的影响。先控制规模和数据语义，再比较 MS/OS 邻域。

GECCO 的工人扩展、动态调度、AGV、鲁棒和工业 APS 只保留为后续方向，不设这轮的截止日期或完成义务。当前最有价值的终点是：**一个正确的标准 FJSP 求解器，加一份你能讲清楚的实验报告。**

## 9. 第一天下手顺序

第一天按三小时执行：约 45 分钟读 Job Shop 官方教程的问题定义；约 60 分钟手算 toy 与两种错误排程；约 45 分钟打开 SchedulingLab README 和 `sfjs01.txt`，逐个数字解释含义；最后 30 分钟写 `notes/model.md` 并确定统一数据结构。

当天结束时应有一页模型笔记、一张手算甘特图和一个已读懂的实例文件。第二次学习就开始写 parser。

上面 toy 对应的 SchedulingLab 风格输入如下，可保存为 `data/toy/two_jobs.txt`：

```text
2 2
2 2 0 3 1 5 1 1 2
2 2 0 2 1 4 2 0 4 1 3
```

第二行解释：J1 有 2 道工序；第一道有 2 个选项 `(0,3)`、`(1,5)`；第二道有 1 个选项 `(1,2)`。图中的 M1/M2 分别对应文件中的机器 0/1。
