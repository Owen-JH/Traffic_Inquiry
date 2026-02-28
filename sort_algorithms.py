# Quick Sort
def quick_sort(arr):
    if len(arr) <= 1:
        return arr
    pivot = arr[len(arr) // 2]
    left = [x for x in arr if x < pivot]
    mid = [x for x in arr if x == pivot]
    right = [x for x in arr if x > pivot]
    return quick_sort(left) + mid + quick_sort(right)


# Merge Sort
def merge_sort(arr):
    if len(arr) <= 1:
        return arr
    mid = len(arr) // 2
    left = merge_sort(arr[:mid])
    right = merge_sort(arr[mid:])
    return merge(left, right)


def merge(left, right):
    result = []
    i = j = 0
    while i < len(left) and j < len(right):
        if left[i] <= right[j]:
            result.append(left[i])
            i += 1
        else:
            result.append(right[j])
            j += 1
    result.extend(left[i:])
    result.extend(right[j:])
    return result


# Heap Sort
def heap_sort(arr):
    import heapq
    h = []
    for v in arr:
        heapq.heappush(h, v)
    return [heapq.heappop(h) for _ in range(len(h))]


# Shell Sort
def shell_sort(arr):
    n = len(arr)
    gap = n // 2
    arr = list(arr)
    while gap > 0:
        for i in range(gap, n):
            temp = arr[i]
            j = i
            while j >= gap and arr[j - gap] > temp:
                arr[j] = arr[j - gap]
                j -= gap
            arr[j] = temp
        gap //= 2
    return arr


# AVL Tree Sort
class AVLNode:
    def __init__(self, val):
        self.val = val
        self.left = None
        self.right = None
        self.height = 1


def avl_height(node):
    return node.height if node else 0


def avl_update(node):
    node.height = 1 + max(avl_height(node.left), avl_height(node.right))


def avl_rotate_right(y):
    x = y.left
    T2 = x.right
    x.right = y
    y.left = T2
    avl_update(y)
    avl_update(x)
    return x


def avl_rotate_left(x):
    y = x.right
    T2 = y.left
    y.left = x
    x.right = T2
    avl_update(x)
    avl_update(y)
    return y


def avl_balance(node):
    balance = avl_height(node.left) - avl_height(node.right)
    if balance > 1:
        if avl_height(node.left.left) < avl_height(node.left.right):
            node.left = avl_rotate_left(node.left)
        return avl_rotate_right(node)
    if balance < -1:
        if avl_height(node.right.right) < avl_height(node.right.left):
            node.right = avl_rotate_right(node.right)
        return avl_rotate_left(node)
    return node


def avl_insert(root, val):
    if not root:
        return AVLNode(val)
    if val < root.val:
        root.left = avl_insert(root.left, val)
    else:
        root.right = avl_insert(root.right, val)
    avl_update(root)
    return avl_balance(root)


def avl_inorder(root, arr):
    if not root:
        return
    avl_inorder(root.left, arr)
    arr.append(root.val)
    avl_inorder(root.right, arr)


def avl_sort(arr):
    root = None
    for v in arr:
        root = avl_insert(root, v)
    result = []
    avl_inorder(root, result)
    return result


# Red-Black Tree Sort
RED = True
BLACK = False


class RBNode:
    def __init__(self, key, color=RED, left=None, right=None, parent=None):
        self.key = key
        self.color = color
        self.left = left
        self.right = right
        self.parent = parent



class RBTree:
    def __init__(self):
        # 统一的 NIL 哨兵节点（所有空孩子都是它）
        self.NIL = RBNode(key=None, color=BLACK)
        self.root = self.NIL

    # ========== 公共接口 ==========

    def insert(self, key):
        """插入一个 key 到红黑树中"""
        node = RBNode(key=key, color=RED, left=self.NIL, right=self.NIL)
        self._bst_insert(node)
        self._fix_insert(node)

    def search(self, key):
        """返回 key 对应的节点，找不到则返回 None"""
        x = self.root
        while x != self.NIL:
            if key == x.key:
                return x
            elif key < x.key:
                x = x.left
            else:
                x = x.right
        return None

    def delete(self, key):
        """删除值为 key 的节点，如果不存在就什么也不做"""
        z = self.search(key)
        if z is None:
            return
        self._delete_node(z)

    def inorder(self):
        """中序遍历，返回所有 key 的有序列表"""
        result = []
        self._inorder(self.root, result)
        return result

    # ========== 内部辅助函数（BST 插入 / 遍历） ==========

    def _bst_insert(self, z):
        """普通 BST 插入，不考虑颜色修复"""
        y = self.NIL
        x = self.root
        while x != self.NIL:
            y = x
            if z.key < x.key:
                x = x.left
            else:
                x = x.right
        z.parent = y

        if y == self.NIL:
            self.root = z
        elif z.key < y.key:
            y.left = z
        else:
            y.right = z

    def _inorder(self, node, result):
        if node == self.NIL:
            return
        self._inorder(node.left, result)
        result.append(node.key)
        self._inorder(node.right, result)

    # ========== 旋转操作 ==========

    def _left_rotate(self, x):
        y = x.right
        x.right = y.left
        if y.left != self.NIL:
            y.left.parent = x

        y.parent = x.parent
        if x.parent == self.NIL:
            self.root = y
        elif x == x.parent.left:
            x.parent.left = y
        else:
            x.parent.right = y

        y.left = x
        x.parent = y

    def _right_rotate(self, y):
        x = y.left
        y.left = x.right
        if x.right != self.NIL:
            x.right.parent = y

        x.parent = y.parent
        if y.parent == self.NIL:
            self.root = x
        elif y == y.parent.right:
            y.parent.right = x
        else:
            y.parent.left = x

        x.right = y
        y.parent = x

    # ========== 插入修复 ==========

    def _fix_insert(self, z):
        """插入后修复红黑树性质"""
        while z.parent.color == RED:
            if z.parent == z.parent.parent.left:
                y = z.parent.parent.right  # 叔叔
                if y.color == RED:
                    # Case 1: 叔叔是红色
                    z.parent.color = BLACK
                    y.color = BLACK
                    z.parent.parent.color = RED
                    z = z.parent.parent
                else:
                    # 叔叔是黑色
                    if z == z.parent.right:
                        # Case 2: z 是右孩子 -> 左旋变成 Case 3
                        z = z.parent
                        self._left_rotate(z)
                    # Case 3
                    z.parent.color = BLACK
                    z.parent.parent.color = RED
                    self._right_rotate(z.parent.parent)
            else:
                # 和上面完全对称（左右互换）
                y = z.parent.parent.left
                if y.color == RED:
                    z.parent.color = BLACK
                    y.color = BLACK
                    z.parent.parent.color = RED
                    z = z.parent.parent
                else:
                    if z == z.parent.left:
                        z = z.parent
                        self._right_rotate(z)
                    z.parent.color = BLACK
                    z.parent.parent.color = RED
                    self._left_rotate(z.parent.parent)

            if z == self.root:
                break

        self.root.color = BLACK

    # ========== 删除相关 ==========

    def _transplant(self, u, v):
        """用子树 v 替换子树 u（u 的父指针也会更新）"""
        if u.parent == self.NIL:
            self.root = v
        elif u == u.parent.left:
            u.parent.left = v
        else:
            u.parent.right = v
        v.parent = u.parent

    def _minimum(self, x):
        """返回以 x 为根的子树中的最小节点"""
        while x.left != self.NIL:
            x = x.left
        return x

    def _delete_node(self, z):
        """按 CLRS 方式删除节点 z 并做修复"""
        y = z
        y_original_color = y.color
        if z.left == self.NIL:
            x = z.right
            self._transplant(z, z.right)
        elif z.right == self.NIL:
            x = z.left
            self._transplant(z, z.left)
        else:
            y = self._minimum(z.right)
            y_original_color = y.color
            x = y.right
            if y.parent == z:
                x.parent = y
            else:
                self._transplant(y, y.right)
                y.right = z.right
                y.right.parent = y

            self._transplant(z, y)
            y.left = z.left
            y.left.parent = y
            y.color = z.color

        if y_original_color == BLACK:
            self._fix_delete(x)

    def _fix_delete(self, x):
        """删除后修复红黑树性质"""
        while x != self.root and x.color == BLACK:
            if x == x.parent.left:
                w = x.parent.right  # 兄弟
                if w.color == RED:
                    # Case 1
                    w.color = BLACK
                    x.parent.color = RED
                    self._left_rotate(x.parent)
                    w = x.parent.right
                # Case 2
                if w.left.color == BLACK and w.right.color == BLACK:
                    w.color = RED
                    x = x.parent
                else:
                    # Case 3
                    if w.right.color == BLACK:
                        w.left.color = BLACK
                        w.color = RED
                        self._right_rotate(w)
                        w = x.parent.right
                    # Case 4
                    w.color = x.parent.color
                    x.parent.color = BLACK
                    w.right.color = BLACK
                    self._left_rotate(x.parent)
                    x = self.root
            else:
                # 和上面对称（左右互换）
                w = x.parent.left
                if w.color == RED:
                    # Case 1
                    w.color = BLACK
                    x.parent.color = RED
                    self._right_rotate(x.parent)
                    w = x.parent.left
                # Case 2
                if w.right.color == BLACK and w.left.color == BLACK:
                    w.color = RED
                    x = x.parent
                else:
                    # Case 3
                    if w.left.color == BLACK:
                        w.right.color = BLACK
                        w.color = RED
                        self._left_rotate(w)
                        w = x.parent.left
                    # Case 4
                    w.color = x.parent.color
                    x.parent.color = BLACK
                    w.left.color = BLACK
                    self._right_rotate(x.parent)
                    x = self.root

        x.color = BLACK

def rbt_sort(arr):
    tree = RBTree()
    for v in arr:
        tree.insert(v)
    return tree.inorder()


# 总接口：sort_array
def sort_array(arr, algorithm="Quick Sort"):

    if algorithm == "Quick Sort":
        return quick_sort(list(arr))

    elif algorithm == "Merge Sort":
        return merge_sort(list(arr))

    elif algorithm == "Heap Sort":
        return heap_sort(list(arr))

    elif algorithm == "Shell Sort":
        return shell_sort(list(arr))

    elif algorithm == "AVL Sort":
        return avl_sort(list(arr))

    elif algorithm == "RBT Sort":
        return rbt_sort(list(arr))

    else:
        raise ValueError(f"Unknown sorting algorithm: {algorithm}")