# VRPTW 求解项目证据核查

## 固定快照

核查仓库：[`fengmaker/vrptw_slover`](https://github.com/fengmaker/vrptw_slover)，`master` 在本次查询中解析为 commit [`9fe59ad51b9533f00bb8efe097143ad0fa5ba8ef`](https://github.com/fengmaker/vrptw_slover/commit/9fe59ad51b9533f00bb8efe097143ad0fa5ba8ef)，提交时间为 2026-10-09 18:12:34 UTC。对应 tree object 是 `3643b04735b9bb938bae24ded4e042c78b05b02c`；本文固定的是前一个 commit SHA，未把 tree SHA 当成提交号。报告、数据、源码链接均指向该快照。

## 问题模型与实际算法

项目求解 Solomon 单仓库、同质车队 VRPTW：每位客户恰好服务一次，每条路线受车辆容量、客户服务开始时间窗和仓库最晚返回时间约束。客户坐标间采用欧氏距离；路径成本为 `round(1000 × hypot(dx, dy))` 的整数 ticks，时间窗和服务时间乘以 1000，需求与容量保留整数。目标按 `(使用车辆数, 总整数距离)` 字典序最小化。模型和标尺可核查于 [`problem.py` 第 33–63 行](https://github.com/fengmaker/vrptw_slover/blob/9fe59ad51b9533f00bb8efe097143ad0fa5ba8ef/src/vrptw/problem.py#L33-L63)、[`evaluate.py` 第 62–103 行](https://github.com/fengmaker/vrptw_slover/blob/9fe59ad51b9533f00bb8efe097143ad0fa5ba8ef/src/vrptw/evaluate.py#L62-L103) 及[四求解器的统一数值协议](https://github.com/fengmaker/vrptw_slover/blob/9fe59ad51b9533f00bb8efe097143ad0fa5ba8ef/benchmarks/four_solver/README.md#L61-L70)。

自研方法应称为 **可行解迭代局部搜索（ILS）**：先按客户截止时间做确定性可行插入，再用 M10 默认混合减车策略；随后在固定车数下执行 ILS。扰动混合移除相关客户与随机客户，再做同车队修复；候选继续做局部改进，最终保留历史最好可行解。[求解流程](https://github.com/fengmaker/vrptw_slover/blob/9fe59ad51b9533f00bb8efe097143ad0fa5ba8ef/src/vrptw/solve.py#L1-L18)、[ILS 扰动与修复](https://github.com/fengmaker/vrptw_slover/blob/9fe59ad51b9533f00bb8efe097143ad0fa5ba8ef/src/vrptw/ils.py#L50-L81)、[ILS 接受与重启逻辑](https://github.com/fengmaker/vrptw_slover/blob/9fe59ad51b9533f00bb8efe097143ad0fa5ba8ef/src/vrptw/ils.py#L135-L180)。四方实验的适配器只覆盖 seed、时间预算和 `search_backend="native"`，其余采用该快照默认配置；默认局部算子为 `relocate`、`swap`、`two_opt`、`two_opt_star`，按 cyclic 次序扫描。[实验适配器](https://github.com/fengmaker/vrptw_slover/blob/9fe59ad51b9533f00bb8efe097143ad0fa5ba8ef/benchmarks/four_solver/ours_backend.py#L10-L34)、[默认算子](https://github.com/fengmaker/vrptw_slover/blob/9fe59ad51b9533f00bb8efe097143ad0fa5ba8ef/src/vrptw/local_search.py#L14-L18)。M12 原生后端还实现了三种段移动，但四方对比协议记录为使用原四算子轮换；因此不应将这组实验描述成七算子全开的结果。[M12 原生迁移边界](https://github.com/fengmaker/vrptw_slover/blob/9fe59ad51b9533f00bb8efe097143ad0fa5ba8ef/benchmarks/M12_REPORT.md#L7-L15)、[四方运行算法设置](https://github.com/fengmaker/vrptw_slover/blob/9fe59ad51b9533f00bb8efe097143ad0fa5ba8ef/benchmarks/four_solver/README.md#L63-L70)。高层构造、减车和修复仍在 Python；原生扩展加速局部搜索候选枚举、筛选和移动应用，每次接受后仍由独立验证器复核。[CLI 与后端说明](https://github.com/fengmaker/vrptw_slover/blob/9fe59ad51b9533f00bb8efe097143ad0fa5ba8ef/README.md#L209-L225)。

## 最新主实验：四求解器对比

`FOUR_SOLVER_REPORT.md` 是较新的四方实验报告，不能与 M12 迁移验收中的固定车数距离实验混为一谈。协议含 56 个 Solomon 100 客户实例：C101–C109、C201–C208；R101–R112、R201–R211；RC101–RC108、RC201–RC208。seed 为 0，每个实例、预算和求解器各运行一次；预算为 0.5 秒和 5 秒，共 `56 × 2 × 4 = 448` 次主实验调用。求解器冷启动、不传初始路线，保留 Solomon 原始车辆上限，共用自研解析器生成的整数距离矩阵，并按车辆数、整数距离优化。搜索预算包括各算法的初始构造；外部建模单独计时，导入和工作进程启动不计时；四个常驻 worker 串行执行，并轮换求解器次序。[报告协议摘要](https://github.com/fengmaker/vrptw_slover/blob/9fe59ad51b9533f00bb8efe097143ad0fa5ba8ef/benchmarks/FOUR_SOLVER_REPORT.md#L3-L7)、[复现说明与完整计时协议](https://github.com/fengmaker/vrptw_slover/blob/9fe59ad51b9533f00bb8efe097143ad0fa5ba8ef/benchmarks/four_solver/README.md#L3-L5)、[协议 manifest](https://github.com/fengmaker/vrptw_slover/blob/9fe59ad51b9533f00bb8efe097143ad0fa5ba8ef/benchmarks/four_solver/archive/manifest.json#L1-L13)、[种子、预算、求解器及代码哈希](https://github.com/fengmaker/vrptw_slover/blob/9fe59ad51b9533f00bb8efe097143ad0fa5ba8ef/benchmarks/four_solver/archive/manifest.json#L72-L86)。

运行环境记录为 AMD Ryzen 7 6800H，8 核、16 逻辑处理器，搜索单线程。自研、OR-Tools 和 Gurobi worker 使用 CPython 3.12.4；PyVRP 使用本地构建的 CPython 3.13.5。版本为 PyVRP 0.13.0a0、OR-Tools 9.15.6755、Gurobi 13.0.0。自研 M12 使用 Windows x64 的 C++17 原生扩展；Gurobi 需要已有有效许可证。[环境与依赖](https://github.com/fengmaker/vrptw_slover/blob/9fe59ad51b9533f00bb8efe097143ad0fa5ba8ef/benchmarks/four_solver/README.md#L37-L59)、[worker 版本与完成时间](https://github.com/fengmaker/vrptw_slover/blob/9fe59ad51b9533f00bb8efe097143ad0fa5ba8ef/benchmarks/four_solver/archive/manifest.json#L238-L276)。OR-Tools 配置为 RoutingModel 插入启发式加 Guided Local Search；Gurobi 是项目自写二下标弧 MILP。PyVRP 用本地 `solve()` ILS 和支配车辆成本，未调用独立 `minimise_fleet()`。[求解器设置及成本合同](https://github.com/fengmaker/vrptw_slover/blob/9fe59ad51b9533f00bb8efe097143ad0fa5ba8ef/benchmarks/four_solver/README.md#L63-L70)。

### 主表结果与 CSV 独立重算

| 预算 | 自研 M12 可行数 / 总车数 | PyVRP 可行数 / 总车数 | M12 较少 / 相同 / 较多车辆 | 同车数距离 gap 样本数 | M12 相对 PyVRP 距离 gap 中位数 / P90 |
| --- | ---: | ---: | ---: | ---: | ---: |
| 0.5 秒 | 56/56 / 454 | 56/56 / 490 | 28 / 24 / 4 | 24 | 7.7841% / 45.4805% |
| 5 秒 | 56/56 / 443 | 56/56 / 490 | 32 / 24 / 0 | 24 | 0.0608% / 4.1299% |

我从固定快照的 [`results/raw_runs.csv`](https://github.com/fengmaker/vrptw_slover/blob/9fe59ad51b9533f00bb8efe097143ad0fa5ba8ef/benchmarks/four_solver/results/raw_runs.csv#L1-L5) 独立读取 448 行，以预算和实例配对 M12 与 PyVRP；车辆统计对全部双方可行的实例计算，距离 gap 仅在车辆数相同时计算，公式为 `(M12 距离 / PyVRP 距离 − 1) × 100%`。采用线性插值 P90 重算，0.5 秒和 5 秒两组车辆总数、车辆差异计数、同车数样本数、中位数与 P90 均与 [`summary.csv`](https://github.com/fengmaker/vrptw_slover/blob/9fe59ad51b9533f00bb8efe097143ad0fa5ba8ef/benchmarks/four_solver/results/summary.csv#L1-L9) 及报告的四舍五入结果吻合。[报告主表与 gap 定义](https://github.com/fengmaker/vrptw_slover/blob/9fe59ad51b9533f00bb8efe097143ad0fa5ba8ef/benchmarks/FOUR_SOLVER_REPORT.md#L9-L22)。5 秒对比 OR-Tools 时，M12 少车 / 同车 / 多车为 8 / 43 / 5，同车数距离 gap 中位数为 1.413%。Gurobi 在 0.5 秒和 5 秒下分别只有 27/56、54/56 例找到可行解，不能把它与完整可行覆盖的总车辆数直接排名。[相对 OR-Tools 与 Gurobi 可行率](https://github.com/fengmaker/vrptw_slover/blob/9fe59ad51b9533f00bb8efe097143ad0fa5ba8ef/benchmarks/FOUR_SOLVER_REPORT.md#L24-L35)。

### 退步、长尾与解释边界

增加预算对 M12 有帮助：从 0.5 秒到 5 秒，11 例少用车辆，39 例在车辆数相同的情况下缩短距离，6 例同车同距；未出现车辆更多或同车距离变长的逐实例配对结果。[预算变化配对表](https://github.com/fengmaker/vrptw_slover/blob/9fe59ad51b9533f00bb8efe097143ad0fa5ba8ef/benchmarks/FOUR_SOLVER_REPORT.md#L37-L44)。不过 5 秒主表中仍有同车数长尾：C103 的主表比较是 M12 10 车、PyVRP 11 车，因此它不属于同车数 gap 样本。报告另有固定车辆上限诊断：将 PyVRP 上限固定为 M12 找到的 10 车、冷启动且不给路线后，C103 的 PyVRP 距离为 828.065，M12 为 1213.077，M12 长 46.495%。这是**不同协议**的路线质量诊断，不能代入 5 秒主表的 0.0608% 中位数。[固定车辆诊断协议及 5 秒结果](https://github.com/fengmaker/vrptw_slover/blob/9fe59ad51b9533f00bb8efe097143ad0fa5ba8ef/benchmarks/FOUR_SOLVER_REPORT.md#L63-L89)。

这些是单机、单 seed 的一次限时观察，不是多 seed 稳定性或全局最优性证明；报告指出计时边界受机器负载影响。PyVRP 结果仅说明本地 0.13.0a0、给定固定成本且未调用 `minimise_fleet()` 的这次运行，不能代表该库最佳 VRPTW 能力。Gurobi 使用基础 MTZ 模型，报告记录 5 秒可行记录的 MIP gap 中位数约 99.17%、节点中位数 1，并明确指出这不能泛化为 Gurobi 求解 VRPTW 的能力上限。[限制与阶段分析](https://github.com/fengmaker/vrptw_slover/blob/9fe59ad51b9533f00bb8efe097143ad0fa5ba8ef/benchmarks/FOUR_SOLVER_REPORT.md#L123-L140)。求解器返回的是已找到的可行解，代码也明确说明不代表证明全局最优。[项目 CLI 结果说明](https://github.com/fengmaker/vrptw_slover/blob/9fe59ad51b9533f00bb8efe097143ad0fa5ba8ef/README.md#L61-L61)。

### 与 M12 单独验收实验区分

[`M12_REPORT.md`](https://github.com/fengmaker/vrptw_slover/blob/9fe59ad51b9533f00bb8efe097143ad0fa5ba8ef/benchmarks/M12_REPORT.md#L32-L64) 核验的是 Python 与原生后端迁移：两轮 56 实例 × 3 种子 × 0.5 秒、诊断关闭的成对运行，另报告最终默认 CLI 批次。它复用 M10 已归档的“固定 PyVRP 车辆上限”距离参考；两轮原生中位 gap 为 9.2651% / 8.8562%，最终 CLI 为 8.9252%。这与四方主实验的单 seed、车辆数优先目标及 24 例同车距离子集不同，两个报告的中位数不可拼接成同一趋势。M12 构建及重复运行命令见[报告复现段](https://github.com/fengmaker/vrptw_slover/blob/9fe59ad51b9533f00bb8efe097143ad0fa5ba8ef/benchmarks/M12_REPORT.md#L66-L89)。

## 复现命令

从仓库根目录运行；使用新的输出目录将完整重跑 448 次主实验：

```powershell
.\benchmarks\four_solver\run.ps1 -Out runs/four_solver_repeat
```

单独的 Python 分步入口和汇总命令也记录在[运行说明](https://github.com/fengmaker/vrptw_slover/blob/9fe59ad51b9533f00bb8efe097143ad0fa5ba8ef/benchmarks/four_solver/README.md#L7-L35)。重跑需要 Windows 原生扩展、所列 OR-Tools 与 Gurobi 版本、PyVRP 本地构建及可用 Gurobi 许可证；完整串行搜索约 20 分钟，CPU 占用和限时停止位置可能改变结果。只分析已保存的运行 CSV 时，`benchmarks/four_solver/analyse.py` 仅需 Python 标准库。

## 可用于作品集的图表和图片

优先用 [`results/per_instance_wide.csv`](https://github.com/fengmaker/vrptw_slover/blob/9fe59ad51b9533f00bb8efe097143ad0fa5ba8ef/benchmarks/four_solver/results/per_instance_wide.csv#L1-L3)：112 行，含预算、实例、四求解器车辆数与距离；可画 0.5/5 秒车辆数配对图，另画仅同车数样本的距离 gap 分布。`results/raw_runs.csv` 为 448 行原始表，含 solver、instance、budget、seed、status、feasible、vehicles、distance_ticks、distance 和后端 metadata，适合保留原始状态与复核关系。Gurobi 需显示可行覆盖，不应对缺解实例伪造车辆数。

优先展示 RC108 的路线图与收敛图：路线布局清楚，收敛图能看到车辆数与距离逐步下降。C103 路线图可作补充；其收敛图基本平坦，展示信息较少。上述均为 M12 最终交付的 seed 0 图，不是四求解器 5 秒主表结果：[`RC108 routes.png`](https://github.com/fengmaker/vrptw_slover/blob/9fe59ad51b9533f00bb8efe097143ad0fa5ba8ef/benchmarks/m12/delivery/RC108/seed-0/routes.png)、[`RC108 convergence.png`](https://github.com/fengmaker/vrptw_slover/blob/9fe59ad51b9533f00bb8efe097143ad0fa5ba8ef/benchmarks/m12/delivery/RC108/seed-0/convergence.png)、[`C103 routes.png`](https://github.com/fengmaker/vrptw_slover/blob/9fe59ad51b9533f00bb8efe097143ad0fa5ba8ef/benchmarks/m12/delivery/C103/seed-0/routes.png)。
