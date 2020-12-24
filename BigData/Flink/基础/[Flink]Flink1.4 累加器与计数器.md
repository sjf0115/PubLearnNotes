---
layout: post
author: sjf0115
title: Flink1.4 累加器与计数器
date: 2018-01-04 11:46:01
tags:
  - Flink
  - Flink 基础

categories: Flink
permalink: flink-accumulators-counters
---

### 1. 概述

累加器(`Accumulators`)是一个简单的构造器，具有加法操作和获取最终累加结果操作，在作业结束后可以使用。

最直接的累加器是一个计数器(`counter`)：你可以使用`Accumulator.add()`方法对其进行累加。在作业结束时，`Flink`将合并所有部分结果并将最终结果发送给客户端。在调试过程中，或者你快速想要了解有关数据的更多信息，累加器很有用。

目前`Flink`拥有以下内置累加器。它们中的每一个都实现了累加器接口：

(1) `IntCounter`, `LongCounter` 以及 `DoubleCounter`: 参阅下面示例中使用的计数器。

(2) `Histogram`：为离散数据的直方图(A histogram implementation for a discrete number of bins.)。内部它只是一个整数到整数的映射。你可以用它来计算值的分布，例如 单词计数程序的每行单词分配。

### 2. 如何使用

首先，你必须在你要使用的用户自定义转换函数中创建一个累加器(`accumulator`)对象(这里是一个计数器):
```java
private IntCounter numLines = new IntCounter();
```

其次，你必须注册累加器(`accumulator`)对象，通常在`rich`函数的`open()`方法中注册。在这里你也可以自定义累加器的名字:
```java
getRuntimeContext().addAccumulator("num-lines", this.numLines);
```
现在你就可以在算子函数中的任何位置使用累加器，包括在`open()`和`close()`方法中:
```java
this.numLines.add(1);
```
最后结果将存储在`JobExecutionResult`对象中，该对象从执行环境的`execute()`方法返回(当前仅当执行等待作业完成时才起作用):
```java
JobExecutionResult result = env.execute();
long lineCounter = result.getAccumulatorResult("num-lines");
System.out.println(lineCounter);
```
每个作业的所有累加器共享一个命名空间。因此，你可以在作业的不同算子函数中使用同一个累加器。`Flink`在内部合并所有具有相同名称的累加器。

备注:
```
目前累加器的结果只有在整个工作结束之后才可以使用。我们还计划在下一次迭代中可以使用前一次迭代的结果。你可以使用聚合器来计算每次迭代的统计信息，并基于此类统计信息来终止迭代。
```

### 3. Example

```java
import com.google.gson.Gson;
import com.google.gson.GsonBuilder;
import com.qunar.innovation.data.bean.AdsPushBehavior;
import com.qunar.innovation.data.utils.ConstantUtil;
import org.apache.flink.api.common.accumulators.LongCounter;
import org.apache.flink.api.common.functions.RichMapFunction;
import org.apache.flink.configuration.Configuration;

public class AdsPushParseMap extends RichMapFunction<String, AdsPushBehavior> {

    private static Gson gson = new GsonBuilder().setDateFormat("yyyy-MM-dd HH:mm:ss").create();
    private final LongCounter behaviorCounter = new LongCounter();

    @Override
    public void open(Configuration parameters) throws Exception {
        super.open(parameters);
        getRuntimeContext().addAccumulator(ConstantUtil.ADS_PUSH_APP_CODE, behaviorCounter);
    }

    @Override
    public AdsPushBehavior map(String content) throws Exception {

        try{
            // 解析
            AdsPushBehavior adsPushBehavior = gson.fromJson(content, AdsPushBehavior.class);
            this.behaviorCounter.add(1);
            return adsPushBehavior;
        }
        catch (Exception e){
            e.printStackTrace();
        }
        return null;

    }
}
```

```java
import com.qunar.innovation.data.TestFlink;
import com.qunar.innovation.data.functions.*;
import com.qunar.innovation.data.utils.ConstantUtil;
import org.apache.flink.api.common.JobExecutionResult;
import org.apache.flink.api.java.DataSet;
import org.apache.flink.api.java.ExecutionEnvironment;
import org.apache.flink.core.fs.FileSystem;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class AdsPushLocalStream {

    private final static Logger LOGGER = LoggerFactory.getLogger(TestFlink.class);

    public static void main(String[] args) {

        ExecutionEnvironment env = ExecutionEnvironment.getExecutionEnvironment();

        DataSet<String> dataSet = env.readTextFile("file:///home/xiaosi/input.txt");

        // 处理数据
        DataSet<String> adsPushDataSet = dataSet.map(new ContentMap()).name("contentMap").setParallelism(1).
                map(new AdsPushParseMap()).name("behaviorMap").setParallelism(1)
                .map(new AdsPushFeatureMap()).name("featureMap").setParallelism(1)
                .filter(new AdsPushFeatureFilter()).name("featureFilter").setParallelism(1);

        adsPushDataSet.writeAsText("file:///home/xiaosi/output", FileSystem.WriteMode.OVERWRITE);

        try {
            JobExecutionResult result = env.execute();
            long behaviorCounter = result.getAccumulatorResult(ConstantUtil.ADS_PUSH_APP_CODE);
            System.out.println(behaviorCounter);
        } catch (Exception e) {
            LOGGER.error(e.getMessage(), e);
        }

    }
}
```

### 3. 自定义累加器

为了实现你自己的累加器，你只需要编写你的`Accumulator`接口的实现。如果你认为你的自定义累加器应与`Flink`一起传输，请随意创建一个拉取请求(Feel free to create a pull request if you think your custom accumulator should be shipped with Flink.)。

你可以选择实现[Accumulator](https://github.com/apache/flink/blob/master//flink-core/src/main/java/org/apache/flink/api/common/accumulators/Accumulator.java)或[SimpleAccumulator](https://github.com/apache/flink/blob/master//flink-core/src/main/java/org/apache/flink/api/common/accumulators/SimpleAccumulator.java)。

`Accumulator<V，R>`非常灵活：它为要添加的值定义一个类型`V`，并为最终结果定义一个结果类型`R`。例如，对于直方图，`V`是数字，`R`是直方图。`SimpleAccumulator`适用于两种类型相同的情况，例如，计数器。

备注:
```
Flink版本:1.4
```


原文:https://ci.apache.org/projects/flink/flink-docs-release-1.4/dev/api_concepts.html#accumulators--counters
