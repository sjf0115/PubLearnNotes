### 1. 查看标签
列出现有标签,使用如下命令：
```
xiaosi@yoona:~/code/learningnotes$ git tag
r-000000-000000-cm.cm
v1.0.0
v1.0.1

```
我们可以用特定的搜索模式列出符合条件的标签。如果只对1.0系列的版本感兴趣，可以运行如下命令：
```
xiaosi@yoona:~/code/learningnotes$ git tag -l 'v1.0.*'
v1.0.0
v1.0.1
```

### 2. 创建标签

Git 使用的标签有两种类型：轻量级的（lightweight）和含附注的（annotated）。
- 轻量级标签就像是个不会变化的分支，实际上它就是个指向特定提交对象的引用。
- 含附注标签，实际上是存储在仓库中的一个独立对象，它有自身的校验和信息，包含着标签的名字，电子邮件地址和日期，以及标签说明，标签本身也允许使用 GNU Privacy Guard (GPG) 来签署或验证。

一般我们都建议使用含附注型的标签，以便保留相关信息；当然，如果只是临时性加注标签，或者不需要旁注额外信息，用轻量级标签也没问题。

#### 2.1 含附注的标签

使用如下命令创建一个含附注类型标签：
```
xiaosi@yoona:~/code/learningnotes$ git tag -a v1.0.2 -m "version 1.0.2"
xiaosi@yoona:~/code/learningnotes$ git tag
r-000000-000000-cm.cm
v1.0.0
v1.0.1
v1.0.2
```
**备注**

- -a （取 `annotated` 的首字母）指定标签名字
- -m 选项指定了对应的标签说明，Git 会将此说明一同保存在标签对象中。如果没有给出该选项，Git 会启动文本编辑软件供你输入标签说明。

可以使用 `git show` 命令查看相应标签的版本信息，并连同显示打标签时的提交对象:
```
xiaosi@yoona:~/code/learningnotes$ git show v1.0.2
tag v1.0.2
Tagger: yoona <yoona@qq.com>
Date:   Tue Jul 25 14:14:26 2017 +0800

version 1.0.2

commit 2274f5e988b9300d9103a6be230d19ee945ff575
Author: xiaosi <xiaosi@qq.com>
Date:   Tue Jul 25 13:39:29 2017 +0800

    MOD
    ...
```

#### 2.2 轻量级标签

轻量级标签实际上就是一个保存着对应提交对象的校验和信息的文件。要创建这样的标签，`-a`，`-s` 或 `-m` 选项都不用，直接给出标签名字即可：
```
xiaosi@yoona:~/code/learningnotes$ git tag v1.0.3
xiaosi@yoona:~/code/learningnotes$ git tag
r-000000-000000-cm.cm
v1.0.0
v1.0.1
v1.0.2
v1.0.3
```
现在运行 `git show` 查看此标签信息，就只有相应的提交对象摘要：
```
xiaosi@yoona:~/code/learningnotes$ git show v1.0.3
commit 2274f5e988b9300d9103a6be230d19ee945ff575
Author: xiaosi <xiaosi@qq.com>
Date:   Tue Jul 25 13:39:29 2017 +0800

    MOD
    ...
```

### 3. 分享标签

默认情况下，git push 并不会把标签传送到远端服务器上，只有通过显式命令才能分享标签到远端仓库。其命令格式如同推送分支，运行 `git push origin [tagname]` 即可：
```
xiaosi@yoona:~/code/learningnotes$ git push origin v1.0.0
对象计数中: 1, 完成.
写入对象中: 100% (1/1), 162 bytes | 0 bytes/s, 完成.
Total 1 (delta 0), reused 0 (delta 0)
To git@github.com:yoona/learningnotes.git
 * [new tag]         v1.0.0 -> v1.0.0
```
如果要一次推送所有本地新增的标签上去，可以使用 --tags 选项：
```
xiaosi@yoona:~/code/learningnotes$ git push origin --tags
对象计数中: 3, 完成.
Delta compression using up to 4 threads.
压缩对象中: 100% (3/3), 完成.
写入对象中: 100% (3/3), 258 bytes | 0 bytes/s, 完成.
Total 3 (delta 2), reused 0 (delta 0)
To git@github.com:xiaosi/learningnotes.git
 * [new tag]         v1.0.1 -> v1.0.1
 * [new tag]         v1.0.2 -> v1.0.2
 * [new tag]         v1.0.3 -> v1.0.3
```
### 4. 删除标签

#### 4.1 删除本地标签

如果本地标签打错了，还没有推送到服务器端，也可以使用如下命令删除标签：
```
xiaosi@yoona:~/code/learningnotes$ git tag -d v1.0.4
已删除 tag 'v1.0.4'（曾为 2274f5e）
```
因为创建的标签都只存储在本地，不会自动推送到远程。所以，打错的标签可以在本地安全删除。

#### 4.2 删除远程标签

如果标签已经推送到远程，要删除远程标签就麻烦一点，先从本地删除：
```
xiaosi@yoona:~/code/learningnotes$ git tag -d v1.0.0
已删除 tag 'v1.0.0'（曾为 ddecd72）
```
然后再从远程删除：
##### 4.2.1 在Git v1.7.0版本之后如下操作
```
xiaosi@yoona:~/code/learningnotes$ git push origin --delete v1.0.0
To git@github.com:xiaosi/learningnotes.git
 - [deleted]         v1.0.0
```
##### 4.2.2 在Git v1.7.0版本之前如下操作
```
xiaosi@yoona:~/code/learningnotes$ git push origin :refs/tags/v1.0.0
To git@github.com:xiaosi/learningnotes.git
 - [deleted]         v1.0.0
```


参考：https://git-scm.com/book/zh/v1/Git-%E5%9F%BA%E7%A1%80-%E6%89%93%E6%A0%87%E7%AD%BE
