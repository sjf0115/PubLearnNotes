---
layout: post
author: sjf0115
title: Spark 性能调优之序列化
date: 2018-06-10 11:28:01
tags:
  - Spark
  - Spark 优化

categories: Spark
permalink: spark-performance-data-serialization
---

### 1. 序列化

序列化是将对象转换为字节流，本质上可以理解为将链表存储的非连续空间的数据存储转换为连续空间的存储的数组中。这样就可以将数据进行流式传输或者块存储。相反，反序列化就是将字节流转换为对象。

序列化主要有以下两个目的：
- 进程间通信：不同节点之间进行数据的传输。
- 数据持久化存储到磁盘：本地节点将对象写入磁盘。

分布式应用中，序列化处于举足轻重的地位。那些需要大量时间进行序列化的数据格式和占据过大空间的对象会拖慢整个应用。通常情况下，序列化是Spark调优的第一步。Spark为了权衡兼容性和性能提供了两种序列化库。

### 2. Java序列化
在默认情况下，Spark使用ObjectOutputStream框架对对象进行序列化。可以通过实现 `java.io.Serializable` 接口使对象可以被序列化。你也可以通过继承 `java.io.Externalizable` 进一步控制序列化的性能。Java标准序列化库很灵活，并且兼容性好，但是通常情况下，速度较慢，而且导致序列化后数据量较大。

### 3. Kryo序列化

Spark也可以使用Kryo序列化库来更快速地序列化对象。Kryo相对于Java序列化库能够更加快速和紧凑地进行序列化（通常有10倍的性能优势），但是Kryo并不能支持所有可序列化的类型，如果对程序有较高的性能优化需求，需要你对程序中使用的类进行注册。

#### 3.1 启用Kryo

你可以通过SparkConf调用 `conf.set（"spark.serializer"，"org.apache.spark.serializer.KryoSerializer"）` 使用Kryo初始化你的作业。

如果不想在程序中硬编码启用Kryo，Spark提供了另外一种方式可以在使用spark-submit提交作业时添加 `--conf spark.serializer=org.apache.spark.serializer.KryoSerializer` 选项。

这个序列化器配置不仅可以在 Worker 节点之间 shuffle 数据使用，而且还可以在将RDD序列化到磁盘时使用。Kryo不是序列化默认值的唯一原因是因为需要你自己注册，我们建议在网络密集型应用程序中可以使用它。从Spark 2.0.0版本开始，我们在使用简单类型，简单类型的数组或字符串类型对RDD进行shuffle时内部使用Kryo序列化器。如果想把Kryo设置为默认值，可以修改全局配置`conf/spark-defaults.conf`，修改如下配置:
```
spark.serializer   org.apache.spark.serializer.KryoSerializer
```
#### 3.2 注册自定义类

Kryo默认序列化实例时在前面会写上类名，比如java.lang.Double，类名越长，额外的存储开销越大。为了解决这个问题，Kryo允许将类名注册进映射表里，通过分配数字ID来替换冗长的类名，比如java.lang.Double使用数字0来代替。这种方式节省了储存空间，但代价是我们必须手动将所有性能相关的类名注册。

spark使用Twitter chill注册了常用的Scala类，也对自己的常用类都进行了注册，具体见KryoSerializer.scala。但很遗憾，在实际使用中，仍然有大量的类名未包含其中，必须手动注册。用户自定义类可以用 `conf.registerKryoClasses` 进行注册。此外如果用--conf选项可以用 `spark.kryo.classesToRegister` 属性来注册类，注册类用逗号分隔如 `--conf spark.kryo.classesToRegister=MyClass1,MyClass2`。

Scala版本：
```scala
val conf = new SparkConf().setMaster(...).setAppName(...)
conf.registerKryoClasses(Array(classOf[MyClass1], classOf[MyClass2]))
val sc = new SparkContext(conf)
```
[Kryo 文档](https://github.com/EsotericSoftware/kryo) 描述了更多高级的注册选项，如添加自定义序列的代码。

如果你的对象很大，可能还需要增加 `spark.kryoserializer.buffer` 配置。该值需要足够大才能容纳你将要序列化的大对象。

最后，如果你没有注册自定义类， Kryo仍然可以工作，但它存储每个对象的完整类名称，这是一种浪费。

> `spark.kryo.registrationRequired`:默认为false，如果设为true程序运行过程中检查当前被序列化的类型是否被注册。如果没有就会抛出异常。这样可以保证整个程序所有序列化类型都被注册，防止有类型忘记被注册。

### 4. 对比

实验的数据是1000000行，每一行第一列是用户ID，第二列是手机平台，第三列是所在城市。实验一共有3个类 kryoSerializationExample，CustomKryoRegistrator, AdvPushInfo。kryoSerializationExample是主类，读取测试文件并统计文件行数。AdvPushInfo用于存储每一行的数据，需要被序列化。CustomKryoRegistrator是注册类，作用是注册要被序列化的类，继承KryoRegistrator。

Code:
```java
package com.sjf.example.batch;

import com.sjf.example.bean.AdvPushInfo;
import org.apache.spark.SparkConf;
import org.apache.spark.api.java.JavaRDD;
import org.apache.spark.api.java.JavaSparkContext;
import org.apache.spark.api.java.function.Function;
import org.apache.spark.storage.StorageLevel;

import java.util.Objects;

/**
 * Kryo序列化Example
 * @author sjf0115
 * @Date Created in 上午10:18 18-6-29
 */
public class kryoSerializationExample {

    public static void main(String[] args) {
        long startTime = System.currentTimeMillis();
        // 配置
        SparkConf conf = new SparkConf();
        conf.setAppName("kryoSerializationExample");
        conf.setMaster("local");
        conf.set("spark.serializer","org.apache.spark.serializer.KryoSerializer");
        conf.set("spark.kryo.registrator", "com.sjf.example.bean.CustomKryoRegistrator");
        conf.set("spark.kryo.registrationRequired","true");

        JavaSparkContext sc = new JavaSparkContext(conf);

        JavaRDD<String> sourceRDD = sc.textFile("/home/xiaosi/data/adv_push_info.txt");
        JavaRDD<AdvPushInfo> advRDD = sourceRDD.map(new Function<String, AdvPushInfo>() {
            @Override
            public AdvPushInfo call(String source) throws Exception {
                String[] params = source.split("\t");
                String id = params[0];
                String platform = params[1];
                String city = "";
                if(params.length > 2){
                    city = params[2];
                    if (Objects.equals(city, "\\N")) {
                        city = "";
                    }
                }

                AdvPushInfo advPushInfo = new AdvPushInfo();
                advPushInfo.setId(id);
                advPushInfo.setPlatform(platform);
                advPushInfo.setCity(city);
                return advPushInfo;
            }
        });
        advRDD.persist(StorageLevel.MEMORY_AND_DISK_SER());
        System.out.println(advRDD.count());
        System.out.println((System.currentTimeMillis() - startTime) / 1000);
    }
}
```
注册器：
```java
package com.sjf.example.bean;

import com.esotericsoftware.kryo.Kryo;
import org.apache.spark.serializer.KryoRegistrator;

/**
 * @author sjf0115
 * @Date Created in 下午2:17 18-6-29
 */
public class CustomKryoRegistrator implements KryoRegistrator {
    @Override
    public void registerClasses(Kryo kryo) {
        kryo.register(AdvPushInfo.class);
    }
}
```

#### 4.1 Java序列化

```
MemoryStore: MemoryStore started with capacity 873.0 MB
MemoryStore: Block broadcast_0 stored as values in memory (estimated size 127.1 KB, free 872.9 MB)
MemoryStore: Block broadcast_0_piece0 stored as bytes in memory (estimated size 14.3 KB, free 872.9 MB)
MemoryStore: Block broadcast_1 stored as values in memory (estimated size 3.7 KB, free 872.9 MB)
MemoryStore: Block broadcast_1_piece0 stored as bytes in memory (estimated size 2.2 KB, free 872.9 MB)
MemoryStore: Block rdd_2_0 stored as bytes in memory (estimated size 41.7 MB, free 831.2 MB)
MemoryStore: Block rdd_2_1 stored as bytes in memory (estimated size 11.7 MB, free 819.5 MB)
MemoryStore: MemoryStore cleared
```

#### 4.2 Kryo且注册

```
MemoryStore: MemoryStore started with capacity 873.0 MB
MemoryStore: Block broadcast_0 stored as values in memory (estimated size 127.1 KB, free 872.9 MB)
MemoryStore: Block broadcast_0_piece0 stored as bytes in memory (estimated size 14.3 KB, free 872.9 MB)
MemoryStore: Block broadcast_1 stored as values in memory (estimated size 3.7 KB, free 872.9 MB)
MemoryStore: Block broadcast_1_piece0 stored as bytes in memory (estimated size 2.2 KB, free 872.9 MB)
MemoryStore: Block rdd_2_0 stored as bytes in memory (estimated size 33.8 MB, free 839.0 MB)
MemoryStore: Block rdd_2_1 stored as bytes in memory (estimated size 9.5 MB, free 829.6 MB)
MemoryStore: MemoryStore cleared
```

#### 4.3 Kryo无注册

```
MemoryStore: MemoryStore started with capacity 873.0 MB
MemoryStore: Block broadcast_0 stored as values in memory (estimated size 127.1 KB, free 872.9 MB)
MemoryStore: Block broadcast_0_piece0 stored as bytes in memory (estimated size 14.3 KB, free 872.9 MB)
MemoryStore: Block broadcast_1 stored as values in memory (estimated size 3.7 KB, free 872.9 MB)
MemoryStore: Block broadcast_1_piece0 stored as bytes in memory (estimated size 2.2 KB, free 872.9 MB)
MemoryStore: Block rdd_2_0 stored as bytes in memory (estimated size 58.4 MB, free 814.5 MB)
MemoryStore: Block rdd_2_1 stored as bytes in memory (estimated size 16.4 MB, free 798.1 MB)
MemoryStore: MemoryStore cleared
```
#### 4.4 实验结果

类型|MemoryStore|TimeCost
---|---|---
Java序列化|53.5MB|15s
Kryo序列化未注册自定义类|74.9MB|10s
Kryo序列化且注册自定义类|43.4MB|9s

通过上面表格中的数据我们可以看到，如果你没有注册自定义类， Kryo虽然可以工作，但由于存储每个对象的完整类名称，会多占用空间。

> Spark 版本 2.3.1

资料：http://spark.apache.org/docs/2.3.1/tuning.html#data-serialization

https://facaiy.com/misc/2017/01/21/spark-kyro.html

https://segmentfault.com/q/1010000007041500
