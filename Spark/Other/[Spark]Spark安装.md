### 1. Scala安装

我们从官网下载最新版本（2.11.8）：http://www.scala-lang.org/

解压到~/opt：
```
tar -zxvf scala-2.11.8.tgz -C opt/
```
### 2. Python安装
```
sudo apt-get install ipython
sudo apt-get install python
```
查看版本：
```
xiaosi@yoona:~$ python --version
Python 2.7.10
xiaosi@yoona:~$ ipython --version
2.3.0
```
### 3. Spark安装

我们从官网上下载最新版本：http://spark.apache.org/downloads.html

解压到~/opt：
```
xiaosi@yoona:~$ tar -zxvf spark-2.0.2-bin-hadoop2.7.tgz -C opt/
```
设置环境变量，指向Spark目录，便于后续操作：
```
# spark
export SPARK_HOME=/home/xiaosi/opt/spark-2.0.2-bin-hadoop2.7
export PATH=${SPARK_HOME}/bin:$PATH
```







