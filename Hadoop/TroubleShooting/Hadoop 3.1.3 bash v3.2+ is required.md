## 1. 问题

运行 `start-dfs.sh` 命令启动 HDFS 时，遇到如下异常：
```
smartsi@192 hadoop % . sbin/start-dfs.sh
bash v3.2+ is required. Sorry.
```

## 2. 分析

第一步‌检查当前 Shell 环境，执行 `echo $SHELL` 命令查看当前使用的 Shell 类型：
```
smartsi@192 hadoop % echo $SHELL
/bin/zsh
```
若类型为 `zsh` 或者其他非 `bash shell`，需要‌切换至 `bash shell`
```
chsh -s /bin/bash
```

切换完成需要重启才能生效，重启之后验证：
```
192:~ smartsi$ echo $SHELL
/bin/bash
```

执行 `bash --version` 确认版本号：
```
192:~ smartsi$ bash --version
GNU bash, version 3.2.57(1)-release (arm64-apple-darwin23)
Copyright (C) 2007 Free Software Foundation, Inc.
```
重新运行 `start-dfs.sh` 命令启动 HDFS：
```

```
