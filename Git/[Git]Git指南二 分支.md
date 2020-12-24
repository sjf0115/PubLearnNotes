### 1. 查看远程分支

分支加上-a参数可以查看远程分支，远程分支会用红色表示出来:
```
xiaosi@yoona:~/code/qtown-score$ git branch -a
  FRESH-1606_qscore-20160503
* dev
  master
  remotes/origin/20151225-qtown-score-FRESH-1236
  remotes/origin/2016-2qtscore
  remotes/origin/FRESH-1606_qscore-20160503
  remotes/origin/HEAD -> origin/master
  remotes/origin/dev
  remotes/origin/master
```  
### 2. 删除远程分支

#### 2.1 在Git v1.7.0之后

删除远程分支：
```
git push origin --delete <branchName>
```

#### 2.2 在Git v1.7.0之前

删除远程分支（推送一个空分支到远程分支，其实相当于删除远程分支）：
```
git push origin :<branchName>
```
删除远程Tag（推送一个空tag到远程tag，其实相当于删除远程tag）：
```
git tag -d <tagname>
git push origin :refs/tags/<tagname>
```
### 3. 重命名远程分支
在Git中重命名远程分支，其实就是先删除远程分支，然后重命名本地分支，再重新提交一个远程分支。
```
xiaosi@yoona:~/code/qt$ git branch -av
* dev                                            8d807de MOD
  master                                         f600e50 code change during build
  remotes/origin/HEAD                            -> origin/master
  remotes/origin/dev                             8d807de MOD
  remotes/origin/master                          f600e50 code change during build
```  
删除远程分支：
```
git push --delete origin dev
```
重命名本地分支：
```
git branch -m dev develop
```
推送本地分支：
```
git push origin develop
```

### 4. 删除本地分支

删除本地分支可以使用如下命令：
```
git branch -D <branchName>
```
如下删除test分支:
```
xiaosi@yoona:~/code$ git branch -D test
```

**备注**

不能删除当前所在的那个分支，否则报错`error: 无法删除您当前所在的分支`
