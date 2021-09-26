
问题描述：
```
[sjf0115@ying ~]$ sudo yum -y install  mysql80-community-release-el6-1.noarch.rpm
Loaded plugins: fastestmirror, security
Repository epel is listed more than once in the configuration
Loading mirror speeds from cached hostfile
epel   | 3.2 kB     00:00     
http://download.fedoraproject.org/pub/epel/6/x86_64/repodata/xxx-primary.xml.gz: [Errno 14] problem making ssl connection
Trying other mirror.
http://download.fedoraproject.org/pub/epel/6/x86_64/repodata/xxx-primary.xml.gz: [Errno 14] problem making ssl connection
Trying other mirror.
Error: failure: repodata/xxx-primary.xml.gz from epel: [Errno 256] No more mirrors to try.
```
问题解决：

把 `/etc/yum.repos.d/epel.repo` 文件第3行注释去掉，把第四行注释掉。
```
[sjf0115@ying ~]$ sudo vim /etc/yum.repos.d/epel.repo
[epel]
name=Extra Packages for Enterprise Linux 6 - $basearch
#baseurl=http://download.fedoraproject.org/pub/epel/6/$basearch
mirrorlist=https://mirrors.fedoraproject.org/metalink?repo=epel-6&arch=$basearch
```
修改为：
```
[sjf0115@ying ~]$ sudo vim /etc/yum.repos.d/epel.repo
[epel]
name=Extra Packages for Enterprise Linux 6 - $basearch
baseurl=http://download.fedoraproject.org/pub/epel/6/$basearch
#mirrorlist=https://mirrors.fedoraproject.org/metalink?repo=epel-6&arch=$basearch
```
再清理源，重新安装
```
sudo yum clean all
sudo yum -y install  mysql80-community-release-el6-1.noarch.rpm
```
