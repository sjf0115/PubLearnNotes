

Java Management Extension (JMX) 是一种远程管理和监视 Java 应用程序的技术。JMX 架构主要由如下组件组成：
- Managed Beans（MBeans）：可以通过 JMX 远程管理和监控
- JMX 代理：管理 MBean 并提供一个接口，以便可以远程访问
- 远程管理应用程序：通过 JMX 代理监视 MBean 并与之交互

MBean 需要一个管理接口来定义可以管理和监视的属性和操作。管理接口包含以下内容：
- 可以读写的属性
- 操作
- 通知

JMX 规范定义了五种类型的 MBean：
- Standard MBean：这是最简单的一种 MBean。它们的管理接口由它们的方法名称定义。
- Dynamic MBean：MBean 的管理接口在运行时定义。
- Open MBean：一种依赖基本数据类型实现通用管理的动态 MBean。这确保远程客户端不需要任何特定于应用程序的编译类来与 MBean 通信。
- Model MBean：它们是在运行时可配置和自我描述的动态 MBean。它们为资源的动态检测提供具有默认行为的 MBean 类。
- MXBean：MXBean 与 Standard MBean 比较类似，但使用类似于 Open MBean 的通用数据类型。

在本篇文章中，我们将只研究 Standard Bean 和 MXBean。我们还将了解如何利用 SpringFramework 轻松注册 MBean。

## 1. Standard MBeans



## 2. MXBean


https://blog.csdn.net/expleeve/article/details/37502501






参考：http://actimem.com/java/jmx/
