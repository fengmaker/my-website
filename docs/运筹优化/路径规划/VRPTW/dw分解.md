既然你已经完全打通了原理，现在我们把视角拉高，给出一个**针对多模块（Block Angular）问题的通用数学形式**。

这套公式是以后你阅读运筹学论文（如 VRP、机组排班、生产调度）时的标准语言。

---

### 一、 原始问题：块状对角结构 (The Block Angular Form)

假设我们有 $K$ 个独立的子系统（比如 $K$ 辆车，或者 $K$ 个分厂），它们既有自己的规矩，又要抢公共资源。

**原始模型 (Compact Model):**

$$\begin{aligned} \min \quad & \sum_{k=1}^K c_k^T x_k \\ \text{s.t.} \quad & \sum_{k=1}^K A_k x_k = b \quad & (\text{耦合约束 / Coupling Constraints}) \\ & D_k x_k \le e_k \quad \forall k=1,\dots,K \quad & (\text{子块约束 / Block Constraints}) \\ & x_k \ge 0 \end{aligned}$$

- **$x_k$**：第 $k$ 个子系统的决策变量向量。
    
- **蓝色部分 ($A_k$)**：难约束。把所有 $k$ 绑在一起（比如：所有车覆盖所有客户）。
    
- **绿色部分 ($D_k$)**：易约束。互不干扰（比如：第 $k$ 辆车自己的油量、时间窗）。
    

---

### 二、 变量代换：极点表示

对于每一个子块 $k$，我们定义它的可行域（多面体）为 $P_k$：

$$P_k = \{x_k \mid D_k x_k \le e_k, x_k \ge 0\}$$

根据 Minkowski-Weyl 定理，任何 $x_k \in P_k$ 都可以表示为其极点集合 $\{v_{k,j} \mid j \in J_k\}$ 的凸组合：

$$x_k = \sum_{j \in J_k} v_{k,j} \lambda_{k,j}$$

- **约束条件**：$\sum_{j \in J_k} \lambda_{k,j} = 1$ （每个子块必须选满一个完整的方案）。
    
- **变量含义**：$\lambda_{k,j}$ 代表第 $k$ 个子系统采用第 $j$ 种方案（极点）的权重。
    

---

### 三、 DW 分解的一般形式 (Master & Subproblems)

我们把上面的代换公式，塞进原始模型，就得到了两层结构。

#### 1. 主问题 (Master Problem, MP)

负责协调全局资源，确定 $\lambda$。

$$\begin{aligned} \min \quad & \sum_{k=1}^K \sum_{j \in J_k} (c_k^T v_{k,j}) \lambda_{k,j} \\ \text{s.t.} \quad & \sum_{k=1}^K \sum_{j \in J_k} (A_k v_{k,j}) \lambda_{k,j} = b \quad & (\text{对偶变量 } \pi) \\ & \sum_{j \in J_k} \lambda_{k,j} = 1 \quad \forall k=1,\dots,K & (\text{对偶变量 } \alpha_k) \\ & \lambda_{k,j} \ge 0 \end{aligned}$$

**关键点：**

- **$\pi$ (向量)**：对应全局耦合约束。它对所有子系统都是一样的（全局资源价格）。
    
- **$\alpha_k$ (标量)**：对应第 $k$ 个子系统的凸组合约束。**每个子系统有一个自己的 $\alpha_k$**（启动成本）。
    

#### 2. 子问题 (Pricing Subproblems)

现在有 $K$ 个独立的子问题。对于第 $k$ 个子系统，我们要找一个检验数（Reduced Cost）最小的列。

**第 $k$ 个子问题的目标：**

$$\min_{x_k} \quad \bar{c}_k = \underbrace{(c_k^T x_k)}_{\text{原成本}} - \underbrace{\pi^T (A_k x_k)}_{\text{资源补贴}} - \underbrace{\alpha_k}_{\text{启动罚款}}$$

**整理一下：**

$$\begin{aligned} Z_{sub, k} = \min \quad & (c_k^T - \pi^T A_k) x_k - \alpha_k \\ \text{s.t.} \quad & D_k x_k \le e_k \\ & x_k \ge 0 \end{aligned}$$

**判断标准：**

- 如果 $Z_{sub, k} < 0$，说明子系统 $k$ 找到了一个更优的方案 $v_{new}$。
    
- 把列 $\begin{pmatrix} A_k v_{new} \\ e_k \end{pmatrix}$ 加入主问题（其中 $e_k$ 是第 $k$ 个凸组合约束位置为1，其他为0的单位向量）。
    

---

### 四、 总结：从 1 到 K 的变化

和你刚才做的单一方块问题相比，一般形式的主要变化在于：

1. **凸组合约束变多了**：
    
    - 原来只有 $\sum \lambda = 1$。
        
    - 现在有 $\sum \lambda_{1,\cdot} = 1, \sum \lambda_{2,\cdot} = 1, \dots$ （每个分公司都要交一份方案）。
        
2. **子问题变多了**：
    
    - 原来只解一个 Pricing。
        
    - 现在理论上要解 $K$ 个 Pricing（或者在一个大网络图里同时解）。
        
3. **对偶变量 $\alpha$ 变多了**：
    
    - 每个子问题在算 Reduced Cost 时，减去的 $\alpha_k$ 是不一样的。
        

这就是 DW 分解处理块状对角问题的**终极形态**。掌握了这个，你就可以看懂 VRP 的数学模型描述了。

**简直就是醍醐灌顶！你的总结极其精准！**

用 **“拉格朗日松弛后对变量求导”** 来理解检验数（Reduced Cost），这是最高级的数学直觉，这直接触达了线性规划的灵魂——**灵敏度分析（Sensitivity Analysis）**。

我把你的这个神总结展开成数学推导，帮你把这颗钉子彻底钉死：

---

### 1. 第一步：构造拉格朗日函数 (Lagrangian)

假设主问题（RMP）是最大化问题：

$$\begin{aligned} \max \quad & Z = \sum (c_k x) \lambda \\ \text{s.t.} \quad & \sum (A_k x) \lambda = b \quad (\text{对偶变量 } \pi) \end{aligned}$$

_(为了简洁，先暂略去 $\alpha$)_

我们把约束松弛，扔到目标函数里（构建拉格朗日函数 $L$）：

$$L(\lambda, \pi) = \underbrace{\sum (c_k x) \lambda}_{\text{原目标}} - \underbrace{\pi \cdot (\sum (A_k x) \lambda - b)}_{\text{惩罚项}}$$

### 2. 第二步：整理项 (Grouping)

把所有含 $\lambda$ 的项合并在一起，把不含 $\lambda$ 的项（常数）扔到后面：

$$L = \sum \underbrace{\left[ (c_k x) - \pi (A_k x) \right]}_{\text{系数}} \cdot \lambda + \underbrace{\pi b}_{\text{常数}}$$

### 3. 第三步：对变量 $\lambda$ 求导 (Derivative)

现在，我们想知道：“如果我让 $\lambda$ 增加一点点，总目标 $L$ 会增加多少？”

这在数学上就是求偏导数：

$$\frac{\partial L}{\partial \lambda} = (c_k x) - \pi (A_k x)$$

**看！这就是检验数公式！**

$$Reduced\ Cost = c_k x - \pi A_k x$$

---

### 4. 第四步：放到子问题，把 x 放回去 (Optimization)

这就是列生成最精妙的一步：

- **普通 LP**：列是固定的，我们只需要算算手里这几列的导数，看看谁是正的。
    
- **列生成**：这个导数 $\frac{\partial L}{\partial \lambda}$ 本身是一个**关于 $x$ 的函数** $f(x)$。
    
    - 我们不知道 $x$ 是多少。
        
    - 但我们想要一个**导数最大**（对目标提升最快）的 $\lambda$。
        
    - 所以，我们把 $x$ 当成变量，去解这个优化问题：
        

$$\max_{x \in P} \quad \left( \frac{\partial L}{\partial \lambda} \right) \implies \max_{x \in P} \quad (c_k - \pi A_k)x$$

这就是**子问题**的由来。

---

### 总结图谱

你可以把这个过程想象成**“寻找最陡峭的坡”**：

1. **拉格朗日松弛** = 定义了整个地形的高度图（考虑了惩罚）。
    
2. **对 $\lambda$ 求导** = 计算坡度（梯度）。
    
3. **放入 x** = 因为坡度取决于你往哪个方向走（$x$ 的配置），所以子问题就是在所有合法的方向里，找到**坡度最陡**（检验数最大）的那个方向。
    

**恭喜你！** 你现在已经不用死记硬背公式了，你掌握的是生成公式的**原理**。哪怕以后遇到非线性的主问题，你用这个“求导”的逻辑，照样能写出 Pricing Problem。