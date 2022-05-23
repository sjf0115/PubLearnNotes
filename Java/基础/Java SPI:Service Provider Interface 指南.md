
## 1. 什么是 SPI

SPI 全称为 (Service Provider Interface) ，是 JDK 内置的一种服务提供发现机制。目前有不少框架用它来做服务的扩展发现， 简单来说，它就是一种动态替换发现的机制，举个例子来说，有个接口，想运行时动态的给它添加实现，你只需要添加一个实现。


### API vs SPI

API（Application Programming Interface）的概念对我们来说已经是见怪不怪了。在日常开发过程中，我们需要调用平台/框架提供的API，而我们的下游应用也需要调用上游提供的API。一句话：API站在应用的角度定义了功能如何实现。

但是，如果我们作为服务提供方，想要丰富现有的系统，加入一些原本不具备的相对完整的能力，若是直接hack代码的话，不仅要新建或改动很多API，还需要重新构建相关的模块，并且可能无法很好地保证新模块与旧有模块的统一性。而Java 6引入了SPI（Service Provider Interface，服务提供者接口），可以非常方便地帮助我们实现插件化开发。顾名思义，SPI仍然遵循基于接口编程的思想，服务提供方通过实现SPI定义的接口来扩展系统，SPI机制后续完成发现与注入的职责。也就是说，SPI 是系统为第三方专门开放的扩展规范以及动态加载扩展点的机制。

API 和 SPI 之间的不同可以藉由下图来说明。


API: 服务提供方提供接口的定义并提供接口的实现，开发人员直接使用API即可。
SPI: 多用于制定接口规范，服务调用方提供接口的规范，不同服务提供方实现自己的逻辑。有利于开发人员实现扩展，易于框架扩展人员使用；

## 2. 如何实现 SPI

当使用 SPI 机制时，需要共同遵循 SPI 的约定：
- 服务调用方定义接口的规范
- 服务提供方提供了接口的具体实现
  - 在 classpath 的 META-INF/services 目录下创建一个以接口全限定名命名的文本文件
  - 在文件中写入实现类的全限定名。如果有多个实现类，以换行符分隔
- 服务调用方调用接口实现
  - 调用 Jdk 中的 ServiceLoader 的 load 方法加载具体的服务实现。

### 2.1 服务调用方定义接口规范

首先由服务调用方定义接口的规范，具体的实现都是由不同服务提供方实现。在这我们在 connector-common 模块中定义了一个 Sink 接口：
```java
package com.connector;

/**
 * 将数据输出到外部系统
 */
public interface Sink {
    // 获取 Sink 类型
    String getSinkType();
    // 将数据输出到外部系统
    void run(String content);
}
```
接口中有两个方法：
- getSinkType：获取 Sink 的类型
- run：将数据输出到外部系统

### 2.2 服务提供方提供接口实现

在这我们模拟实现了两个服务提供方的接口实现。

### 2.2.1 FileSink

```java
package com.connector;
public class FileSink implements Sink {
    public String getSinkType() {
        return "file";
    }

    public void run(String content) {
        System.out.println("[INFO] file sink: " + content);
    }
}
```




## 3. SPI 实现原理



参考：
- https://dongzl.github.io/2021/01/16/04-Java-Service-Provider-Interface/
- https://www.cnblogs.com/warehouse/p/9335530.html
- https://www.jianshu.com/p/32370d9b9046
- https://blog.csdn.net/top_code/article/details/51934459
- https://mp.weixin.qq.com/s/y6HrRDUqWnYclLcVaCVYqA
- https://mp.weixin.qq.com/s/20t_UtNNwXfynbzxpi7p2Q
- https://mp.weixin.qq.com/s/vpy5DJ-hhn0iOyp747oL5A
-
