## 1. 查询 UUID

```
diskutil info /Volumes/{你的移动硬盘名称} | grep UUID
```
输出如下结果:
```
Volume UUID:              xxx
```

## 2.

```
echo "UUID=xxx none ntfs rw,auto,nobrowse" | sudo tee -a /etc/fstab
```


参考：https://www.youtube.com/watch?v=j5AedYxk90E
