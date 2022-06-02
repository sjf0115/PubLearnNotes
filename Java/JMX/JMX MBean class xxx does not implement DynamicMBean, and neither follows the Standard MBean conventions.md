## 1 现象

在运行标准 MBean 的示例时：
```java
public class MBeanServerRegister {
    public static void main(String[] args) throws Exception {
        // 获取 MBean Server
        MBeanServer platformMBeanServer = ManagementFactory.getPlatformMBeanServer();
        // 创建 MBean
        CustomResource resource = new CustomResource();
        resource.addItem("item_1");
        resource.addItem("item_2");
        resource.addItem("item_3");
        // 注册
        ObjectName objectName = new ObjectName("com.common.example.jmx:type=CustomResource, name=CustomResourceMBean");
        platformMBeanServer.registerMBean(resource, objectName);
        // 防止退出
        while (true) {
            Thread.sleep(3000);
            System.out.println("[INFO] 休眠 3s ..............");
        }
    }
}
```
抛出如下异常：
```java
Exception in thread "main" javax.management.NotCompliantMBeanException: MBean class com.common.example.jmx.CustomResource does not implement DynamicMBean, and neither follows the Standard MBean conventions (javax.management.NotCompliantMBeanException: Class com.common.example.jmx.CustomResource is not a JMX compliant Standard MBean) nor the MXBean conventions (javax.management.NotCompliantMBeanException: com.common.example.jmx.CustomResource: Class com.common.example.jmx.CustomResource is not a JMX compliant MXBean)
	at com.sun.jmx.mbeanserver.Introspector.checkCompliance(Introspector.java:176)
	at com.sun.jmx.interceptor.DefaultMBeanServerInterceptor.registerMBean(DefaultMBeanServerInterceptor.java:317)
	at com.sun.jmx.mbeanserver.JmxMBeanServer.registerMBean(JmxMBeanServer.java:522)
	at com.common.example.jmx.MBeanServerRegister.main(MBeanServerRegister.java:26)
	at sun.reflect.NativeMethodAccessorImpl.invoke0(Native Method)
	at sun.reflect.NativeMethodAccessorImpl.invoke(NativeMethodAccessorImpl.java:62)
	at sun.reflect.DelegatingMethodAccessorImpl.invoke(DelegatingMethodAccessorImpl.java:43)
	at java.lang.reflect.Method.invoke(Method.java:498)
	at com.intellij.rt.execution.application.AppMain.main(AppMain.java:144)
```
需要注意的是，标准 MBean 接口名称必需是在要监控的类名后面加上 MBean 后缀, 且要监控的类和 MBean 接口必需在同一包下。假设标准 MBean 接口名称为 ResourceMBean，那么实现 ResourceMBean 接口的实现类必须为 Resource：
```java
public class Resource implements ResourceMBean {
  ...
}
```
而此时我们的实现类名称为 CustomResource，所以抛出异常。
