# 运筹优化：知识体系与学习地图

这部分按“理论 → 方法 → 问题 → 实现 → 项目”的主线组织，面向运筹优化算法的系统学习与工程实践。大部分既有内容参考[笑笑的站](https://smilingwayne.github.io/me/OROpt/)；我会随着学习加入自己的理解并持续修订。引用内容的来源与授权信息见文末“参考资料与许可”。

## 六个知识模块

| 模块 | 要回答的问题 | 入口 |
| --- | --- | --- |
| 01 · 基础理论与建模 | 如何表达决策、约束、目标，理论依据是什么？ | [线性规划、图论与建模技巧](../运筹优化/基础理论与建模/index.md) |
| 02 · 求解算法体系 | 怎样搜索、分解、定价或快速改进解？ | [精确算法、启发式、CP-SAT 与随机优化](../运筹优化/求解算法体系/index.md) |
| 03 · 经典优化问题 | 问题的业务假设、模型与算法选择是什么？ | [路径、调度、分配、图与能源](../运筹优化/经典优化问题/index.md) |
| 04 · 求解器与工程实现 | 怎样将模型和算法写成可核对的程序？ | [工具与实现索引](../运筹优化/求解器与工程实现/index.md) |
| 05 · 项目与实验复现 | 自己实现了什么，效果如何，有哪些证据？ | [开发方案与实验记录](../运筹优化/项目与实验复现/index.md) |
| 06 · 资料库与面试 | 怎样复习、查资料和探索交叉方向？ | [题库、课程、解谜与标签](../运筹优化/资料库与面试/index.md) |

## 两种检索方式

- 按问题探索：[问题—算法索引](../运筹优化/学习地图/问题算法索引.md) → [VRPTW](../运筹优化/路径规划/VRPTW/总笔记.md) → [DW 分解应用](../运筹优化/路径规划/VRPTW/dw分解.md) → [开发方案](../运筹优化/路径规划/VRPTW/研究方案.md)。
- 按方法探索：[精确算法索引](../运筹优化/求解算法体系/精确算法.md) → [列生成原理](../运筹优化/求解方法/列生成与DW分解.md) → [下料问题](../运筹优化/求解算法/Chapter12.md)或[VRPTW 分支定价](../运筹优化/求解算法/ExactVRP.md)。

第一次系统学习可按[系统学习路线](../运筹优化/学习地图/系统学习路线.md)推进；按关键词跨专题查找可使用[标签索引](../运筹优化/资料库与面试/标签索引.md)。

## 内容归属与扩展

每篇文章只保留一个导航入口，原理文章与问题应用通过链接连接。入门、详解和专题应用保留各自范围，不合并不同内容。现有 Markdown 路径与文章 URL 保持不变，旧文件夹名不再决定导航分类。

未完成的 CP-SAT 通用教程、独立 FJSP Solver、鲁棒优化等逐步补充；项目方案与实测成果分别标记，不为未来主题建立空目录。新项目采用[专题与实验记录模板](../运筹优化/项目与实验复现/专题与实验记录模板.md)。

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
