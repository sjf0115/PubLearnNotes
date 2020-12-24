# -*- coding: UTF-8 -*-
# Numpy 数组操作

import numpy as np

# 简单数组
numbers = np.array(range(1, 11), copy=True)
print numbers  # [ 1  2  3  4  5  6  7  8  9 10]

# 给定数组形状shape与数据类型type 全1数组
ones = np.ones([2, 4], dtype=np.float64)
print ones
'''
[
  [ 1.  1.  1.  1.]
  [ 1.  1.  1.  1.]
]
'''

# 给定数组形状shape与数据类型type 全0数组
zeros = np.zeros([2, 4], dtype=np.float64)
print zeros
'''
[
  [ 0.  0.  0.  0.]
  [ 0.  0.  0.  0.]
]
'''

# 给定数组形状shape与数据类型type 尚未初始化数组 其元素值不一定为零
empty = np.empty([2, 4], dtype=np.float64)
print empty
'''
[
  [ 1.  1.  1.  1.]
  [ 1.  1.  1.  1.]
]
'''

# 只要没有经过变形(reshape) 该属性给出的就是数组的原始形状
print ones.shape  # (2, 4)

# 等价于len(numbers.shape)
print ones.ndim  # 2

# 数据类型
print ones.dtype  # float64

# N×M的眼形单位矩阵
eye = np.eye(3, k=1)
print eye
'''
[
 [ 0.  1.  0.]
 [ 0.  0.  1.]
 [ 0.  0.  0.]
]
'''

# 等间隔数值数组
double_numbers = np.arange(2, 5, 0.25)
print double_numbers  # [ 2.    2.25  2.5   2.75  3.    3.25  3.5   3.75  4.    4.25  4.5   4.75]

# 改变数组数据类型
int_numbers = double_numbers.astype(np.int)
print int_numbers  # [2 2 2 2 3 3 3 3 4 4 4 4]










































