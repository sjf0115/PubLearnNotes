---
layout: post
author: sjf0115
title: Flink1.4 执行计划
date: 2018-01-04 14:46:01
tags:
  - Flink
  - Flink 基础

categories: Flink
permalink: flink-execution-plans
---

根据各种参数(如数据大小或集群中的机器数量)，`Flink`的优化器自动会为你的程序选择一个执行策略。很多情况下，准确的知道`Flink`如何执行你的程序是很有帮助的。

### 1. 计划可视化工具

`Flink`内置一个执行计划的可视化工具。包含可视化工具的`HTML`文档位于`tools/planVisualizer.html`下。用`JSON`表示作业执行计划，并将其可视化为具有执行策略完整注释的图(visualizes it as a graph with complete annotations of execution strategies)。

备注:
```
打开可视化工具的方式有所改变:由本地文件 tools/planVisualizer.html 改为 url http://flink.apache.org/visualizer/index.html
```

以下代码显示了如何从程序中打印执行计划的`JSON`：

Java版本:
```java
final ExecutionEnvironment env = ExecutionEnvironment.getExecutionEnvironment();
...
System.out.println(env.getExecutionPlan());
```
Scala版本:
```
val env = ExecutionEnvironment.getExecutionEnvironment
...
println(env.getExecutionPlan())
```

要可视化执行计划，请执行以下操作：

(1) 使用浏览器打开`planVisualizer.html`(或者直接在浏览器中输入http://flink.apache.org/visualizer/index.html 网址)

![](https://github.com/sjf0115/PubLearnNotes/blob/master/image/Flink/Flink%20%E6%89%A7%E8%A1%8C%E8%AE%A1%E5%88%92-2.png?raw=true)

(2) 将`JSON`字符串粘贴到文本框中

(3) 点击`Draw`按钮

完成上面这些步骤后，将会显示详细的执行计划。

![](https://github.com/sjf0115/PubLearnNotes/blob/master/image/Flink/Flink%20%E6%89%A7%E8%A1%8C%E8%AE%A1%E5%88%92-1.png?raw=true)

### 2. Web界面

`Flink`提供了一个用于提交和执行作业的Web界面。这个界面是`JobManager Web`监控界面的一部分，默认情况下在端口`8081`上运行。通过这个界面提交作业需要你在`flink-conf.yaml`中设置`jobmanager.web.submit.enable：true`。

你可以在作业执行之前指定程序参数。执行计划可视化器使你能够在执行Flink作业之前查看执行计划。


备注:
```
Flink版本:1.4
```

原文:https://ci.apache.org/projects/flink/flink-docs-release-1.3/dev/execution_plans.html
