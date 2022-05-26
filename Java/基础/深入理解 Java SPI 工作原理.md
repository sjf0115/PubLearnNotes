
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

### 3.1 ServiceLoader.load 初始化

从上面可以知道入口在 ServiceLoader.load 方法中：
```java
public static <S> ServiceLoader<S> load(Class<S> service) {
    // 获取当前线程上下文类加载器
    ClassLoader cl = Thread.currentThread().getContextClassLoader();
    // 将 service 接口类和线程上下文类加载器作为参数传入，继续调用 load 重载方法
    return ServiceLoader.load(service, cl);
}

public static <S> ServiceLoader<S> load(Class<S> service, ClassLoader loader) {
    // 创建 ServiceLoader 对象
    return new ServiceLoader<>(service, loader);
}
```
使用当前线程的 Thread#getContextClassLoader 方法获取上下文类加载器。将 service 接口类和线程上下文类加载器作为参数传入 load 重载方法中，继续调用 load 重载方法，创建一个 ServiceLoader 对象：
```java
public final class ServiceLoader<S> implements Iterable<S> {
  private final Class<S> service;
  private final ClassLoader loader;
  private final AccessControlContext acc;
  // 构造函数
  private ServiceLoader(Class<S> svc, ClassLoader cl) {
      // 指定类不能为null
      service = Objects.requireNonNull(svc, "Service interface cannot be null");
      // 如果类加载器为null则使用应用程类加载器(系统类加载器)
      loader = (cl == null) ? ClassLoader.getSystemClassLoader() : cl;
      acc = (System.getSecurityManager() != null) ? AccessController.getContext() : null;
      // 调用 reload 方法
      reload();
  }

  public Iterator<S> iterator() {
    ...
  }
}
```

![](31)

从上面我们看到了 ServiceLoader 的整体框架：ServiceLoader 实现了 Iterable 接口，并重写了 iterator 方法产生一个迭代器。可以看到在构建 ServiceLoader 对象时除了给其成员属性赋值外，还调用了 reload 方法：
```java
// 缓存 service 接口实现类的实例
private LinkedHashMap<String,S> providers = new LinkedHashMap<>();
private LazyIterator lookupIterator;

public void reload() {
    // 清空 providers
    providers.clear();
    // 创建 LazyIterator 对象
    lookupIterator = new LazyIterator(service, loader);
}
```
providers 其实是一个 LinkedHashMap，用来缓存读取到的 META-INFO.services 文件夹下 service 接口实现类的实例，所以在创建 ServiceLoader 对象的时，首先清空缓存中的数据。此外还创建了一个 LazyIterator 对象：
```java
private class LazyIterator implements Iterator<S> {
    Class<S> service;
    ClassLoader loader;
    private LazyIterator(Class<S> service, ClassLoader loader) {
        this.service = service;
        this.loader = loader;
    }

    private boolean hasNextService() {
        ...
    }

    private S nextService() {
        ...
    }

    public boolean hasNext() {
        ...
    }

    public S next() {
        ...
    }

    public void remove() {
     ...
    }
}
```
可以看到在创建 LazyIterator 对象时，也只是给其成员变量 service 和 loader 变量赋值，我们一直也没有看到去 META-INF/services 文件夹下读取 service 接口的实现类。其实 ServiceLoader 的 load 方法只是做初始化工作，并不做加载工作。真正的工作是交给了 LazyIterator 对象。Lazy 顾名思义是懒的意思，Iterator就是迭代的意思。我们猜测 LazyIterator 对象的作用是在迭代的时候再去加载 service 接口的实现类。

### 3.2 ServiceLoader.iterator 懒加载

通过上面我们知道 ServiceLoader 的 load 方法只是做初始化工作，并不做加载工作。真正的加载还是需要 ServiceLoader 实例的 iterator 方法：
```java
Iterator<Sink> iterator = sinkServiceLoader.iterator();
```
其实在上面构造 ServiceLoader 对象时，我们知道 ServiceLoader 不仅实现了 Iterable 接口，并重写了 iterator 方法产生一个迭代器。这个 iterator 方法就是我们要将的 iterator 方法。下面我们一起看一下 iterator 方法是如何执行的：
```java
public Iterator<S> iterator() {
    // 返回一个迭代器
    return new Iterator<S>() {
        Iterator<Map.Entry<String,S>> knownProviders
            = providers.entrySet().iterator();
        public boolean hasNext() {
            if (knownProviders.hasNext())
                return true;
            return lookupIterator.hasNext();
        }
        public S next() {
            if (knownProviders.hasNext())
                return knownProviders.next().getValue();
            return lookupIterator.next();
        }
        public void remove() {
            throw new UnsupportedOperationException();
        }
    };
}
```
在 Iterator 接口 hasNext() 和 next() 方法匿名实现中，首先会从全局变量 providers 中判断是否已经缓存了服务提供方的实现类，如果已缓存，直接返回结果；如果还未缓存，则会继续调用 LazyIterator 类中对应的 hasNext() 和 next() 方法。

#### 3.2.1 hasNext 与 next

在 LazyIterator 类内部实现中，hasNext() 方法逻辑主要在 hasNextService() 方法中完成，next() 方法逻辑主要在 nextService() 方法中完成：
```java
public boolean hasNext() {
    if (acc == null) {
        // 调用 hasNextService 实现
        return hasNextService();
    } else {
        PrivilegedAction<Boolean> action = new PrivilegedAction<Boolean>() {
            public Boolean run() { return hasNextService(); }
        };
        return AccessController.doPrivileged(action, acc);
    }
}

public S next() {
    if (acc == null) {
        // nextService
        return nextService();
    } else {
        PrivilegedAction<S> action = new PrivilegedAction<S>() {
            public S run() { return nextService(); }
        };
        return AccessController.doPrivileged(action, acc);
    }
}
```

#### 3.2.2 hasNextService  

hasNext() 方法逻辑主要在 hasNextService() 方法中完成，具体看看 hasNextService 是如何实现的。如果没有指定类加载器 loader 则使用 ClassLoader.getSystemResources 方法加载配置文件，否则会使用指定类加载器 loader 的 getResources 方法加载。具体加载哪些配置文件呢？我可以看到 PREFIX 实际上是 META-INF/services/ 目录，service.getName() 是接口的全限定名，所以类加载器会查找 META-INF/services/ 目录下以 service.getName() 方法获取接口的全限定名的配置文件，缓存在 configs 对象中：
```java
private boolean hasNextService() {
    // 是否有下一个全限定名
    if (nextName != null) {
        return true;
    }
    // 1. 加载配置文件(可能会有多个)
    if (configs == null) {
        try {
            // PREFIX 为 META-INF/services/
            // service.getName() 接口的全限定名
            String fullName = PREFIX + service.getName();
            if (loader == null)
                configs = ClassLoader.getSystemResources(fullName);
            else
                configs = loader.getResources(fullName);
        } catch (IOException x) {
            fail(service, "Error locating configuration files", x);
        }
    }
    // 2. pending 为实现类全限定名的迭代器 每次首先检查其是否有直接可用的
    while ((pending == null) || !pending.hasNext()) {
        // 是否有可供解析的配置文件
        if (!configs.hasMoreElements()) {
            return false;
        }
        // 解析配置文件获取实现类的全限定名(可能会有多个)
        pending = parse(service, configs.nextElement());
    }
    nextName = pending.next();
    return true;
}
```
我们可以看到 hasNextService 做了初始化加载配置文件以及解析配置文件内容的工作，具体流程如下图所示：

![]()

nextName 变量存储下一个可以获取的接口实现类的全限定名，首先判断 nextName 变量是否有可以直接获取的全限定名，如果有直接返回 true；如果没有，则需要判断是否加载过配置文件，只有当 configs 对象为 null 时，即从来没有加载过配置文件时，才会根据指定的文件名加载配置文件(可能会有多个，如上面示例就会有两个配置文件)，配置文件信息存储在 configs 对象中。如果之前加载过，就不会再去加载一次；下一步检查全限定名缓存队列 pending(字符串数组的迭代器)中是否有可用的全限定名，如果有直接取出一个存储在 nextName 变量中，后续 nextService 方法直接使用这个变量获取全限定名即可；如果没有，需要从加载完的配置文件中解析出接口实现类的全限定名(一个配置文件中可能会有多个全限定名，如上面示例就有两个：com.connector.FileSink 和 com.connector.HdfsSink)。解析出来的多个全限定名缓存在队列 pending 中。每次调用 hasNextService，都会首先从 pending 中取出一个全限定名，只有没有时才会考虑去解析配置文件。

#### 3.2.3 nextService

可以看到会在 nextService 方法中实现服务提供者实现类的实例化，并放进 providers 集合中：
```java
private S nextService() {
    // 是否有下一个
    if (!hasNextService())
        throw new NoSuchElementException();
    // 从 nextName 中取出下一个接口实现类的全限定名
    String cn = nextName;
    // 取走之后赋为 null，表示没有下一个了，需要从 pending 中重新获取
    nextName = null;
    Class<?> c = null;
    try {
        // 根据全限定名加载类
        c = Class.forName(cn, false, loader);
    } catch (ClassNotFoundException x) {
        fail(service, "Provider " + cn + " not found");
    }
    if (!service.isAssignableFrom(c)) {
        fail(service, "Provider " + cn  + " not a subtype");
    }
    try {
        // 创建对象
        S p = service.cast(c.newInstance());
        // 缓存到全局的 LinkedHashMap 中
        providers.put(cn, p);
        return p;
    } catch (Throwable x) {
        fail(service, "Provider " + cn + " could not be instantiated",x);
    }
    throw new Error(); // This cannot happen
}
```
在 hasNextService() 方法中只是完成了配置文件的加载与解析，我们得到了服务提供者实现类的全限定名的字符串，并没有真正完成具体实现类的实例化，真正类的实例化是在调用 nextService() 方法中完成的。


参考：
- https://dongzl.github.io/2021/01/16/04-Java-Service-Provider-Interface/
- https://www.cnblogs.com/warehouse/p/9335530.html
- https://www.jianshu.com/p/32370d9b9046
- https://blog.csdn.net/top_code/article/details/51934459
- https://mp.weixin.qq.com/s/y6HrRDUqWnYclLcVaCVYqA
- https://mp.weixin.qq.com/s/20t_UtNNwXfynbzxpi7p2Q
- https://mp.weixin.qq.com/s/vpy5DJ-hhn0iOyp747oL5A
-
