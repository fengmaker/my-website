# 作品集实验材料核查

核查日期：2026-10-11。对应用户已完成的两个项目；本轮只读检查源项目、解析归档记录、重算汇总并生成网站图表，没有安装项目依赖或重跑求解器。

| 项目 | 核查来源 | 本轮重算范围 |
| --- | --- | --- |
| GMRP-ALNS | 用户本地 `D:\AAA-OR-Route\GAP`，HEAD `0ce7fd2061240144d9430d417070fe8951de7113`；M7 源码冻结于 `ee29875c39c111c0b2a651e56450829b6f376599` | 660 条记录签名 / 归档校验和 / checker 回执与成本一致性；6 主方法各 100 条，超容差 178 + 30 = 208 |
| VRPTW Solver | 公开仓库固定 commit `9fe59ad51b9533f00bb8efe097143ad0fa5ba8ef` | 四方主实验 448 行；车辆数、共同可行集合、同车距离 Gap 的中位数与 P90 |

细节见 [GMRP 核查](gmrp-audit.md)与 [VRPTW 核查](vrptw-audit.md)。GMRP 原仓库中的无关本地改动保持原样，未纳入本站材料；原项目目录均未被修改。

网站提供 5 个 CSV、4 张 PNG 和一个[来源清单](../../docs/assets/projects/provenance.json)。CSV 包括原汇总文件及精简观察表：GMRP 观察表保留原记录 ID、目标、时间与 checker 状态，VRPTW 运行表去掉冗长后端 metadata 与本机 solution 路径；它们不是完整 assignment / route 档案。记录中的 `record_sha256` 指向原始完整记录，并不是精简 CSV 行的哈希。原文件 SHA-256、投影规则和发布文件校验值写入来源清单；官方输入没有复制到网站。

两张汇总图由本站脚本重新绘制；RC108 路线与轨迹图按固定版本原样复制，明确标为 M12 delivery、seed 0、0.5 秒，未混入四方 5 秒主表。图表已查看，图例和坐标说明无重叠。

重画汇总图仅需可选的 Matplotlib 依赖：

```powershell
python -m pip install matplotlib
python -B scripts/plot_project_results.py
```

该命令只读取已提交 CSV 并更新两张 PNG，不执行优化实验。完整实验或归档报告再生的命令放在各项目页面，并注明环境、预算、依赖和输入要求。

GMRP 材料核查时公开接口返回 404，因此证据来自本地固定快照。2026-10-11 用户随后确认仓库已公开；来源清单中的访问情况保留为核查当时的历史记录。VRPTW 原拼写 `vrptw_slover` 沿用实际仓库地址。两项目的百分比采用不同基准，不作跨问题性能排名。
