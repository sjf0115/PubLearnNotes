---
layout: post
author: sjf0115
title: Hadoop MapReduce 作业配置与提交
date: 2022-07-01 13:20:17
tags:
  - Hadoop

categories: Hadoop
permalink: hadoop-mapreduce-job-conf-submit
---

在 Hadoop 中，Common、HDFS 和 MapReduce 各有对应的配置文件，用于保存对应模块中可配置的参数。这些配置文件均为 ⅩML 格式且由两部分构成：系统默认配置文件和管理员自定义配置文件。其中，系统默认配置文件分别是 core-default.xml、hdfs-default.xml和 mapred-default.xml，它们包含了所有可配置属性的默认值。而管理员自定义配置文件分别是 core-site.xml、hdfs-site.xml 和 mapred-site.xml。它们由管理员设置，主要用于定义一些新的配置属性或者覆盖系统默认配置文件中的默认值。通常这些配置一旦确定，便不能被修改（如果想修改，需重新启动 Hadoop）。需要注意的是，core-default.xml和 core-site.xml 属于公共基础库的配置文件，默认情况下，Hadoop 总会优先加载它们。

在 Hadoop 中，每个配置属性主要包括三个配置参数：name、value 和 description，分别表示属性名、属性值和属性描述。其中，属性描述仅仅用来帮助用户理解属性的含义，Hadoop 内部并不会使用它的值。此外，Hadoop 为配置文件添加了两个新的特性：final 参数和变量扩展。

第一个特性是 final 参数，如果管理员不想让用户程序修改某些属性的属性值，可将该属性的 final 参数置为true，比如：
```xml
<property>
  <name>mapred.map.tasks.speculative.execution</name>
  <value>true</value>
  <final>true</final>
</property>
```
管理员一般在 ⅩⅩⅩ-site.xml 配置文件中为某些属性添加 final 参数，以防止用户在应用程序中修改这些属性的属性值。

第二个特性是变量扩展，当读取配置文件时，如果某个属性存在对其他属性的引用，那么 Hadoop 首先会查找引用的属性是否为下列两种属性之一。如果是，则进行扩展：
- 其他已经定义的属性。
- Java中System.getProperties()函数可获取属性。

比如，如果一个配置文件中包含以下配置参数：
```xml
<property>
  <name>hadoop.tmp.dir</name>
  <value>/tmp/hadoop-${user.name}</value>
</property>
<property>
  <name>mapred.temp.dir</name>
  <value>${hadoop.tmp.dir}/mapred/temp</value>
</property>
```
则当用户想要获取属性 mapred.temp.dir 的值时，Hadoop 会将 hadoop.tmp.dir 解析成该配置文件中另外一个属性的值，而 user.name 则被替换成系统属性 user.name 的值。

## 2. MapReduce 作业配置与提交

在 MapReduce 中，每个作业由两部分组成：应用程序和作业配置。其中，作业配置内容包括环境配置和用户自定义配置两部分。环境配置由 Hadoop 自动添加，主要由 mapred-default.xml 和 mapred-site.xml 两个文件中的配置选项组合而成；用户自定义配置则由用户自己根据作业特点个性化定制而成，比如用户可设置作业名称、Map和Reduce Task 个数等。在新旧两套 API 中，作业配置接口发生了变化，首先通过一个例子感受一下使用上的不同。

旧 API 作业配置实例：
```java
JobConf conf = new JobConf(new Configuration(), WordCountV1.class);
conf.setJobName("WordCountV1");
conf.setMapperClass(WordCountMapper.class);
conf.setReducerClass(WordCountReducer.class);
JobClient.runJob(conf);
```
新 API 作业配置实例：
```java
Configuration conf = this.getConf();
Job job = Job.getInstance(conf);
job.setJobName("WordCountV2");
job.setJarByClass(WordCountV2.class);
job.setMapperClass(WordCountMapper.class);
job.setReducerClass(WordCountReducer.class);
System.exit(job.waitForCompletion(true) ? 0 : 1);
```
从以上两个实例可以看出，新版 API 用 Job 类代替了 JobConf 和 JobClient 两个类，这样仅使用一个类就可以完成作业配置和作业提交相关功能，进一步简化了作业编写方式。
