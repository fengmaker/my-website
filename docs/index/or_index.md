# 运筹优化：学习路线

这部分按“先会建模，再理解求解，最后进入路径规划问题”的顺序整理。大部分内容参考[笑笑的站](https://smilingwayne.github.io/me/OROpt/)；我会随着学习加入自己的理解并持续修订。引用内容的来源与授权信息见文末的“参考资料与许可”。

| 阶段 | 要回答的问题 | 从这里开始 |
| --- | --- | --- |
| 基础建模 | 目标、约束和决策变量怎么写？ | [线性规划与对偶](../运筹优化/基础建模/线性规划与对偶.md) → [整数规划与松弛](../运筹优化/基础建模/整数规划与松弛.md) → [0-1 变量建模](../运筹优化/基础建模/0-1变量建模.md) |
| 图与离散优化 | 如何用图表示可行解，如何缩小搜索范围？ | [最短路与网络流](../运筹优化/图与离散优化/最短路与网络流.md) → [分支定界](../运筹优化/图与离散优化/分支定界.md) |
| 求解方法 | 变量太多、无法一次列完时怎么办？ | [列生成与 DW 分解](../运筹优化/求解方法/列生成与DW分解.md) |
| 路径规划 | 车辆、容量和时间窗如何逐步进入模型？ | [问题谱系](../运筹优化/路径规划/问题谱系.md) → [TSP](../运筹优化/路径规划/TSP/第一阶段.md) → [CVRP](../运筹优化/路径规划/CVRP/第一阶段.md) → [VRPTW](../运筹优化/路径规划/VRPTW/模型建立.md) |

## 一条具体的阅读线

1. 用线性规划认识可行域、松弛和对偶价格；再用整数规划认识“选或不选”的决定。
2. 学习最短路与分支定界。前者是许多路径子问题的基础，后者解释精确算法怎样证明最优。
3. 先读 TSP 的连通性约束，再读 CVRP 的容量约束，最后读 VRPTW 的到达时间传播。对照三个模型，检查新增约束是否真的排除了不可行解。
4. 读列生成和 DW 分解后，回看 [VRPTW 的 DW 分解笔记](../运筹优化/路径规划/VRPTW/dw分解.md)，理解“按弧选路”和“按完整路径选路”的区别。

## 按主题继续阅读

左侧导航还按主题收录了[运筹学基础](../运筹优化/运筹学基础/Chapter1.md)、[离散优化](../运筹优化/离散优化/Ch_01.md)、[应用建模](../运筹优化/应用建模/Max_k_cut.md)、[求解算法](../运筹优化/求解算法/Chapter12.md)、[不确定性](../运筹优化/不确定性/SAA.md)、[解谜](../运筹优化/解谜/CPSAT_1.md)及[调度与生产](../运筹优化/调度与生产/JSP.md)。路径规划下的 TSP、CVRP、VRPTW 各有独立文件夹，方便继续补充笔记。

??? info "参考资料与许可"
    本栏主要参考 [SmilingWayne/me](https://github.com/SmilingWayne/me/tree/371cfb49f7f9b0c2ee1c25a69a81352deae3558b) 的“运筹与优化”内容，作者 SmilingWayne。配图主要来自 [SmilingWayne/picsrepo](https://github.com/SmilingWayne/picsrepo)，另有一张来自 [博客园原图](https://img2018.cnblogs.com/blog/1903168/201912/1903168-20191220004845529-3040599.jpg)。

    原文档的 MIT 许可声明如下：

    ```text
    MIT License

    Copyright (c) 2023 SmilingWayne

    Permission is hereby granted, free of charge, to any person obtaining a copy
    of this software and associated documentation files (the "Software"), to deal
    in the Software without restriction, including without limitation the rights
    to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
    copies of the Software, and to permit persons to whom the Software is
    furnished to do so, subject to the following conditions:

    The above copyright notice and this permission notice shall be included in all
    copies or substantial portions of the Software.

    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
    AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
    LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
    OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
    SOFTWARE.
    ```
