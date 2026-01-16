这几道题属于 **“多状态动态规划” (Multi-State DP)**，也被称为 **“状态机 DP” (State Machine DP)**。

它们的共同特点是：当前位置的最优解，不仅取决于数值大小，还取决于当前处于什么**“状态”**（如：正负、奇偶、峰谷、持有/空仓等）。

---

### 一、 核心模版与心法

1. 状态定义

通常不需要一个 $N$ 维数组，只需要定义几个变量来代表不同的“结尾状态”。

例如：pos/neg（正负），odd/even（奇偶），up/down（峰谷）。

2. 状态转移 (滚动更新)

遍历数组时，根据当前数字 x 的特征，更新这几个状态变量。

- **技巧**：使用 `new_state` 临时变量或 Python 的元组解包 `a, b = new_a, new_b` 来保证同时也更新，避免使用已经污染的新值。
    

**3. 通用代码框架**

Python

```
# 初始化状态 (根据题意，可能是 0，-inf，或 nums[0])
state_A = ...
state_B = ...

for x in nums:
    # 暂存旧值 (如果需要)
    last_A, last_B = state_A, state_B
    
    # 根据逻辑计算新值
    # 这里的逻辑通常涉及 max/min 以及状态之间的跳跃
    state_A = calculate_A(last_A, last_B, x)
    state_B = calculate_B(last_A, last_B, x)

return max(state_A, state_B)
```

---

### 二、 题目详细解析

#### 1. 3259. 超级饮料的最大强化能量

- **DP 定义**：
    
    - `f[i][0]`：第 `i` 小时喝了 A 饮料能获得的最大能量。
        
    - `f[i][1]`：第 `i` 小时喝了 B 饮料能获得的最大能量。
        
- **技巧**：**冷却期**。如果切换饮料，需要回溯到 `i-2` 的状态（因为 `i-1` 在冷却）。
    
- **空间优化代码**：
    

Python

```
class Solution:
    def maxEnergyBoost(self, a: List[int], b: List[int]) -> int:
        # prev: i-2 时刻的状态 (刚喝完 A/B)
        # curr: i-1 时刻的状态 (刚喝完 A/B)
        # 初始化：因为有冷却期，i=0 时之前的状态设为 -inf
        prev_a = prev_b = float('-inf') 
        curr_a, curr_b = a[0], b[0]
        
        for i in range(1, len(a)):
            # 选项1: 继续喝同类 (接 curr)
            # 选项2: 切换类别 (接 prev，因为中间空了一格)
            new_a = max(curr_a, prev_b) + a[i]
            new_b = max(curr_b, prev_a) + b[i]
            
            # 滚动
            prev_a, prev_b = curr_a, curr_b
            curr_a, curr_b = new_a, new_b
            
        return max(curr_a, curr_b)
```

#### 2. 2222. 选择建筑的方案数

- **DP 定义**：这不是标准的状态机，而是**前缀状态计数**。
    
    - `n0`, `n1`：长度为 1 的 "0", "1" 的数量。
        
    - `n01`, `n10`：长度为 2 的 "01", "10" 的数量。
        
- **技巧**：**乘法原理**。遇到 '0'，它能组成的 "10" 的数量等于前面 "1" 的数量。
    
- **空间优化代码**：
    

Python

```
class Solution:
    def numberOfWays(self, s: str) -> int:
        n0, n1 = 0, 0
        n10, n01 = 0, 0
        ans = 0
        for c in s:
            if c == '0':
                ans += n01      # 组成 "010"
                n10 += n1       # 组成 "10"
                n0 += 1
            else:
                ans += n10      # 组成 "101"
                n01 += n0       # 组成 "01"
                n1 += 1
        return ans
```

#### 3. 2708. 一个小组的最大实力值 (联系 152)

- **DP 定义**：
    
    - `mx`：以当前位置结尾（或包含当前位置）的最大**正**乘积。
        
    - `mn`：以当前位置结尾（或包含当前位置）的最小**负**乘积。
        
- **技巧**：**负负得正**。这题和 152 (Max Product Subarray) 的区别在于 **152 是连续子数组（必须选），本题是子序列（可以不选，跳过）**。
    
    - 如果不选 `x`：状态保持 `mx, mn` 不变。
        
    - 如果选 `x`：状态变为 `mx * x` 或 `mn * x`。
        
- **空间优化代码**：
    

Python

```
class Solution:
    def maxStrength(self, nums: List[int]) -> int:
        # 特判：虽然题目说非空，但如果全是0或只有一个负数需要特殊处理
        # 这里的 DP 逻辑能覆盖大部分，但纯贪心其实更简单。
        # 为了演示 DP 模版：
        
        # mx: 最大积, mn: 最小积
        # 初始化为 nums[0]
        mx = mn = nums[0]
        
        for x in nums[1:]:
            # 可能性：
            # 1. 不选 x (保持 mx, mn)
            # 2. 选 x (单独一个 x)
            # 3. 选 x 并累乘 (mx*x, mn*x)
            candidates = [mx, mn, x, mx * x, mn * x]
            mx = max(candidates)
            mn = min(candidates)
            
        return mx
```

#### 4. 1567. 乘积为正数的最长子数组长度

- **DP 定义**：
    
    - `pos`：以当前元素结尾，乘积为**正**的最长连续长度。
        
    - `neg`：以当前元素结尾，乘积为**负**的最长连续长度。
        
- **技巧**：**交换律**。遇到负数时，正变负，负变正。
    
- **空间优化代码**：
    

Python

```
class Solution:
    def getMaxLen(self, nums: List[int]) -> int:
        pos, neg = 0, 0
        ans = 0
        for x in nums:
            if x == 0:
                pos, neg = 0, 0 # 重置
            elif x > 0:
                pos += 1
                neg = (neg + 1 if neg > 0 else 0)
            else: # x < 0
                # 状态交换
                new_pos = (neg + 1 if neg > 0 else 0)
                new_neg = pos + 1
                pos, neg = new_pos, new_neg
            ans = max(ans, pos)
        return ans
```

#### 5. 2786. 访问数组中的位置使分数最大

- **DP 定义**：
    
    - `f[0]`：以**偶数**结尾的最大得分。
        
    - `f[1]`：以**奇数**结尾的最大得分。
        
- **技巧**：**奇偶索引**。直接用 `x % 2` 作为数组下标来访问对应的状态。
    
- **空间优化代码**：
    

Python

```
class Solution:
    def maxScore(self, nums: List[int], x: int) -> int:
        # 初始化：因为必须从 nums[0] 开始
        f = [float('-inf')] * 2
        f[nums[0] % 2] = nums[0]
        
        for v in nums[1:]:
            r = v % 2
            # 转移：max(接同性，接异性-x)
            f[r] = max(f[r], f[1 - r] - x) + v
            
        return max(f)
```

#### 6. 1911. 最大交替子序列和

- **DP 定义**：
    
    - `even`：交替和中，最后一个操作是 **加** (下标偶) 的最大值。
        
    - `odd`：交替和中，最后一个操作是 **减** (下标奇) 的最大值。
        
- **技巧**：**买卖股票模型**。加法相当于“卖出/空仓”，减法相当于“买入/持有”。
    
- **空间优化代码**：
    

Python

```
class Solution:
    def maxAlternatingSum(self, nums: List[int]) -> int:
        even, odd = 0, 0
        for x in nums:
            # 想要变成加法结尾(even)：要么保持不变，要么从减法(odd)那边加过来
            new_even = max(even, odd + x)
            # 想要变成减法结尾(odd)：要么保持不变，要么从加法(even)那边减过来
            new_odd = max(odd, even - x)
            even, odd = new_even, new_odd
        return even
```

#### 7. 376. 摆动序列

- **DP 定义**：
    
    - `up`：以**上升**趋势 (Peak) 结尾的最长子序列长度。
        
    - `down`：以**下降**趋势 (Valley) 结尾的最长子序列长度。
        
- **技巧**：**贪心/几何折线**。只在趋势发生反转（形成拐点）时更新长度。
    
- **空间优化代码**：
    

Python

```
class Solution:
    def wiggleMaxLength(self, nums: List[int]) -> int:
        if len(nums) < 2: return len(nums)
        up, down = 1, 1
        for i in range(1, len(nums)):
            if nums[i] > nums[i-1]:
                up = down + 1   # 谷变峰
            elif nums[i] < nums[i-1]:
                down = up + 1   # 峰变谷
        return max(up, down)
```

---

### 三、 总结：常用技巧清单

1. **奇偶性状态 (Parity)**
    
    - 题目涉及 "奇偶"、"模2"、"不同组扣分"。
        
    - **模版**：`f[0], f[1]`，使用 `f[r]` 和 `f[1-r]` 进行转移。
        
    - _例题：2786_
        
2. **符号翻转状态 (Sign Flip)**
    
    - 题目涉及 "正负乘积"、"加减交替"。
        
    - **模版**：`pos/neg` 或 `odd/even` (加减)，负数时交换 `pos` 和 `neg`。
        
    - _例题：1567, 1911, 2708_
        
3. **峰谷趋势状态 (Trend)**
    
    - 题目涉及 "上升下降"、"波峰波谷"。
        
    - **模版**：`up/down`。趋势延续时不更新（或更新值不更新长度），趋势反转时 `+1`。
        
    - _例题：376_
        
4. **冷却期/间隔状态 (Gap/Cooldown)**
    
    - 题目涉及 "不能连续选"、"切换需要等待"。
        
    - **模版**：需要维护 `curr` (当前) 和 `prev` (上上轮) 两个维度的变量。
        
    - _例题：3259, 打家劫舍系列_
        
5. **前缀计数 (Prefix Counting)**
    
    - 题目涉及 "子序列计数"。
        
    - **模版**：`count_A`, `count_AB`, `count_ABC`。每一层依赖上一层的计数。
        
    - _例题：2222_