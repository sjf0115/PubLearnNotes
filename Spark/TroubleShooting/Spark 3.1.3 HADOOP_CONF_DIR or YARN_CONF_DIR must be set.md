
## 1. 现象

使用如下命令以 client 模式提交作业到 Yarn 上时：
```
spark-submit \
  --class com.spark.example.core.base.WordCount \
  --master yarn \
  --deploy-mode client \
  --executor-memory 2g \
  --num-executors 4 \
  --executor-cores 1 \
spark-example-3.1-1.0.jar \
/data/word-count/word-count-input /data/word-count/word-count-output
```
抛出如下异常：
```java
Exception in thread "main" org.apache.spark.SparkException: When running with master 'yarn' either HADOOP_CONF_DIR or YARN_CONF_DIR must be set in the environment.
        at org.apache.spark.deploy.SparkSubmitArguments.error(SparkSubmitArguments.scala:631)
        at org.apache.spark.deploy.SparkSubmitArguments.validateSubmitArguments(SparkSubmitArguments.scala:271)
        at org.apache.spark.deploy.SparkSubmitArguments.validateArguments(SparkSubmitArguments.scala:234)
        at org.apache.spark.deploy.SparkSubmitArguments.<init>(SparkSubmitArguments.scala:119)
        at org.apache.spark.deploy.SparkSubmit$$anon$2$$anon$3.<init>(SparkSubmit.scala:1022)
        at org.apache.spark.deploy.SparkSubmit$$anon$2.parseArguments(SparkSubmit.scala:1022)
        at org.apache.spark.deploy.SparkSubmit.doSubmit(SparkSubmit.scala:85)
        at org.apache.spark.deploy.SparkSubmit$$anon$2.doSubmit(SparkSubmit.scala:1039)
        at org.apache.spark.deploy.SparkSubmit$.main(SparkSubmit.scala:1048)
        at org.apache.spark.deploy.SparkSubmit.main(SparkSubmit.scala)
```

> [WordCount](https://github.com/sjf0115/data-example/blob/master/spark-example-3.1/src/main/java/com/spark/example/core/base/WordCount.java)

## 2. 解决方案

上面错误提示其实已经说的很明白了，在运行环境中缺少了 HADOOP_CONF_DIR 或者 YARN_CONF_DIR 环境变量配置。所以我们在 spark-env.sh 文件中添加如下配置：
```
# Options read in YARN client/cluster mode
export HADOOP_CONF_DIR=/opt/hadoop/etc/hadoop
```
配置完重新运行脚本即可。
