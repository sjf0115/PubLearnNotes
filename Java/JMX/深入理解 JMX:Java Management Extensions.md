
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

我们以实际问题为例，假设我们希望给应用程序添加一个用户黑名单功能，凡是在黑名单中的用户禁止访问，传统的做法是定义一个配置文件，启动的时候读取：
```
# blacklist.txt
a
b
...
```
如果要修改黑名单怎么办？修改配置文件，然后重启应用程序。但是每次都重启应用程序实在是太麻烦了，能不能不重启应用程序？可以自己写一个定时读取配置文件的功能，检测到文件改动时自动重新读取。上述需求本质上是在应用程序运行期间对参数、配置等进行热更新并要求尽快生效。

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

MBean 有一个规则，标准 MBean 接口名称必需是在要实现类名后面加上 MBean 后缀, 并且实现类必须和 MBean 接口必需在同一包下。所以我们的黑名单管理实现类必须为 BlackList，其中定义了一个 uidSet 集合存储用户黑名单：
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
### 3.3 实时热更新 MBean

```java
public class BlackListServer {
    public static void main(String[] args) throws Exception {
        String hostname = "localhost";
        int port = 9000;
        // 获取 MBean Server
        MBeanServer platformMBeanServer = ManagementFactory.getPlatformMBeanServer();

        // 创建 MBean 初始黑名单用户为 a 和 b
        BlackList blackList = new BlackList();
        blackList.addBlackItem("a");
        blackList.addBlackItem("b");

        // 注册
        ObjectName objectName = new ObjectName("com.common.example.jmx:type=BlackList, name=BlackListMBean");
        platformMBeanServer.registerMBean(blackList, objectName);

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
    }
}
```
