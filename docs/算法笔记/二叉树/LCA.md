这几道题构成了 LeetCode 中 **LCA（最近公共祖先）** 系列的完整版图。我们可以将这些题目总结为三个核心模型。

---

## 🟢 二叉树 LCA 算法笔记总览

### 1. 通用核心思路

- **自底向上汇报**：利用**后序遍历**（Left -> Right -> Root），每个节点收集左右子树的“情报”，汇总后汇报给父节点。
    
- **返回值设计**：
    
    - 返回 `None`：代表子树中没发现目标。
        
    - 返回 `Node`：代表子树中发现了目标（或是已找到的 LCA）。
        
- **分类讨论**：
    
    - 若左右子树都返回了非空节点，当前节点就是 LCA。
        
    - 若只有一边返回非空，则继续向上回传该非空节点。
        

---

## 🔵 题目详解与代码实现

### 1. 基础型：已知节点求 LCA

#### [236] 二叉树的最近公共祖先

- **描述**：给定 $p, q$（保证在树中），求其 LCA。
    
- **思路**：最标准模型。遇到 $p, q$ 就返回，根据左右子树返回值判断。
    

Python

```
def lowestCommonAncestor(self, root, p, q):
    if not root or root == p or root == q: return root
    left = self.lowestCommonAncestor(root.left, p, q)
    right = self.lowestCommonAncestor(root.right, p, q)
    if left and right: return root
    return left or right
```

#### [1644] 二叉树的最近公共祖先 II (会员题)

- **描述**：$p$ 或 $q$ **可能不在树中**。
    
- **思路**：不能遇到 $p$ 就立刻返回，必须**遍历完整个子树**来计数。只有计数为 2 时才返回 LCA。
    

Python

```
class Solution:
    def lowestCommonAncestor(self, root, p, q):
        self.count = 0
        def dfs(node):
            if not node: return None
            # 注意：这里先搜左右，确保完整遍历
            left = dfs(node.left)
            right = dfs(node.right)
            if node == p or node == q:
                self.count += 1
                return node
            if left and right: return node
            return left or right
        
        res = dfs(root)
        return res if self.count == 2 else None
```

#### [1676] 二叉树的最近公共祖先 IV (会员题)

- **描述**：给定一个节点**集合** `nodes`，求这些所有节点的 LCA。
    
- **思路**：将 `p, q` 的逻辑扩展到集合。只要当前节点在集合中，它就可能是 LCA 的一部分。
    

Python

```
def lowestCommonAncestor(self, root, nodes):
    nodes_set = set(nodes)
    def dfs(node):
        if not node or node in nodes_set: return node
        left = dfs(node.left)
        right = dfs(node.right)
        if left and right: return node
        return left or right
    return dfs(root)
```

---

### 2. 特殊结构型

#### [235] 二叉搜索树的最近公共祖先

- **描述**：利用 BST 性质（左 < 根 < 右）。
    
- **思路**：不需要后序遍历，直接**自顶向下**。如果 $p, q$ 都比根小，往左走；都比根大，往右走；否则当前节点就是分叉点。
    

Python

```
def lowestCommonAncestor(self, root, p, q):
    while root:
        if p.val < root.val and q.val < root.val: root = root.left
        elif p.val > root.val and q.val > root.val: root = root.right
        else: return root
```

#### [1650] 二叉树的最近公共祖先 III (会员题)

- **描述**：每个节点有 `parent` 指针，不给 `root`。
    
- **思路**：这其实是**寻找两个链表的第一个交点**。让 $p$ 和 $q$ 分别向上走，走到头就交换起点，最终必会相遇。
    

Python

```
def lowestCommonAncestor(self, p, q):
    a, b = p, q
    while a != b:
        a = a.parent if a.parent else q
        b = b.parent if b.parent else p
    return a
```

---

### 3. 深度与距离型

#### [1123 / 865] 最深叶节点的最近公共祖先

- **描述**：求所有最深叶子节点的 LCA。
    
- **思路**：自底向上返回 `(深度, 该深度的 LCA)`。只有当左右子树高度相等时，当前节点才是暂时的 LCA。
    

Python

```
def lcaDeepestLeaves(self, root):
    def dfs(node):
        if not node: return 0, None
        d1, l_lca = dfs(node.left)
        d2, r_lca = dfs(node.right)
        if d1 > d2: return d1 + 1, l_lca
        if d2 > d1: return d2 + 1, r_lca
        return d1 + 1, node
    return dfs(root)[1]
```

#### [1740] 找到二叉树中的距离 (会员题)

- **思路**：距离公式 = $depth(p) + depth(q) - 2 \times depth(LCA(p, q))$。
    

1. 先用基础 LCA 算法找 $p, q$ 的共同祖先。
    
2. 再计算该祖先到 $p$ 和 $q$ 的距离之和。
    

#### [2096] 从二叉树一个节点到另一个节点的方向

- **思路**：
    
    1. 找到 LCA。
        
    2. 从 LCA 到 `startNode`：全是 'U'（向上）。
        
    3. 从 LCA 到 `destNode`：标准的 DFS 路径（'L' 或 'R'）。
        
    4. 拼接两者。
        

---

## 💡 总结技巧：如何一眼定思路？

1. **有 parent 指针吗？** 有就当成链表相交题（双指针）。
    
2. **是 BST 吗？** 是就自顶向下根据数值大小判断。
    
3. **找特定节点的 LCA？** 后序遍历，返回 $p, q$ 的状态。
    
4. **找最深叶子的 LCA？** 后序遍历，返回高度值。
    

你想让我针对其中哪道“会员题”写一个完整的带有测试用例的模拟运行流程吗？