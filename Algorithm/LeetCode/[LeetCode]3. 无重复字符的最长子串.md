---
layout: post
author: sjf0115
title: 3. 无重复字符的最长子串
date: 2017-03-21 00:00:03
tags:
  - LeetCode

categories: LeetCode
permalink: leetcode-longest-substring-without-repeating-characters
---

### 1. 题目描述

给定一个字符串，找出不含有重复字符的最长子串的长度。

示例：

给定 "abcabcbb" ，没有重复字符的最长子串是 "abc" ，那么长度就是3。

给定 "bbbbb" ，最长的子串就是 "b" ，长度是1。

给定 "pwwkew" ，最长子串是 "wke" ，长度是3。请注意答案必须是一个子串，"pwke" 是 子序列  而不是子串。

### 2. 解决方案

```java
public int lengthOfLongestSubstring(String s) {
        int maxLen = 0;
        int n = s.length();
        if(n == 0){
            return maxLen;
        }
        Map<Character, Integer> locationMap = new HashMap<>();
        int start = 0;
        int end = 0;
        while (end < n){
            char c = s.charAt(end);
            if(locationMap.containsKey(c)){
                start = Math.max(locationMap.get(c) + 1, start);
            }
            int curLen = end - start + 1;
            if(curLen > maxLen){
                maxLen = curLen;
            }
            locationMap.put(c, end);
            end++;
        }
        return maxLen;
    }
```

```c++
int lengthOfLongestSubstring(string s) {
        int len = s.length();
        if(len <= 1){
            return len;
        }//if
        // 记录上次出现的位置
        int last[256];
        // 初始化
        memset(last,-1,sizeof(last));
        // 计算
        int max = 0,cur = 0,start = 0;
        for(int i = 0;i < len;++i){
            int pos = (int)s[i];
            // 有元素和该元素重复
            if(last[pos] >= start){// not last[pos] >= 0
                // 更新长度
                cur = cur - (last[pos] - start);
                // 更新起点
                start = last[pos] + 1;
            }//if
            else{
                ++cur;
            }
            // 更新字符位置
            last[pos] = i;
            if(cur > max){
                max =cur;
            }//if
        }//for
        return max;
    }
```




题目地址：https://leetcode-cn.com/problems/longest-substring-without-repeating-characters/description/
