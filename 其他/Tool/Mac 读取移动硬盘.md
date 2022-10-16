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

## 3. 查找

访达->显示隐藏文件(command + shift + .)->

磁盘工具 -> 磁盘 -> 在访达中显示



参考：https://www.youtube.com/watch?v=j5AedYxk90E
