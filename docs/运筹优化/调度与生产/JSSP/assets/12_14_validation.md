# 第 12–14 节验收记录

核验日期：2026-10-12。三节均为第一版、待用户 review；本记录说明计算与格式检查范围，不代表用户已认可内容。

## 计算检查

- 第 12 节：逐机器工序对距离；全部减少距离的可行相邻交换；按目标值与固定 tie-break 选择的四步重连；各候选和路径时间表的独立区间检查。
- 第 13 节：明确标注为 `illustrative` 的教学 CSV；重新读入 CSV 核对均值；最好值、中位数、最差值、样本标准差、RPD、Greedy 改善率与最优值频次。
- 第 14 节：OS/MS 追加解码得 A=8、B=7；另一条 DAG 解码路径穷举 8 种 MS、60 组机器队列，其中 26 组可行，最小值 7；全部可行时间表通过独立区间检查；最快机器/分流反例为 6/4；两类入门全局下界均为 5。

第 14 节最优值 7 的一般排除论证已写入 14.4；枚举用于交叉核算。本次未运行 OR-Tools，也未运行任何公开实例的算法性能实验。

```text
python Heuristic/fjsp_learning/jssp/scripts/12_14_build_figures.py
python Heuristic/fjsp_learning/jssp/scripts/12_14_check_notes.py
```

依赖：Python、Matplotlib、`markdown-it-py` 及前文既有的核算 helper。数值明细见 [12_14_numerical_check.json](https://github.com/fengmaker/my-website/blob/main/Heuristic/fjsp_learning/jssp/checks/12_14_numerical_check.json)，格式统计见 [12_14_validation.json](https://github.com/fengmaker/my-website/blob/main/Heuristic/fjsp_learning/jssp/checks/12_14_validation.json)。

## 格式与图表

检查脚本用 CommonMark 兼容解析器检查三节、专题目录 与两份来源记录的公式分隔符、TeX 花括号、加粗解析、表格与本地相对链接，并生成系统临时目录下的 HTML 预览。MathJax 3 从 jsDelivr 加载，需要网络。

三张配图保存为 PNG 与 SVG，并保留绘图源码；下标使用绘图工具的数学环境。已逐张查看 PNG，核对重连折线、示意频次、甘特图区间、工序下标和图注；修正第 14 节甘特图的横轴标签与图例重叠后再次查看，未发现裁切或重叠。

HTML 浏览器视觉验收未完成：当前 Computer Use 浏览器清单为空，in-app browser 不可用；另行尝试的 Chrome 无头渲染因 GPU 初始化失败退出，Edge 无头渲染超时，均未取得可验收截图。因此本记录只确认 Markdown 解析、本地链接、数值和 PNG 视觉检查通过，不把它们称作完整 Markdown 渲染验收。检查脚本仍生成可供后续打开的 HTML 预览。

未覆盖环境：用户 IDE 的内置 Markdown 预览。CommonMark + MathJax 预览结果不保证所有编辑器插件采用相同渲染规则。

## 来源

第 12、14 节来源由独立研究代理查阅，主代理复核代表性原论文页、作者稿与官方源码，再决定正文表述。只读到摘要的论文已标明阅读限制；没有据摘要补写完整算法细节。详见 [第 12 节来源](12_sources_verified.md)、[第 14 节来源](14_sources_verified.md)。第 13 节入口与格式事实在正文逐项链接 OR-Library、Taillard 作者页与 JSPLib 维护仓库。
