---
layout: post
author: smartsi
title: JMX 使用指南一 Java Management Extensions
date: 2021-06-27 12:07:21
tags:
  - JMX

categories: JMX
permalink: jmx-java-management-extensions
---

## 1. 什么是 JMX

JMX，全称 Java Management Extensions，是在 J2SE 5.0 版本中引入的一个功能。提供了一种在运行时动态管理资源的框架，主要用于企业应用程序中实现可配置或动态获取应用程序的状态。JMX 提供了一种简单、标准的监控和管理资源的方式，对于如何定义一个资源给出了明确的模式。

## 2. JMX 架构

JMX 架构分为三层：
- 资源层：该层包含 MBean 及其可管理的资源，提供了实现 JMX 技术可管理资源的规范。
- 代理层：或者称为 MBean Server 层，是 JMX 的核心。充当 MBean 和应用程序之间的中介。
- 远程管理层：能够让应用程序远程通过 Connector 和 Adapter 访问 MBean Server。

![](https://github.com/sjf0115/ImageBucket/blob/main/Java/jmx-java-management-extensions-1.png?raw=true)

要通过 JMX 管理资源，我们需要创建 MBean 来表示要管理的资源，然后将其注册到 MBean Server 中。MBean Server 作为所有已注册 MBean 的管理代理，实现对外提供服务以及对内管理 MBean 资源。JMX 不仅仅用于本地管理，JMX Remote API 为 JMX 添加了远程功能，使之可以通过网络远程监视和管理应用程序。我们可以使用 JMX Connector 连接到 MBean Server 并管理注册的资源。例如，可以使用 JDK 自带的 JConsole 连接到本地或远程 MBean Server。

### 2.1 资源探测层

资源探测层的核心是用于资源管理的 Managed bean，简称 MBean。MBean 表示在 Java 虚拟机中运行的资源，例如应用程序或 Java EE 技术服务（事务监视器、JDBC 驱动程序等）。MBean 可用来收集重点关注的统计信息，比如性能、资源使用以及问题等，也可以用于获取和设置应用程序配置或属性（推/拉模式），也还可以用于故障通知或者状态变更（推送）等。

MBean 有两种基本类型：
- Standard MBean：这是最简单的一种 MBean。实现了一个业务接口，其中包含属性的 setter 和 getter 以及操作（即方法）。
- Dynamic MBean：实现 javax.management.DynamicMBean 接口的 MBean，该接口提供了一种列出属性和操作以及获取和设置属性值的方法。

此外还有 Open MBeans、Model MBeans 和 Monitor MBeans。Open MBean 是依赖于基本数据类型的动态 MBean。Model MBean 是可以在运行时配置的动态 MBean。

MBean 是一个轻量级的 Java 类，它知道如何使用、获取和操作其资源，以便为代理和用户提供访问或功能。除了 JVM 会把自身的各种资源以 MBean 注册到 JMX 中，我们自己的配置、监控等资源也可以作为 MBean 注册到 JMX，这样管理程序就可以直接控制我们暴露的 MBean。为此我们需要首先创建一个接口（定义属性和操作），并且接口的名称必须以 MBean 结尾：
```java
public interface CounterMBean {
    // 管理属性
    public int getCounter();
    public void setCounter(int counter);
    // 管理操作
    public void increase();
    public void decrease();
}
```
下一步是提供 MBean 接口的实现。JMX 命名约定实现类名为接口名去掉 MBean 后缀。所以我的实现类将是 Counter：
```java
public class Counter implements CounterMBean {
    private int counter = 0;
    @Override
    public int getCounter() {
        return counter;
    }
    @Override
    public void setCounter(int counter) {
        this.counter = counter;
    }
    // 加1
    @Override
    public void increase() {
        this.counter += 1;
    }
    // 减1
    @Override
    public void decrease() {
        this.counter -= 1;
    }
}
```
MBean 允许通过使用 JMX 代理来管理资源。每个 MBean 都会暴露了底层资源的一部分属性和操作：
- 可以读写的属性，实现包含属性的 setter 和 getter 方法，在这为 counter。
- 可以调用的方法，可以向它提供参数或者获取返回值，在这有 increase 和 decrease。

### 2.2 代理层

代理层充当管理资源和应用程序之间的中介。代理层提供对来自管理应用程序的管理资源的访问。JMX 代理可以在嵌入在管理资源的机器中的 JVM 中运行，也可以位于远程位置。代理不需要知道它公开的资源以及使用公开 MBean 的管理器应用程序。它充当处理 MBean 的服务，并允许通过通过 Connector 或 Adaptor 公开的协议来操作 MBean。

代理层的职责之一是将应用程序与管理资源分离。应用程序不会直接引用管理的资源，而是通过 JMX 代理的对象名称引用调用管理操作。代理层的核心组件是 MBean Server，作为 MBean 的注册中心，并允许应用程序发现已注册 MBean 的管理接口。除此之外，代理层提供了四种代理服务，使管理 MBean 更加容易：计时器服务、监控服务、关系服务以及动态 MBean 加载服务。  

想要 MBean Server 可以管理 MBean 资源，首先要把资源注册到 MBean Server 上，任何符合 JMX 的 MBean 资源都可以进行注册。现在我们需要将上面创建的 MBean 实现类 Counter 注册到 MBean Server 中：
```java
public class CounterManagement {
    public static void main(String[] args) throws Exception {
        // 获取 MBean Server
        MBeanServer platformMBeanServer = ManagementFactory.getPlatformMBeanServer();
        // 创建 MBean
        Counter counter = new Counter();
        counter.setCounter(0);
        // 注册
        ObjectName objectName = new ObjectName("com.common.example.jmx:type=Counter, name=CounterMBean");
        platformMBeanServer.registerMBean(counter, objectName);
        // 防止退出
        while (true) {
            Thread.sleep(3000);
            System.out.println("[INFO] 休眠 3s ..............");
        }
    }
}
```
首先我们通过 ManagementFactory 来获取 MBean Server 来注册 MBean。我们会使用 ObjectName 向 MbeanServer 注册 MBean 接口实现类 Counter 实例。ObjectName 由 domain:key 格式构成：
- domain：可以是任意字符串，但根据 MBean 命名约定，一般使用 Java 包名（避免命名冲突）
- key：以逗号分隔的'key=value'键值对列表

我们一般会定义两个 key：
- type=MXBean 接口的实现类的类名
- name=自定义的名字

在这里，我们使用的是：'com.common.example.jmx:type=Counter, name=CounterMBean'。

### 2.3 远程管理层

远程管理层是 JMX 架构的最外层，该层负责使 JMX 代理对外部世界可用。代理层并没有实现远程访问方法，所以在远程管理层会提供一个远程通信接口对外提供服务。提供对外服务需要通过使用一个或多个 JMX Connector 或者 Adaptor 来实现。Connector 和 Adaptor 允许应用程序通过特定协议访问远程 JMX 代理，这样来自不同 JVM 的应用程序就可以调用 MBean Server 上的管理操作、获取或设置管理属性、实例化和注册新的 MBean，以及注册和接收来自管理资源的通知。

Connector 是将代理 API 暴露给其他分布式技术，例如 Java RMI，而 Adaptor 则是通过 HTTP 或者 SNMP 等不同的协议提供对 MBean 的可见性。事实上，一个代理可以使用许多不同的技术。Connector 和 Adaptor 在 JMX 环境中提供相同的功能。

JavaSE 提供了一个 Jconsole 程序，用于通过 RMI 连接到 MBean Server，这样就可以管理整个 Java 进程。下面示例我们会使用 JConsole 来演示效果。

## 3. 实战

我们以实际问题为例，假设我们希望给应用程序添加一个用户黑名单功能，凡是在黑名单中的用户禁止访问，传统的做法是定义一个配置文件，启动的时候读取：
```
# blacklist.txt
a
b
...
```
如果要修改黑名单怎么办？修改配置文件，然后重启应用程序。但是每次都重启应用程序实在是太麻烦了，能不能不重启应用程序？可以自己写一个定时读取配置文件的功能，检测到文件改动时自动重新读取。上述需求本质上就是在应用程序运行期间对参数、配置等进行热更新并要求尽快生效。

这个需求我们可以尝试使用 JMX 的方式实现，我们不必自己编写自动重新读取的任何代码，只需要提供一个符合 JMX 标准的 MBean 来存储用户黑名单即可。

### 3.1 黑名单管理接口 BlacklistMBean

JMX 的 MBean 通常以 MBean 结尾，因此我们遵循标准命名规范，首先编写一个 BlacklistMBean 接口实现对用户黑名单的管理：
```java
public interface BlackListMBean {
    // 获取黑名单列表
    public String[] getBlackList();
    // 在黑名单列表中添加一个用户
    public void addBlackItem(String uid);
    // 判断某个用户是否在黑名单中
    public boolean contains(String uid);
    // 获取黑名单大小
    public int getBlackListSize();
}
```

### 3.2 黑名单管理实现 BlackList

MBean 有一个规则，标准 MBean 接口名称必需是在要实现类名后面加上 MBean 后缀。所以我们的黑名单管理实现类必须为 BlackList，其中定义了一个 uidSet 集合存储用户黑名单：
```java
public class BlackList implements BlackListMBean {
    private Set<String> uidSet = new HashSet<>();
    @Override
    public String[] getBlackList() {
        return uidSet.toArray(new String[0]);
    }
    @Override
    public void addBlackItem(String uid) {
        uidSet.add(uid);
    }
    @Override
    public boolean contains(String uid) {
        return uidSet.contains(uid);
    }
    @Override
    public int getBlackListSize() {
        return uidSet.size();
    }
}
```
### 3.3 实时热更新黑名单 MBeanServer

下一步，我们要使用 JMX 来实时热更新这个 MBean，首先我们要把 MBean 注册到 MBeanServer 中，初始黑名单只有两个用户 a 和 b：
```java
// 获取 MBean Server
MBeanServer platformMBeanServer = ManagementFactory.getPlatformMBeanServer();

// 创建 MBean 初始黑名单用户为 a 和 b
BlackList blackList = new BlackList();
blackList.addBlackItem("a");
blackList.addBlackItem("b");

// 注册
ObjectName objectName = new ObjectName("com.common.example.jmx:type=BlackList, name=BlackListMBean");
platformMBeanServer.registerMBean(blackList, objectName);
```
下面我们使用 Socket 接收字符串模拟用户登录，并根据用户黑名单对用户进行拦截：
```
String hostname = "localhost";
int port = 9000;
// 循环接收
while (true) {
    // 简单从 Socket 接收字符串模拟接收到的用户Id
    try (Socket socket = new Socket()) {
        socket.connect(new InetSocketAddress(hostname, port), 0);
        try (BufferedReader reader = new BufferedReader(new InputStreamReader(socket.getInputStream()))) {
            char[] buffer = new char[8012];
            int bytes;
            while ((bytes = reader.read(buffer)) != -1) {
                String result = new String(buffer, 0, bytes);
                String uid = result;
                // 去掉换行符
                if (result.endsWith("\n")) {
                    uid = result.substring(0, result.length() - 1);
                }
                if (blackList.contains(uid)) {
                    System.out.println("[INFO] uid " + uid + " is in black list");
                } else {
                    System.out.println("[INFO] uid " + uid + " is not in black list");
                }
            }
        }
    }
    Thread.sleep(3000);
    System.out.println("[INFO] 休眠 3s ..............");
}
```

### 3.4 演示

下一步就是正常启动用户登录应用程序，打开另一个命令行窗口，输入 jconsole 命令启动 JavaSE 自带的一个 JMX 客户端程序：

![](https://github.com/sjf0115/ImageBucket/blob/main/Java/jmx-java-management-extensions-2.png?raw=true)

通过 jconsole 连接到我们当前正在运行的应用程序，在 jconsole 中可直接看到内存、CPU 等资源的监控。点击 MBean Tab，左侧按分类列出所有 MBean，可以在 com.common.example.jmx 下查看我们创建的 MBean 信息：

![](https://github.com/sjf0115/ImageBucket/blob/main/Java/jmx-java-management-extensions-3.png?raw=true)

点击 BlackList 属性，可以看到目前黑名单中用户有 a 和 b 两个用户，即默认的黑名单用户：

![](https://github.com/sjf0115/ImageBucket/blob/main/Java/jmx-java-management-extensions-4.png?raw=true)

我们在 Socket 中输入用户 a、b、c 模拟用户登录，输出日志如下：
```
[INFO] uid a is in black list
[INFO] uid b is in black list
[INFO] uid c is not in black list
```
可见，用户 a 和 b 确实被添加到了用户黑名单中了，而用户 c 不在用户黑名单中。我们点击操作 contains，填入用户 c 并点击 contains 按钮，验证用户 c 是否是在黑名单中，如下图所示用户 c 确实不在黑名单中：

![](https://github.com/sjf0115/ImageBucket/blob/main/Java/jmx-java-management-extensions-5.png?raw=true)

现在我们希望用户 c 也添加在黑名单中，点击操作 addBlackItem，填入用户 c 并点击 addBlackItem 按钮。相当于 jconsole 通过 JMX 接口调用了我们自己的 BlacklistMBean 的 addBlackItem() 方法，传入的参数就是填入的用户 c：

![](https://github.com/sjf0115/ImageBucket/blob/main/Java/jmx-java-management-extensions-6.png?raw=true)

再次查看属性 blackList，可以看到结果已经更新了。我们在 Socket 中输入用户 c 模拟用户登录，测试一下黑名单功能是否已生效：
```
[INFO] uid c is in black list
```
可见，用户 c 确实被添加到了黑名单中了。我们调用 removeBlackItem 移除用户 a：

![](https://github.com/sjf0115/ImageBucket/blob/main/Java/jmx-java-management-extensions-7.png?raw=true)

我们在 Socket 中输入用户 a 模拟用户登录测试一下黑名单功能是否生效：
```
[INFO] uid a is not in black list
```
可见，用户 a 确实从用户黑名单中移除了。
