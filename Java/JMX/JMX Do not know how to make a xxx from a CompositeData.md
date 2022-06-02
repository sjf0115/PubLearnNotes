## 1. 现象

```java
Exception in thread "main" javax.management.NotCompliantMBeanException: com.common.example.jmx.ResourceMXBean: java.io.InvalidObjectException: Do not know how to make a com.common.example.bean.ResourceItem from a CompositeData: no method from(CompositeData); no constructor has @ConstructorProperties annotation; does not have a public no-arg constructor; not an interface
	at com.sun.jmx.mbeanserver.Introspector.throwException(Introspector.java:466)
	at com.sun.jmx.mbeanserver.MBeanIntrospector.getPerInterface(MBeanIntrospector.java:200)
	at com.sun.jmx.mbeanserver.MBeanSupport.<init>(MBeanSupport.java:138)
	at com.sun.jmx.mbeanserver.MXBeanSupport.<init>(MXBeanSupport.java:66)
	at com.sun.jmx.mbeanserver.Introspector.makeDynamicMBean(Introspector.java:202)
	at com.sun.jmx.interceptor.DefaultMBeanServerInterceptor.registerObject(DefaultMBeanServerInterceptor.java:898)
	at com.sun.jmx.interceptor.DefaultMBeanServerInterceptor.registerMBean(DefaultMBeanServerInterceptor.java:324)
	at com.sun.jmx.mbeanserver.JmxMBeanServer.registerMBean(JmxMBeanServer.java:522)
	at com.common.example.jmx.MXBeanServerRegister.main(MXBeanServerRegister.java:29)
	at sun.reflect.NativeMethodAccessorImpl.invoke0(Native Method)
	at sun.reflect.NativeMethodAccessorImpl.invoke(NativeMethodAccessorImpl.java:62)
	at sun.reflect.DelegatingMethodAccessorImpl.invoke(DelegatingMethodAccessorImpl.java:43)
	at java.lang.reflect.Method.invoke(Method.java:498)
	at com.intellij.rt.execution.application.AppMain.main(AppMain.java:144)
Caused by: java.lang.IllegalArgumentException: java.io.InvalidObjectException: Do not know how to make a com.common.example.bean.ResourceItem from a CompositeData: no method from(CompositeData); no constructor has @ConstructorProperties annotation; does not have a public no-arg constructor; not an interface
	at com.sun.jmx.mbeanserver.ConvertingMethod.checkCallFromOpen(ConvertingMethod.java:94)
	at com.sun.jmx.mbeanserver.MXBeanIntrospector.checkMethod(MXBeanIntrospector.java:109)
	at com.sun.jmx.mbeanserver.MXBeanIntrospector.checkMethod(MXBeanIntrospector.java:54)
	at com.sun.jmx.mbeanserver.PerInterface$InitMaps.visitOperation(PerInterface.java:252)
	at com.sun.jmx.mbeanserver.MBeanAnalyzer.visit(MBeanAnalyzer.java:74)
	at com.sun.jmx.mbeanserver.PerInterface.<init>(PerInterface.java:54)
	at com.sun.jmx.mbeanserver.MBeanIntrospector.getPerInterface(MBeanIntrospector.java:195)
	... 12 more
Caused by: java.io.InvalidObjectException: Do not know how to make a com.common.example.bean.ResourceItem from a CompositeData: no method from(CompositeData); no constructor has @ConstructorProperties annotation; does not have a public no-arg constructor; not an interface
	at com.sun.jmx.mbeanserver.DefaultMXBeanMappingFactory.invalidObjectException(DefaultMXBeanMappingFactory.java:1457)
	at com.sun.jmx.mbeanserver.DefaultMXBeanMappingFactory$CompositeMapping.makeCompositeBuilder(DefaultMXBeanMappingFactory.java:905)
	at com.sun.jmx.mbeanserver.DefaultMXBeanMappingFactory$CompositeMapping.checkReconstructible(DefaultMXBeanMappingFactory.java:912)
	at com.sun.jmx.mbeanserver.ConvertingMethod.checkCallFromOpen(ConvertingMethod.java:92)
	... 18 more
```

## 2. 解决方案

实现 MXBean 接口类 ResourceX 时，引用的 ResourceItem 实体类必须具有一个 public 的无参构造函数：
```java
public class ResourceX implements ResourceMXBean {
    private List<ResourceItem> items = new ArrayList<>();
    @Override
    public ResourceItem getLastItem() {
        return items.get(getSize()-1);
    }
    @Override
    public int getSize() {
        return items.size();
    }
    @Override
    public List<ResourceItem> getItems() {
        return items;
    }
    @Override
    public void addItem(ResourceItem item) {
        items.add(item);
    }
    @Override
    public ResourceItem getItem(int pos) {
        return items.get(pos);
    }
}

public class ResourceItem {
    private String name;
    private int age;

    public ResourceItem() {
    }

    public ResourceItem(String name, int age) {
        this.name = name;
        this.age = age;
    }
    ...
}
```
