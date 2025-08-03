由于网络原因，直接在 Atom 上安装插件会异常的慢（基本无法安装成功），因此采用离线安装的方式，本文通过 atom-beautify 插件的安装步骤来介绍 Atom 如何去离线安装插件。

1. 准备
npm的安装：安装步骤比较简单，可以自行百度安装。
2. 下载atom插件
下载atom插件的方式比较多，我这里建议去GitHub网站下载。
1）在GitHub网站上找到atom-beautify：



```
smartsi@192 .atom % cd packages
smartsi@192 packages %
smartsi@192 packages % ls -al
total 0
drwxr-xr-x  2 smartsi  staff   64  8  3 09:33 .
drwxr-xr-x  9 smartsi  staff  288  8  3 09:33 ..
smartsi@192 packages %
smartsi@192 packages % git clone git@github.com:Glavin001/atom-beautify.git
Cloning into 'atom-beautify'...
remote: Enumerating objects: 11670, done.
remote: Counting objects: 100% (62/62), done.
remote: Compressing objects: 100% (33/33), done.
remote: Total 11670 (delta 59), reused 29 (delta 29), pack-reused 11608 (from 2)
Receiving objects: 100% (11670/11670), 3.41 MiB | 308.00 KiB/s, done.
Resolving deltas: 100% (7806/7806), done.
```

```
smartsi@192 packages % cd git-plus
smartsi@192 atom-beautify % npm install
npm warn old lockfile
npm warn old lockfile The package-lock.json file was created with an old version of npm,
npm warn old lockfile so supplemental metadata must be fetched from the registry.
npm warn old lockfile
npm warn old lockfile This is a one-time fix-up, please be patient...
npm warn old lockfile
```
