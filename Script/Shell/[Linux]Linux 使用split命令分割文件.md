---
layout: post
author: sjf0115
title: Linux 使用split命令分割文件
date: 2018-04-08 18:17:17
tags:
  - Linux
  - Linux 命令

categories: Linux
permalink: linux-split-file-usage
---

### 1. 概述

split　命令可以将一个大文件分割成很多个小文件。在默认情况下将按照每1000行切割成一个小文件，默认前缀为 `x`。没有输入或输入为 `-` 时，从标准输入中读取。

### 2. 语法：
```
split [OPTION]... [INPUT [PREFIX]]
```

### 3. 选项

```
-l : 指定每多少行切成一个小文件。
-b : 指定每多少字节切成一个小文件。
-C : 每一输出档中，单行的最大 byte 数。
-d ： 使用数字作为后缀。
```

### 4. 实例

#### 4.1 按行分割
```
xiaosi@ying:~/test/input$ split -6 a.txt
```
或者
```
xiaosi@ying:~/test/input$ split -l 6 a.txt
```
执行以上命令后，会将原来的大文件 a.txt 切割成多个以 `x` 开头的小文件。而在这些小文件中，每个文件都至多6行数据(最后一个文件有可能不满６行)。
```
xiaosi@ying:~/test/input$ ll
总用量 32
drwxrwxr-x 2 xiaosi xiaosi 4096  4月  8 18:19 ./
drwxrwxr-x 6 xiaosi xiaosi 4096  8月 24  2017 ../
-rw-rw-r-- 1 xiaosi xiaosi  924  4月  8 18:18 a.txt
-rw-rw-r-- 1 xiaosi xiaosi  198  4月  8 18:19 xaa
-rw-rw-r-- 1 xiaosi xiaosi  198  4月  8 18:19 xab
-rw-rw-r-- 1 xiaosi xiaosi  198  4月  8 18:19 xac
-rw-rw-r-- 1 xiaosi xiaosi  198  4月  8 18:19 xad
-rw-rw-r-- 1 xiaosi xiaosi  132  4月  8 18:19 xae
xiaosi@ying:~/test/input$ cat a.txt | wc -l
28
xiaosi@ying:~/test/input$ cat xae | wc -l
4
```

#### 4.2 按文件大小分割

```
xiaosi@ying:~/test/input$ split -b50M b.txt
```
执行以上命令后，会将原来的大文件 b.txt 切割成多个以 `x` 开头的小文件。而在这些小文件中，每个文件大小都为50M(最后一个文件有可能不满50M)。
```
xiaosi@ying:~/test/input$ ll
总用量 322296
drwxrwxr-x 2 xiaosi xiaosi      4096  4月  8 18:25 ./
drwxrwxr-x 6 xiaosi xiaosi      4096  8月 24  2017 ../
-rw-rw-r-- 1 xiaosi xiaosi       924  4月  8 18:18 a.txt
-rw-rw-r-- 1 xiaosi xiaosi 165000000  4月  8 11:53 b.txt
-rw-rw-r-- 1 xiaosi xiaosi  52428800  4月  8 18:25 xaa
-rw-rw-r-- 1 xiaosi xiaosi  52428800  4月  8 18:25 xab
-rw-rw-r-- 1 xiaosi xiaosi  52428800  4月  8 18:25 xac
-rw-rw-r-- 1 xiaosi xiaosi   7713600  4月  8 18:25 xad
```

#### 4.3 修改后缀

上述示例中，文件被分割成多个带有字母的后缀文件，如果想用数字后缀可使用 -d 参数，同时可以使用 -a <length> 来指定后缀的长度：
```
xiaosi@ying:~/test/input$ split -b50M b.txt -d -a 3
```
执行以上命令后，会将原来的大文件 b.txt 切割成多个以 `x` 开头后面为数字的小文件：
```
xiaosi@ying:~/test/input$ ll
总用量 322296
drwxrwxr-x 2 xiaosi xiaosi      4096  4月  8 18:36 ./
drwxrwxr-x 6 xiaosi xiaosi      4096  8月 24  2017 ../
-rw-rw-r-- 1 xiaosi xiaosi       924  4月  8 18:18 a.txt
-rw-rw-r-- 1 xiaosi xiaosi 165000000  4月  8 11:53 b.txt
-rw-rw-r-- 1 xiaosi xiaosi  52428800  4月  8 18:36 x000
-rw-rw-r-- 1 xiaosi xiaosi  52428800  4月  8 18:36 x001
-rw-rw-r-- 1 xiaosi xiaosi  52428800  4月  8 18:36 x002
-rw-rw-r-- 1 xiaosi xiaosi   7713600  4月  8 18:36 x003
```
#### 4.4 指定输出文件名前缀

```
xiaosi@ying:~/test/input$ split -b50M b.txt split_
```
执行以上命令后，会将原来的大文件 b.txt 切割成多个以 `split_` 开头的小文件：
```
xiaosi@ying:~/test/input$ ll
总用量 322296
drwxrwxr-x 2 xiaosi xiaosi      4096  4月  8 18:41 ./
drwxrwxr-x 6 xiaosi xiaosi      4096  8月 24  2017 ../
-rw-rw-r-- 1 xiaosi xiaosi       924  4月  8 18:18 a.txt
-rw-rw-r-- 1 xiaosi xiaosi 165000000  4月  8 11:53 b.txt
-rw-rw-r-- 1 xiaosi xiaosi  52428800  4月  8 18:41 split_aa
-rw-rw-r-- 1 xiaosi xiaosi  52428800  4月  8 18:41 split_ab
-rw-rw-r-- 1 xiaosi xiaosi  52428800  4月  8 18:41 split_ac
-rw-rw-r-- 1 xiaosi xiaosi   7713600  4月  8 18:41 split_ad
```
