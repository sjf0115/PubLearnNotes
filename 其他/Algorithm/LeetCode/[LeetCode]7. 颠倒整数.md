---
layout: post
author: sjf0115
title: 7. 颠倒整数
date: 2017-03-21 00:00:07
tags:
  - LeetCode

categories: LeetCode
permalink: leetcode-reverse-integer
---

### 1. 题目描述

给定一个范围为 32 位 int 的整数，将其颠倒。

例 1:
```
输入: 123
输出:  321
```

例 2:
```
输入: -123
输出: -321
```

例 3:
```
输入: 120
输出: 21
```
> 注意： 假设我们的环境只能处理 32 位 int 范围内的整数。根据这个假设，如果颠倒后的结果超过这个范围，则返回 0。

### 2. 解决方案

```java
public int reverse(int x) {

    long result = 0;
    int tmp = Math.abs(x);
    while(tmp > 0){
        result = result * 10 + tmp % 10;
        if(result > Integer.MAX_VALUE){
            return 0;
        }
        tmp = tmp / 10;
    }
    return (int)(x > 0 ? result : -result);

}
```

```java
public int reverse(int x) {

    if(x == 0){
        return x;
    }
    long n = x;
    boolean isNegative = false;
    if (x < 0){
        isNegative = true;
        n = -1 * (long)x;
    }
    long result = 0;
    while(n != 0){
        result = result * 10 + n % 10;
        n = n / 10;
    }
    if(isNegative){
        result = -1 * result;
        if(result <= Integer.MIN_VALUE){
            return 0;
        }
        return (int)result;
    }
    else {
        if(result >= Integer.MAX_VALUE){
            return 0;
        }
        return (int)result;
    }

}
```

题目地址：https://leetcode-cn.com/problems/reverse-integer/description/
