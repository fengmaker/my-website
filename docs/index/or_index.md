# 运筹优化：从 P 到 NP-Hard 的艺术

> "The purpose of computing is insight, not numbers." — Richard Hamming

## 🗺️ 知识图谱与演进路线

本专栏记录了我从经典运筹问题到复杂工业级路径规划算法的探索历程。

我的研究路线遵循 **“约束递增 (Constraints Increment)”** 的逻辑，旨在构建一套可复用、高鲁棒性的求解器架构。

---

### 1. 起点：TSP (旅行商问题)
**一切路径规划的原子问题。**

在这里，我主要关注如何将一个组合优化问题建模为整数规划 (MIP)，并探索最基础的精确解法。

- **核心关注：**
    - MTZ / DFJ 约束消除
    - 动态规划解法 (Dynamic Programming)

### 2. 进阶：CVRP (带容量约束的车辆路径问题)
**从“单人独旅”进化为“车队调度”。**

引入了 **Capacity (容量)** 约束，问题性质发生了质变，开始涉及多车协同与资源分配。

- **核心关注：**
    - 节约算法 (Clarke-Wright)
    - 禁忌搜索 (Tabu Search) 初探

### 3. 终极挑战：VRPTW (带时间窗的车辆路径问题)
**这是我目前的核心主攻方向。**

在 CVRP 基础上引入 **Time Window (时间窗)** 硬约束，这是现代物流配送中最真实的场景。

- **核心技术栈：**
    - **数学分解：** Dantzig-Wolfe 分解 (D-W Decomposition)
    - **精确算法：** 分支定价切割 (Branch-Cut-and-Price, BCP) 
    - **子问题加速：** 标签算法 (Labeling Algorithm) 与桶图优化 (Bucket Graph)

---

## 🛠️ 方法论：精确与启发

在运筹优化的世界里，我坚持 **“双腿走路”**：

| 方法流派 | 核心理念 | 我的实践 |
| :--- | :--- | :--- |
| **Exact Methods**<br>(精确算法) | 追求数学上的最优解 (Global Optimum)，挑战算力极限。 | 深入研究 **Column Generation (列生成)** 框架，手写 BCP 求解器。 |
| **Heuristics**<br>(启发式算法) | 在有限时间内寻找高质量满意解，追求工程可行性。 | 实现 **ALNS (自适应大邻域搜索)**，应对大规模算例。 |

## 📚 阅读指南

本笔记包含大量的数学模型（LaTeX）与 Python/C++ 代码实现。建议按照 `TSP -> CVRP -> VRPTW` 的顺序阅读，体会模型是如何像乐高积木一样被搭建起来的。