
```
I have no name!@spark-master:/opt/bitnami/spark$ bin/spark-submit \
    --master yarn \
    --deploy-mode cluster \
    --class org.apache.spark.examples.SparkPi \
    /opt/bitnami/spark/examples/jars/spark-examples_2.12-3.5.0.jar \
    1000
Exception in thread "main" org.apache.spark.SparkException: When running with master 'yarn' either HADOOP_CONF_DIR or YARN_CONF_DIR must be set in the environment.
	at org.apache.spark.deploy.SparkSubmitArguments.error(SparkSubmitArguments.scala:650)
	at org.apache.spark.deploy.SparkSubmitArguments.validateSubmitArguments(SparkSubmitArguments.scala:281)
	at org.apache.spark.deploy.SparkSubmitArguments.validateArguments(SparkSubmitArguments.scala:237)
	at org.apache.spark.deploy.SparkSubmitArguments.<init>(SparkSubmitArguments.scala:122)
	at org.apache.spark.deploy.SparkSubmit$$anon$2$$anon$3.<init>(SparkSubmit.scala:1103)
	at org.apache.spark.deploy.SparkSubmit$$anon$2.parseArguments(SparkSubmit.scala:1103)
	at org.apache.spark.deploy.SparkSubmit.doSubmit(SparkSubmit.scala:86)
	at org.apache.spark.deploy.SparkSubmit$$anon$2.doSubmit(SparkSubmit.scala:1120)
	at org.apache.spark.deploy.SparkSubmit$.main(SparkSubmit.scala:1129)
	at org.apache.spark.deploy.SparkSubmit.main(SparkSubmit.scala)
```
