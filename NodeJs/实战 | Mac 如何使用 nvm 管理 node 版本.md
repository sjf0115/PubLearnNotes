## 1. 安装 nvm

在这使用 homebrew 安装 nvm：
```
smarsi:opt smartsi$ brew install nvm
==> Auto-updating Homebrew...
Adjust how often this is run with `$HOMEBREW_AUTO_UPDATE_SECS` or disable with
`$HOMEBREW_NO_AUTO_UPDATE=1`. Hide these hints with `$HOMEBREW_NO_ENV_HINTS=1` (see `man brew`).
==> Fetching downloads for: nvm
==> Fetching nvm
==> Downloading https://mirrors.aliyun.com/homebrew/homebrew-bottles/nvm-0.40.3.all.bottle.tar.gz
############################################################################################################################################################ 100.0%
==> Pouring nvm-0.40.3.all.bottle.tar.gz
==> Caveats
Please note that upstream has asked us to make explicit managing
nvm via Homebrew is unsupported by them and you should check any
problems against the standard nvm install method prior to reporting.

You should create NVM's working directory if it doesn't exist:
  mkdir ~/.nvm

Add the following to your shell profile e.g. ~/.profile or ~/.zshrc:
  export NVM_DIR="$HOME/.nvm"
  [ -s "/opt/homebrew/opt/nvm/nvm.sh" ] && \. "/opt/homebrew/opt/nvm/nvm.sh"  # This loads nvm
  [ -s "/opt/homebrew/opt/nvm/etc/bash_completion.d/nvm" ] && \. "/opt/homebrew/opt/nvm/etc/bash_completion.d/nvm"  # This loads nvm bash_completion

You can set $NVM_DIR to any location, but leaving it unchanged from
/opt/homebrew/Cellar/nvm/0.40.3 will destroy any nvm-installed Node installations
upon upgrade/reinstall.

Type `nvm help` for further information.
==> Summary
🍺  /opt/homebrew/Cellar/nvm/0.40.3: 10 files, 206.6KB
==> Running `brew cleanup nvm`...
Disable this behaviour by setting `HOMEBREW_NO_INSTALL_CLEANUP=1`.
Hide these hints with `HOMEBREW_NO_ENV_HINTS=1` (see `man brew`).
==> No outdated dependents to upgrade!
==> `brew cleanup` has not been run in the last 30 days, running now...
Disable this behaviour by setting `HOMEBREW_NO_INSTALL_CLEANUP=1`.
Hide these hints with `HOMEBREW_NO_ENV_HINTS=1` (see `man brew`).
Removing: /Users/smartsi/Library/Caches/Homebrew/bootsnap/c76bd5d607f544946a2f876e31b967af5b6ad99c68a2a67a0a02acc7c592f5f2... (625 files, 5.0MB)
Removing: /Users/smartsi/Library/Logs/Homebrew/openssl@3... (64B)
Removing: /Users/smartsi/Library/Logs/Homebrew/ca-certificates... (64B)
Removing: /Users/smartsi/Library/Logs/Homebrew/node... (64B)
==> Caveats
Bash completion has been installed to:
  /opt/homebrew/etc/bash_completion.d
```

## 2. 配置环境变量

首先创建 NVM 的工作目录：
```bash
mkdir ~/.nvm
```
在这修改 `~/.profile` 添加如下配置：
```bash
export NVM_DIR="$HOME/.nvm"
[ -s "/opt/homebrew/opt/nvm/nvm.sh" ] && \. "/opt/homebrew/opt/nvm/nvm.sh"  # This loads nvm
[ -s "/opt/homebrew/opt/nvm/etc/bash_completion.d/nvm" ] && \. "/opt/homebrew/opt/nvm/etc/bash_completion.d/nvm"  # This loads nvm bash_completion
```
运行以下命令以使更改生效：
```bash
source ~/.profile
```

## 3. 验证

运行 `nvm -v` 命令即可验证 nvm 是否安装成功：
```bash
smarsi:opt smartsi$ nvm -v
0.40.3
```

## 4. 使用 nvm 安装多个版本 node

我们已经安装了一个 `v23.11.0` 版本的 node：
```
smarsi:opt smartsi$ node -v
v23.11.0
```
现在想使用 nvm 安装特定版本的 node，例如 `nvm install 13`：
```bash
smarsi:opt smartsi$ nvm install 13
Downloading and installing node v13.14.0...
Downloading https://nodejs.org/dist/v13.14.0/node-v13.14.0-darwin-x64.tar.xz...
############################################################################################################################################################ 100.0%
Computing checksum with shasum -a 256
Checksums matched!
Now using node v13.14.0 (npm v6.14.4)
Creating default alias: default -> 13 (-> v13.14.0)
smarsi:opt smartsi$
```
安装完成查看 node 版本已经发生改变：
```
smarsi:opt smartsi$ node -v
v13.14.0
```

当前你也可以再切换回原先 node 版本，使用 `nvm use` 命令切换到指定版本：
```
smarsi:opt smartsi$ nvm use 23
Now using node v23.11.1 (npm v10.9.2)
smarsi:opt smartsi$
smarsi:opt smartsi$ nvm use 13
Now using node v13.14.0 (npm v6.14.4)
```

> https://cloud.tencent.com/developer/article/2451510
