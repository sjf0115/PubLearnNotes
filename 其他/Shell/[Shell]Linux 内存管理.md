当在Linux下频繁存取文件后，物理内存会很快被用光，当程序结束后，内存不会被正常释放，而是一直作为caching。这个问题，貌似有不少人在问，不过都没有看到有什么很好解决的办法。那么我来谈谈这个问题。

### 1. free命令
```
ubuntu@VM-0-7-ubuntu:~$ free -m
             total       used       free     shared    buffers     cached
Mem:        129088     109597      19491          0       1136      95839
-/+ buffers/cache:      12620     116467
Swap:        49151          0      49151
```

参数|说明
---|---
total|内存总数
used|已经使用的内存数
free|空闲的内存数
shared|多个进程共享的内存总额

buffers Buffer Cache和cached Page Cache 磁盘缓存的大小
-buffers/cache (已用)的内存数:used - buffers - cached
+buffers/cache(可用)的内存数:free + buffers + cached
可用的memory=free memory+buffers+cached
