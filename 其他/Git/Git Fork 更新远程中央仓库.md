
```
localhost:flink wy$ git branch -a
* master
  remotes/origin/FLINK-19449
  remotes/origin/HEAD -> origin/master
  remotes/origin/benchmark-request
  remotes/origin/blink
  remotes/origin/cron-master-dependency_check
  remotes/origin/cron-master-maven_compat
  remotes/origin/dependabot/maven/flink-end-to-end-tests/flink-glue-schema-registry-avro-test/io.netty-netty-codec-http-4.1.71.Final
  remotes/origin/dependabot/maven/flink-end-to-end-tests/flink-glue-schema-registry-json-test/io.netty-netty-codec-http-4.1.71.Final
  remotes/origin/dependabot/maven/flink-formats/flink-json-glue-schema-registry/io.netty-netty-codec-http-4.1.71.Final
  remotes/origin/dependabot/npm_and_yarn/flink-runtime-web/web-dashboard/minimist-1.2.6
  remotes/origin/docs_experimental__docs
  remotes/origin/docs_experimental__docs_compile
  remotes/origin/exp_github_actions
  remotes/origin/experiment_gha_docs
  remotes/origin/master
  ...
  remotes/origin/release-1.1
  remotes/origin/release-1.1.0-rc1
  remotes/origin/release-1.1.0-rc2
  remotes/origin/release-1.1.1-rc1
  remotes/origin/release-1.1.2-rc1
  remotes/origin/release-1.1.3-rc1
  remotes/origin/release-1.1.3-rc2
  remotes/origin/release-1.1.4-rc1
  remotes/origin/release-1.1.4-rc2
```
给 fork 添加源库的 clone 地址：
```
git remote add src-flink https://github.com/apache/flink.git
```

## 2. 同步 Tag

```
# 获取源项目的 tag
git fetch src-flink --tags  
```
输出如下信息：
```
localhost:flink wy$ git fetch src-flink --tags
remote: Enumerating objects: 8031, done.
remote: Counting objects: 100% (2577/2577), done.
remote: Compressing objects: 100% (5/5), done.
remote: Total 8031 (delta 2574), reused 2572 (delta 2572), pack-reused 5454
Receiving objects: 100% (8031/8031), 2.41 MiB | 493.00 KiB/s, done.
Resolving deltas: 100% (3213/3213), completed with 852 local objects.
From https://github.com/apache/flink
 * [new branch]              28733                  -> src-flink/28733
 * [new branch]              FLINK-19449            -> src-flink/FLINK-19449
 * [new branch]              benchmark-request      -> src-flink/benchmark-request
 * [new branch]              blink                  -> src-flink/blink
 ...
 * [new branch]              release-1.4            -> src-flink/release-1.4
 * [new branch]              release-1.5            -> src-flink/release-1.5
 * [new branch]              release-1.6            -> src-flink/release-1.6
 * [new branch]              release-1.7            -> src-flink/release-1.7
 * [new branch]              release-1.8            -> src-flink/release-1.8
 * [new branch]              release-1.9            -> src-flink/release-1.9
...
 * [new tag]                 release-1.14.5         -> release-1.14.5
 * [new tag]                 release-1.14.5-rc1     -> release-1.14.5-rc1
 * [new tag]                 release-1.14.6         -> release-1.14.6
 * [new tag]                 release-1.14.6-rc1     -> release-1.14.6-rc1
 * [new tag]                 release-1.14.6-rc2     -> release-1.14.6-rc2
 * [new tag]                 release-1.15.1         -> release-1.15.1
 * [new tag]                 release-1.15.1-rc1     -> release-1.15.1-rc1
 * [new tag]                 release-1.15.2         -> release-1.15.2
 * [new tag]                 release-1.15.2-rc1     -> release-1.15.2-rc1
 * [new tag]                 release-1.15.2-rc2     -> release-1.15.2-rc2
 * [new tag]                 release-1.16.0-rc0     -> release-1.16.0-rc0
 * [new tag]                 release-1.16.0-rc1     -> release-1.16.0-rc1
```

```
# 将新的 tag 推送到 fork 项目
git push --tags  
```
输出如下信息：
```
localhost:flink wy$ git push --tags
Counting objects: 1693, done.
Delta compression using up to 4 threads.
Compressing objects: 100% (939/939), done.
Writing objects: 100% (1693/1693), 509.50 KiB | 36.39 MiB/s, done.
Total 1693 (delta 839), reused 1595 (delta 748)
remote: Resolving deltas: 100% (839/839), completed with 82 local objects.
To github.com:sjf0115/flink.git
 * [new tag]                 release-1.14.5 -> release-1.14.5
 * [new tag]                 release-1.14.5-rc1 -> release-1.14.5-rc1
...
 * [new tag]                 release-1.16.0-rc0 -> release-1.16.0-rc0
 * [new tag]                 release-1.16.0-rc1 -> release-1.16.0-rc1
```

```
git push --branchs
```

## 3. Branch 同步

### 3.1 已 fork 的分支同步

### 3.2 未 fork 的分支同步

因为要同步的分支在 origin 不存在，所以需要在 fork 的项目(origin)建一个新的分支，最好是新建一个空的分支。如下所示，创建新建一个空分支 release-1.16，然后推送到 fork 仓库：
```
git commit --allow-empty -m "initial commit"
git push origin HEAD:refs/heads/release-1.16       
git branch -a
```
输出如下信息：
```
localhost:flink wy$ git commit --allow-empty -m "initial commit"
[master 0315c37e9c3] initial commit
localhost:flink wy$ git push origin HEAD:refs/heads/release-1.16
Counting objects: 1, done.
Writing objects: 100% (1/1), 178 bytes | 178.00 KiB/s, done.
Total 1 (delta 0), reused 0 (delta 0)
remote:
remote: Create a pull request for 'release-1.16' on GitHub by visiting:
remote:      https://github.com/sjf0115/flink/pull/new/release-1.16
remote:
To github.com:sjf0115/flink.git
 * [new branch]              HEAD -> release-1.16
```
切换到新分支 release-1.16：
```
git checkout -b release-1.16 origin/release-1.16
git branch -a
```
拉取源项目未fork的分支(这里以cassandra-new举个例子哈)
```
git pull src-flink release-1.16 –allow-unrelated-histories
git push origin release-1.16                #推送到空分支
```


参考：
- https://blog.csdn.net/limingjian/article/details/42749355
- http://www.qtcn.org/bbs/read-htm-tid-53628.html
