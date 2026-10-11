---
tags:
  - CP-SAT
  - 建模
  - 基础理论
---

# CP-SAT 建模入门：变量域、逻辑与求解状态

阅读谜题或调度案例之前，先把模型拆成变量域、约束、目标和结果解释。本文使用 OR-Tools Python 接口讲解建模语义，代码是教学示例，尚未执行求解或性能实验。

## 变量域是模型的一部分

整数变量需要明确上下界，布尔变量取值为 0 或 1。边界应来自问题本身，例如任务总时长、车辆容量或可选集合，过宽的边界会丢失可用信息，也可能使缩放后的表达式超出整数范围。

CP-SAT 的线性约束使用整数表达。存在有理数系数时，可以乘公分母得到等价整数约束；直接四舍五入通常会改变模型，必须说明容差和误差。具体要求与求解状态见 [CP-SAT 官方入门](https://developers.google.com/optimization/cp/cp_solver)。

约束传播可以理解为用约束缩小尚可行的变量域。例如整数变量满足 $x+y=10$、$0\le x,y\le10$ 且 $x\ge7$，便能推出 $y\le3$。传播与搜索共同推进求解；传播本身不保证已经找到解。

## 条件约束只表达一个方向

`constraint.only_enforce_if(b)` 表示 $b=1$ 时约束必须成立。它不会自动保证“约束成立时 $b=1$”。要表达 $b\Leftrightarrow x\ge8$，可同时写出：

$$
b\Rightarrow x\ge8,\qquad \neg b\Rightarrow x\le7.
$$

第二条使用了 $x$ 为整数的前提。此类双向关联称为 channeling；更多建模方式见 [官方 channeling 示例](https://developers.google.com/optimization/cp/channeling)。

```python
from ortools.sat.python import cp_model

model = cp_model.CpModel()
load = model.new_int_var(0, 12, "load")
high = model.new_bool_var("high")

# high 与“load 至少为 8”等价，而非仅单向蕴含。
model.add(load >= 8).only_enforce_if(high)
model.add(load <= 7).only_enforce_if(~high)
model.add(load >= 5)
model.minimize(load)

solver = cp_model.CpSolver()
solver.parameters.max_time_in_seconds = 2.0
status = solver.solve(model)

if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
    print(solver.status_name(status), solver.value(load), solver.value(high))
else:
    print(solver.status_name(status))
```

这是用于解释接口的完整小模型。时间上限只是停止参数，不能把此片段当成运行时间测量。Python 的 `if` 在构建模型时执行，不能用 `if high:` 代表求解中的逻辑分支。

## 结果状态决定能否读变量值

| 状态 | 结果解释 |
| --- | --- |
| `OPTIMAL` | 已证明当前模型的最优性；无目标的可行性模型也可能返回此状态。 |
| `FEASIBLE` | 已找到可行解，尚未证明最优。 |
| `INFEASIBLE` | 已证明当前模型不可行；需检查是否漏建、错建了业务规则。 |
| `MODEL_INVALID` | 模型未通过校验，需要修复变量、约束或数值表达。 |
| `UNKNOWN` | 停止时未得到可报告的可行性结论，例如过早达到限制。 |

只在 `OPTIMAL` 或 `FEASIBLE` 时读取解值。即便返回最优，也应核对模型是否完整表达业务问题；模型最优与业务决策正确是两层判断。

## 从普通约束走向全局约束

`all_different` 描述一组变量互不相同；`no_overlap` 描述区间互不重叠；`circuit` 描述特定环路结构。选用这些接口前，应确认其变量、可选对象以及自环等语义，不能只凭名称替换原模型。也不是所有约束都支持 `only_enforce_if`，条件化前应核对接口支持并检查模型有效性。

在作业车间调度中，一个操作可以由开始时间、持续时间与结束时间构成区间。同一机器的操作需要不重叠，同一作业的操作还需要先后关系；机器不重叠不会自动推出作业内的顺序。完整建模思路见 [OR-Tools 作业车间示例](https://developers.google.com/optimization/scheduling/job_shop)。FJSP 还涉及机器选择与可选区间，本站尚未提供对应的完整 CP-SAT 实现。

## 建模检查清单

1. 每个业务决策是否有变量，域是否包含全部合法取值？
2. 每条逻辑是单向还是双向？否定条件在整数域上是否准确？
3. 时间、距离、成本是否统一单位？缩放是否等价，表达式是否可能溢出？
4. 是否遗漏覆盖、唯一分配、连通性或先后约束？
5. 是否先检查状态再读解，并用业务规则独立验证结果？

继续阅读[环路类谜题](../解谜/CPSAT_1.md)、[涂色连通性](../解谜/CPSAT_2.md)和 [JSP / FJSP 问题笔记](../调度与生产/JSP.md)。这些材料保留各自来源；未来实测按[实验规范](../求解器与工程实现/实验规范.md)另行记录。
