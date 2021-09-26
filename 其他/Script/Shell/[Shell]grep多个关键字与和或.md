### 1. 或操作
找出文件中包含entrance=301或者entrance=303的行

使用grep方式实现：
```
grep -E 'entrance=301|entrance=303' fileName
grep -E 'entrance=(301|303)' fileName
```
使用egrep方式实现：
```
egrep 'entrance=301|entrance=303' fileName
```
使用awk方式实现：
```
awk '/entrance=301|entrance=303/' fileName     
```

### 2. 与操作

```
grep command1 | grep command2 
```