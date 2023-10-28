
```
git remote add github git@github.com:sjf0115/spi-example.git
git remote add gitee git@gitee.com:sjf0115/spi-example.git
```


```
[core]
        repositoryformatversion = 0
        filemode = true
        bare = false
        logallrefupdates = true
        ignorecase = true
        precomposeunicode = true
[remote "origin"]
        # github
        url = git@github.com:sjf0115/spi-example.git
        fetch = +refs/heads/*:refs/remotes/origin/*
```

```
[core]
        repositoryformatversion = 0
        filemode = true
        bare = false
        logallrefupdates = true
        ignorecase = true
        precomposeunicode = true
[remote "origin"]
        # github
        url = git@github.com:sjf0115/spi-example.git
        fetch = +refs/heads/*:refs/remotes/origin/*
        # gitee
        url = https://gitee.com/sjf0115/spi-example.git
```


```
localhost:spi-example wy$ git remote -v
origin  git@github.com:sjf0115/spi-example.git (fetch)
origin  git@github.com:sjf0115/spi-example.git (push)
origin  https://gitee.com/sjf0115/spi-example.git (push)
```
