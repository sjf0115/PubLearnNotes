https://www.php.cn/tool/git/467610.html

```
git branch --delete release-1.16
```

```
localhost:flink wy$ git branch --delete release-1.16
error: The branch 'release-1.16' is not fully merged.
If you are sure you want to delete it, run 'git branch -D release-1.16'.
```


```
git push origin --delete release-1.16
```

```
localhost:flink wy$ git push origin --delete release-1.16
To github.com:sjf0115/flink.git
 - [deleted]                 release-1.16
```
