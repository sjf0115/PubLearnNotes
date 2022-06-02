
## 1. 什么是 JMX

JMX，全称 Java Management Extensions，是在 J2SE 5.0 版本中引入的一个功能。提供了一种在运行时动态管理资源的框架，主要用于企业应用程序中实现可配置或动态获取应用程序的状态。

JMX 提供了一种简单、标准的监控和管理资源的方式，对于如何定义一个资源给出了明确的结构和设计模式，主要用于监控和管理应用程序运行状态、资源信息、Java 虚拟机运行情况等信息。JMX 是可以动态的，可以在资源创建、安装、实现时进行动态监控和管理。

## 2. JMX 架构

要通过 JMX 管理资源，我们需要创建 Managed Bean (简称 MBean)来表示要管理的资源，然后将其注册到 MBean Server 中。MBean Server 作为所有已注册 MBean 的管理代理，实现对外提供服务以及对内管理 MBean 资源。

JMX 不仅仅用于本地管理，JMX Remote API 为 JMX 添加了远程功能，使之可以通过网络远程监视和管理应用程序。我们可以使用 JMX Connector 连接到 MBean Server 并管理注册的资源。例如，可以使用 JDK 自带的 JConsole 连接到本地或远程 MBean Server。

### 2.1 资源管理 MBean

资源管理在架构中标识为资源探测层（Probe Level），在 JMX 中，使用 MBean 或 MXBean 来表示一个资源（下面简称 MBean），访问和管理资源也都是通过 MBean，所以 MBean 往往包含着资源的属性和操作方法。

下面列举 JMX 对 JVM 的资源检测类，都可以直接使用。

Java 虚拟机具有以下管理接口的单个实例：

| 资源接口 | 管理的资源 | Object Name | Java 虚拟机中的实例个数 |
| :------------- | :------------- | :------------- | :------------- |
| ClassLoadingMXBean     | 类加载的 | java.lang:type=ClassLoading  | 1个 |
| MemoryMXBean	         | 内存系统	| java.lang:type=Memory | 1个 |
| ThreadMXBean	         | 线程系统	  | java.lang:type=Threading	| 1个 |
| RuntimeMXBean	         | 运行时系统 | java.lang:type=Runtime	| 1个 |
| OperatingSystemMXBean	 | 操作系统	| java.lang:type=OperatingSystem	| 1个 |
| PlatformLoggingMXBean	 | 日志系统	| java.util.logging:type=Logging	| 1个 |
| CompilationMXBean	     | 汇编系统 | java.lang:type=Compilation	 | 0个或1个 |
| GarbageCollectorMXBean | 垃圾收集	| java.lang:type=GarbageCollector,name=<collector名称> | 1个或更多 |
| MemoryManagerMXBean	   | 内存池	 | java.lang:typeMemoryManager,name=<manager名称> | 1个或更多 |
| MemoryPoolMXBean	     | 内存	   | java.lang:type=MemoryPool,name=<pool名称>	| 1个或更多 |
| BufferPoolMXBean	     | Buffer | java.nio:type=BufferPool,name=<pool名称> | 1个或更多 |



JMX 已经对 JVM 进行了多维度资源检测，所以可以轻松启动 JMX 代理来访问内置的 JVM 资源检测，从而通过 JMX 技术远程监控和管理 JVM。

### 2.2 资源代理 MBean Server

资源代理 MBean Server 是 MBean 资源的代理，通过 MBean Server 可以让 MBean 资源用于远程管理，MBean 资源和 MBean Server 往往都是在同一个 JVM 中，但这不是必须的。

想要 MBean Server 可以管理 MBean 资源，首先要把资源注册到 MBean Server，任何符合 JMX 的 MBean 资源都可以进行注册，最后 MBean Server 会暴露一个远程通信接口对外提供服务。

### 2.3 JMX 远程管理

可以通过网络协议访问 JMX API，如 HTTP 协议、SNMP（网络管理协议）协议、RMI 远程调用协议等，JMX 技术默认实现了 RMI 远程调用协议。

受益于资源管理 MBean 的充分解耦，可以轻松的把资源管理功能扩展到其他协议，如通过 HTTP 在网页端进行管理。



## 3 实战

在这里，我们将学习 JMX 的基础知识以及如何使用 JConsole 连接和管理 MBean。让我们现在开始…

首先，我们需要创建 MBean，为此我们需要首先创建定义我们想要公开的属性和操作的接口。 接口名称必须以 MBean 结尾。 如果您只想允许只读，则可以保留 setter 方法。

应用程序可以通过以下方式访问平台 MXBean：

1. 直接访问一个 MXBean 接口
- 通过调用 getPlatformMXBean 或 getPlatformMXBeans 方法获取 MXBean 实例，并在正在运行的虚拟机中本地访问 MXBean。
- 构造一个 MXBean 代理实例，通过调用 getPlatformMXBean(MBeanServerConnection, Class) 或 getPlatformMXBeans(MBeanServerConnection, Class) 方法将方法调用转发到给定的 MBeanServer。 newPlatformMXBeanProxy 方法还可用于构造-给定 ObjectName 的 MXBean 代理实例。代理通常被构造为远程访问另一个正在运行的虚拟机的 MXBean。

2.通过MBeanServer间接访问一个MXBean接口
- 通过平台 MBeanServer 本地访问 MXBean 或通过特定的 MBeanServerConnection 远程访问 MXBean。 MXBean 的属性和操作仅使用 JMX 开放类型，包括 OpenType 中定义的基本数据类型、CompositeData 和 TabularData。详细信息在 MXBean 规范中指定了映射。
