# GMRP-ALNS 本地证据审计

审计日期：2026-10-11。范围是本机 `D:\AAA-OR-Route\GAP` 的只读快照；未访问 GitHub、未运行项目代码或 solver、未安装依赖，也未复制 ROADEF/OR-Library 原始数据。主代理本轮对 GitHub 公开接口的检查返回 404，因此以下结论只对本地快照负责。

## 身份、提交与完整性

- `README_zh.md:1,5-8` 和 `pyproject.toml:26-30` 将项目标识为 **fengmaker/GMRP-ALNS**，研究对象为 ROADEF/EURO 2012 Machine Reassignment Problem（GMRP）。本机 `origin` URL 是 `https://github.com/fengmaker/GMRP-ALNS.git`。
- 本地 `HEAD`：`0ce7fd2061240144d9430d417070fe8951de7113`（2026-09-20，`docs: record optimization portfolio project sequence`）。`v1.0.0` 是 annotated tag，tag object `c019135f3f2da4bafc5ba546afb0f6ad614efe24`，指向 release commit `ede65ce54947b33838e9d8929fb1f611e8535521`；HEAD 在 tag 后 3 个提交。
- 工作树带有与 M7 证据无关的本地改动：`QA.md` 修改、`docs/portfolio_zh.md` 删除、`docs/1111 portfolio_zh.md` 未跟踪。指定 README、M7 文档及 `results/m7/` 在工作树中均无未提交差异。以下统计来自提交内容中的归档，而不是这些本地改动。
- M7 manifest 记录的实验源码提交为 `ee29875c39c111c0b2a651e56450829b6f376599`，冻结时工作树状态字段为空。manifest 源码摘要为 `ddb2dba016f365b3853e3028416c7d0ce9cf79f5694a75466cd098b0f7d32c27`；按 `protocol.py:37-39` 的算法，从该提交读取 34 个 `src/**/*.py` 并重算后完全匹配。
- M7 `manifest.json` SHA-256：`829de290e1e374b13b06024e66bcacf16a75785bc13b7662b9522e328e8005e5`；`records.jsonl` 为 4,100,186 bytes，SHA-256：`aca9570d6a3c47ad5afff0d5a16e23547ab9261d47b8d8a63f834380b119a0b2`。归档 `checksums.json` 中列出的 11 个文件全部匹配；manifest 中的 40 个实例/初始 assignment 文件哈希和 checker 二进制哈希也全部与本机忽略数据目录的文件匹配。没有把这些官方文件带入网站。

## 问题、规模与实验设计

GMRP 为每个 process 选一台最终 machine。官方可行性条件包括容量（含 transient resource 双端占用）、同 service 不同 process 不同机、service location spread、neighborhood service dependency。目标最小化五类加权成本：超过 safety capacity 的 load、可用容量上的 balance penalty、process move、所有 service 中最大 moved-process 数、以及 source-to-destination machine move cost。公式与实现约定见 `docs/mathematical_model.md:7-20,48-62`；service move 项是各 service 搬迁数的最大值，不是总和。

M7 使用 20 个官方 A/B 实例（A1/A2 各 5 个，B 组 10 个），种子 `7, 42, 101, 202, 303`，请求搜索时限 1.0 秒。六个主方法为 Initial、Relocate、VND、Random LNS、Adaptive ALNS、ALNS + Restricted CP-SAT Repair：`20 × 5 × 6 = 600` 个观察。另在 A1_2、A2_3、B3、B7 上各跑 3 个额外消融、每个种子一次，增加 `4 × 5 × 3 = 60`，合计 660；Restricted Repair 自身已在六方法主矩阵中，不能重复计入额外消融。规模从 4–5,000 台 machine、100–50,000 个 process 不等。协议见 `docs/m7_protocol.md:7-11,25-32` 与 `docs/m7_verification.md:5-9`。

Restricted Repair 在 ALNS 中周期触发：把选中的 process 联合建模，冻结其余 assignment，以受限 machine domain 调用一个 CP-SAT worker；每 10 轮至多触发一次，变量上限 100、候选 machine 上限 10、局部 solver 时间 0.05 秒，只有经验证的严格改进才写回。实现/边界见 `docs/algorithm.md:47-59`，固定参数见 `results/m7/manifest.json` 的 config。

测量机为 Windows 11 build 22621、Python 3.12.4、AMD64 Family 25 Model 68、8 physical/16 logical CPU、16,371,519,488 bytes RAM；OR-Tools 9.15.6755、NumPy 2.5.3、psutil 7.2.2、Matplotlib 3.11.2；数值库线程、CP-SAT worker、并行实验进程均设为 1。首轮 45 次观测因 Windows launcher 内存采样错误而排除，v2 runner 改为跟踪 Python 子进程；协议、参数、实例、种子和预算未改变。详见 `docs/m7_verification.md:17-30`。

## 从 660 条记录独立重算

对 `results/m7/records.jsonl` 逐行解析得到 660 条非空且唯一记录；所有记录的 run ID 都对应 manifest matrix，660 个 `record_sha256` 均匹配规范化记录摘要，且 `manifest_sha256` 均指向同一 manifest。每条记录都是 `status=ok`。改善率使用项目公式 `100 × (initial_cost - best_cost) / initial_cost`，先按每条观察计算，再在每个 100 条主方法行上等权平均。下表的值由本次逐行解析重算：

| 主方法（n=100 各） | 平均改善率 | solver call > 1.1 秒 |
|---|---:|---:|
| Initial（确定性对照） | 0.000% | 0 |
| Relocate | 12.032% | 30 |
| VND | 12.008% | 31 |
| Random LNS | 5.584% | 37 |
| Adaptive ALNS | 9.126% | 40 |
| ALNS + Restricted Repair | 8.994% | 40 |
| **主矩阵小计（600）** | — | **178** |

三项额外消融（random-only、no-restart、greedy-only）各 20 条，分别有 10 次超过 1.1 秒；所以完整归档为 **208/660**。原始请求是 1.0 秒，1.1 秒是预注册容差界；这里的 208 是完整 solver call 超过该容差，不等同于超过内部搜索 deadline。solver call 测量含状态构建、warm start、Restricted call 和最终 oracle，parse 与 checker 另行计时。

完整性字段也逐条交叉核对：660/660 的归档记录为 `feasible=true`、`official_valid=true`、`checker_returncode=0`；checker stdout 均报告 `Solution is valid`，并给出与 `best_cost` 一致的总目标值；五个加权 objective component 重新相加也均等于 `best_cost`。但归档只保留 `solution_sha256`，不包含 660 个 assignment 向量，因此本审计能独立验证记录标记、checker 回执、目标值和摘要的一致性，不能从 JSONL 单独重放完整 validator/checker 来重新证明每个约束。

## 结果解释与边界

1 秒请求档上，Relocate 与 VND 的平均改善率略高于 ALNS；主矩阵中 Restricted Repair 对 ALNS 的平均配对收益是 `-0.131` 个百分点（32 胜 / 35 平 / 33 负）。在 held-out B3–B10 的 40 对里，Restricted 为 10 胜 / 22 平 / 8 负，平均 `-0.222` 个百分点，而且没有一对双方都落在 1.1 秒容差内。B 组改善普遍远低于 A 组。

这是一项单机、单一 1 秒请求预算研究；没有 BKS gap、竞赛程序对比、显著性检验或 10/60/300 秒结果。`no-restart` 的 20 个 ALNS 样本都没有达到 200 轮触发点（观测为 0–57 轮），所以其表面收益不支持 restart 的因果结论。报告把 208 次超容差如实保留，不应写成“严格一秒完成”或 SOTA。见 `docs/m7_verification.md:75-103,105-126,164-171` 与 `docs/release_audit_v1.0.0.md:55-60`。

GAP 是另一个 Generalized Assignment Problem 玩具/OR-Library 基线，不是 GMRP 实例或 M7 结果。README 快速开始将 GMRP toy 成本 2411 与 GAP toy 成本 8 分开报告（`README_zh.md:64-79`）；作品集不要把 GAP 的“8”写成 GMRP 成本，也不要把 GAP 精确基线描述成 ROADEF 竞赛结果。

## 复现与可复制素材

报告 CLI 的静态代码路径支持直接从归档 `manifest.json` + `records.jsonl` 重建：`report.py:17-44` 在缺少逐记录 JSON 文件时解析 JSONL，并检查每条记录摘要、manifest 摘要及冻结矩阵身份；`report.py:177-231` 只汇总、绘图和写文件，不调用 solver。外部项目根目录中的精确命令为：

```powershell
.\.venv\Scripts\python.exe -m gmrp_alns.experiments report results/m7 results/report/m7-regen
```

命令未在本次审计执行。完整重跑 M7 则需要安装 `.[dev,experiments]`、先将官方 A/B 文件和官方 checker 放到 `data/raw/roadef/`，再按 `docs/m7_verification.md:138-162` 的 freeze/run/report 命令执行；依赖定义在 `pyproject.toml:22-38`，项目没有 `requirements.txt`。

可从本机归档少量复制至作品集的证据素材：

- `results/m7/quality_runtime.png`（67,677 bytes）：主算法改善率与时间；
- `results/m7/ablations.png`（38,895 bytes）：消融配对；
- `results/m7/convergence.png`（96,697 bytes）：收敛曲线；
- `results/m7/summary.csv`（18,973 bytes）：机器可读的逐实例/方法汇总；
- 可选 `results/m7/manifest.json`（107,266 bytes）：实验来源、配置、环境和输入/checker 哈希。

`records.jsonl` 有约 4.1 MB，适合保留作审计源或从中生成精简观察 CSV；完整官方输入与 checker 不应复制到网站。本项源项目审计只写入本报告；网站最终采用的表格和图表见[材料清单](README.md)。

## 原始来源定位

路径均相对于 `D:\AAA-OR-Route\GAP`：

- `README_zh.md:5-8,23,26-38,64-79,95-121`
- `docs/mathematical_model.md:7-20,48-68`
- `docs/m7_protocol.md:7-11,25-43,51-55`
- `docs/m7_verification.md:5-46,48-80,82-103,105-171`
- `docs/algorithm.md:47-59`
- `docs/reproducibility.md:51-80`
- `docs/release_audit_v1.0.0.md:44-60`
- `pyproject.toml:22-38`
- `results/m7/manifest.json`, `records.jsonl`, `checksums.json`, `summary.csv`, `summary.json`
- report CLI：`src/gmrp_alns/experiments/__main__.py:21-34`、`src/gmrp_alns/experiments/report.py:17-44,177-231`
