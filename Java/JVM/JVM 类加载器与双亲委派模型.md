---
layout: post
author: sjf0115
title: JVM 类加载器与双亲委派模型
date: 2022-05-15 17:40:01
tags:
  - Java
  - JVM

categories: Java
permalink: jvm-class-loader-parents-delegation-model
---

## 1. 类加载器

我们知道，虚拟机在加载类的过程中需要使用类加载器进行加载，而在 Java 中，类加载器有很多，那么当 JVM 想要加载一个 `.class` 文件的时候，到底应该由哪个类加载器加载呢？这时候就需要双亲委派机制来告诉 JVM 使用哪个类加载器加载。在讲解什么是双亲委派机制之前，我们先看一下有哪些加载器。

从 Java 虚拟机的角度来讲，只存在两种不同的类加载器：一种是启动类加载器 Bootstrap ClassLoader，这个类加载器使用 C++ 语言实现，是虚拟机自身的一部分；另一种就是所有其他的类加载器，这些类加载器都由 Java 语言实现，独立于虚拟机外部，并且全都继承自抽象类 java.lang.ClassLoader。从 Java 开发人员的角度来看，类加载器还可以划分得更细致一些，分为用户级别和系统级别类加载器。用户级别的类加载器我们统一称为自定义类加载器，而系统级别的类加载器有：
- 启动类加载器：Bootstrap ClassLoader
- 扩展类加载器：Extention ClassLoader
- 应用程序类加载器：Application ClassLoader

### 1.1 启动类加载器

启动类加载器 Bootstrap ClassLoader 使用 C/C++ 语言实现，负责将存放在 `<JAVA_HOME>\lib` 目录中的，或者被 `-Xbootclasspath` 参数所指定的路径中的，并且是虚拟机识别的（仅按照文件名识别，如 rt.jar，名字不符合的类库即使放在lib目录中也不会被加载）类库加载到虚拟机内存中。启动类加载器无法被 Java 程序直接引用，用户在编写自定义类加载器时，如果需要把加载请求委派给引导类加载器，那直接使用 null 代替即可。

可以通过如下代码查看启动类加载器可以加载哪些路径的 jar：
```java
String bootStrapPath = System.getProperty("sun.boot.class.path");
System.out.println("启动类加载器加载的路径: ");
for (String paths : bootStrapPath.split(";")){
    for (String path : paths.split(":")) {
        System.out.println(path);
    }
}
```

### 1.2 扩展类加载器

扩展类加载器 Extension ClassLoader 由 Java 语言编写，并由 `sun.misc.Launcher$ExtClassLoader` 实现，父类加载器为启动类加载器。负责加载 `<JAVA_HOME>\lib\ext` 目录中的，或者被 `java.ext.dirs` 系统变量所指定的路径中的所有类库。开发者可以直接使用扩展类加载器，如果用户创建的 JAR 放在扩展目录下，也会自动由扩展类加载器加载。

可以通过如下代码查看扩展类加载器可以加载哪些路径的 jar：
```java
String extClassLoaderPath = System.getProperty("java.ext.dirs");
System.out.println("拓展类加载器加载的路径: ");
for (String paths : extClassLoaderPath.split(";")){
    for (String path : paths.split(":")) {
        System.out.println(path);
    }
}
```

#### 1.3 应用程序类加载器

应用程序类加载器 Application ClassLoader 由 Java 语言编写，并由 `sun.misc.Launcher$App-ClassLoader` 实现，父类加载器为扩展类加载器。由于这个类加载器是 ClassLoader 中的 getSystemClassLoader() 方法的返回值，所以一般也称它为系统类加载器。它负责加载用户类路径 ClassPath 或系统属性 `java.class.path` 指定路径下的类库。开发者可以直接使用这个类加载器，如果应用程序中没有自定义过自己的类加载器，一般情况下这个就是程序中默认的类加载器。

可以通过如下代码查看应用程序类加载器可以加载哪些路径的 jar：
```java
String appClassLoaderPath = System.getProperty("java.class.path");
for (String paths : appClassLoaderPath.split(";")){
    System.out.println("应用程序类加载器加载的路径: ");
    for (String path : paths.split(":")) {
        System.out.println(path);
    }
}
```

#### 1.4 自定义类加载器

在 Java 的日常应用程序开发中，类的加载几乎是由上述 3 种类加载器相互配合执行的，在必要时，我们还可以自定义类加载器，来定制类的加载方式。那么什么场景下需要自定义类加载器呢？
- 隔离加载类
- 修改类加载的方式
- 扩展加载源
- 防止源码泄漏

开发人员可以通过继承抽象类 java.lang.ClassLoader 类的方式，实现自己的类加载器，以满足一些特殊的需求。在 JDK 1.2 之前，在自定义类加载器时，总会去继承 ClassLoader 类并重写 loadClass() 方法，从而实现自定义的类加载类，但是在 JDK 1.2 之后已不再建议用户去覆盖 loadClass() 方法，而是建议把自定义的类加载逻辑写在 findclass() 方法中。

第一步自定义一个实体类 Car.java：
```java
// 测试对象 Car
public class Car {
    public Car() {
        System.out.println("welcome you");
    }

    public void print() {
        System.out.println("this is a car");
    }
}
```
第二步自定义一个类加载器，我们自定义的 CustomClassLoader 继承自 java.lang.ClassLoader，且只实现 findClass 方法：
```java
// 自定义加载器
public class CustomClassLoader extends ClassLoader{
    private String path;
    public CustomClassLoader(String path) {
        this.path = path;
    }

    @Override
    protected Class<?> findClass(String name) throws ClassNotFoundException {
        System.out.println("CustomClassLoader: " + name);
        try {
            String fileName = path + "/" + name.substring(name.lastIndexOf(".") + 1) + ".class";
            FileInputStream inputStream = new FileInputStream(fileName);
            if (inputStream == null) {
                return super.findClass(name);
            }
            byte[] bytes = new byte[inputStream.available()];
            inputStream.read(bytes);
            return defineClass(name, bytes, 0, bytes.length);
        } catch (IOException ex) {
            throw new ClassNotFoundException(name, ex);
        }
    }
}
```
第三步演示自定义类加载器如何使用：
```java
CustomClassLoader myClassLoader = new CustomClassLoader("/opt/data");
Class<?> myClass = myClassLoader.loadClass("com.common.example.bean.Car");
// 创建对象实例
Object o = myClass.newInstance();
// 调用方法
Method print = myClass.getDeclaredMethod("print", null);
print.invoke(o, null);
// 输出类加载器
System.out.println("ClassLoader: " + o.getClass().getClassLoader());
```
直接运行上述代码，会输出如下结果：
```
welcome you
this is a car
ClassLoader: sun.misc.Launcher$AppClassLoader@49476842
```
从上面看到输出结果并不符合我们的预期，Car 类使用的应用程序类加载器加载的，并不是我们自定义的类加载器。这个问题主要是因为 Idea 编译后会存放在 target/classes 目录下

![](https://github.com/sjf0115/ImageBucket/blob/main/Java/jvm-class-loader-parents-delegation-model-1.png?raw=true)

而这个目录正好是应用程序类加载的路径，可以使用[]()代码验证。为了解决这个问题，我们可以把 Car.class 移动到 /opt/data 目录下（删除 target/classes 目录下的 Car.class 文件，避免由应用程序类加载器加载）。再次运行输出如下结果：
```
CustomClassLoader: com.common.example.bean.Car
welcome you
this is a car
ClassLoader: com.common.example.jvm.classLoader.CustomClassLoader@4617c264
```

## 2. 什么是双亲委派模型

上述四种类加载器之间存在着一种层次关系，如下图所示：

![](https://github.com/sjf0115/ImageBucket/blob/main/Java/jvm-class-loader-parents-delegation-model-2.png?raw=true)

一般认为上一层加载器是下一层加载器的父类加载器，除了启动类加载器 BootstrapClassLoader 之外，所有的加载器都是有父类加载器。我们可以先通过如下代码来看一下类加载器的层级结构：
```java
// 应用程序类加载器(系统类加载器)
ClassLoader systemClassLoader = ClassLoader.getSystemClassLoader();
System.out.println(systemClassLoader); // sun.misc.Launcher$AppClassLoader@49476842

// 获取上层加载器:扩展类加载器
ClassLoader extClassLoader = systemClassLoader.getParent();
System.out.println(extClassLoader); // sun.misc.Launcher$ExtClassLoader@5acf9800

// 获取上层加载器:启动类加载器
ClassLoader bootstrapClassLoader = extClassLoader.getParent();
System.out.println(bootstrapClassLoader); // null
```
在上述代码中依次输出 ClassLoaderParent 类的类加载器，父类加载器以及父类的父类加载器。可以看到当前类的加载器是应用程序类加载器，它的父类亲加载器是扩展类加载器，扩展类加载器的父类输出了一个 null，这个 null 会去调用启动类加载器。后续通过 ClassLoader 类的源码我们可以知道这一点。

那到底什么是双亲委派模型呢？其实我们把上述类加载器之间的这种层次关系，我们称为类加载器的双亲委派模型（Parents Delegation Model）。双亲委派模型要求除了顶层的启动类加载器外，其余的类加载器都应当有自己的父类加载器。这里类加载器之间的父子关系一般不会以继承（Inheritance）的关系来实现，而是都使用组合（Composition）关系来复用父加载器的代码。

类加载器的双亲委派模型是在 JDK 1.2 期间被引入并被广泛应用于之后几乎所有的 Java 程序中。但它并不是一个强制性的约束模型，而是 Java 设计者推荐给开发者的一种类加载器实现方式。

我们从概念上知道了什么是双亲委派模型，那它到底是用来做什么的呢？双亲委派模型的工作过程是：如果一个类加载器收到了类加载的请求，它首先不会自己去尝试加载这个类，而是把这个请求委派给父类加载器去完成，每一个层次的类加载器都是如此，因此所有的加载请求最终都委派到顶层的启动类加载器中，只有当父加载器反馈自己无法完成这个加载请求（它的搜索范围中没有找到所需的类）时，子加载器才会尝试自己去加载。

## 3. 为什么需要双亲委派模型

如上面我们提到的，因为类加载器之间有严格的层次关系，那么也就使得 Java 类也随之具备了一种带有优先级的层次关系。例如类 java.lang.Object，它存放在 rt.jar 之中，无论哪一个类加载器要加载这个类，但最终都委派给最顶层的启动类加载器进行加载，因此 Object 类在程序的各种类加载器环境中都是同一个类。相反，如果没有使用双亲委派模型，由各个类加载器自行去加载的话，如果用户自己编写了一个称为 java.lang.Object 的类，并放在程序的 ClassPath 中，那系统中将会出现多个不同的 Object 类，Java 类型体系中最基础的行为也就无法保证，应用程序也将会变得一片混乱。

通过上面我们可以知道双亲委派模型的核心是保障类加载的唯一性和安全性：
- 唯一性：可以避免类的重复加载，当父类加载器已经加载过某一个类时，子加载器就不会再重新加载这个类。例如上述提及的 java.lang.Object 类，最终都委派给最顶层的启动类加载器进行加载，因此 Object 类在程序的各种类加载器环境中都是同一个类。
- 安全性：保证了 Java 的核心 API 不被篡改。因为启动类加载器 Bootstrap ClassLoader 在加载的时候，只会加载 JAVA_HOME 中的 jar 包里面的类，如 java.lang.Object，那么就可以避免加载自定义的有破坏能力的 java.lang.Object。

## 4. 双亲委派模型是怎么实现的

双亲委派模型对于保证 Java 程序的稳定运作很重要，但它的实现却非常简单，实现双亲委派的代码都集中在 java.lang.ClassLoader 的 loadClass() 方法之中：
```java
protected Class<?> loadClass(String name, boolean resolve) throws ClassNotFoundException {
    synchronized (getClassLoadingLock(name)) {
        // 首先检查类是否已经被加载过
        Class<?> c = findLoadedClass(name);
        if (c == null) {
            long t0 = System.nanoTime();
            try {
                if (parent != null) {
                    // 若没有加载过并且有父类加载器则调用父类加载器的 loadClass() 方法
                    c = parent.loadClass(name, false);
                } else {
                    // 调用启动类加载器
                    c = findBootstrapClassOrNull(name);
                }
            } catch (ClassNotFoundException e) {
                // ClassNotFoundException thrown if class not found
                // from the non-null parent class loader
            }

            if (c == null) {
                // If still not found, then invoke findClass in order
                // to find the class.
                long t1 = System.nanoTime();
                c = findClass(name);

                // this is the defining class loader; record the stats
                sun.misc.PerfCounter.getParentDelegationTime().addTime(t1 - t0);
                sun.misc.PerfCounter.getFindClassTime().addElapsedTimeFrom(t1);
                sun.misc.PerfCounter.getFindClasses().increment();
            }
        }
        if (resolve) {
            resolveClass(c);
        }
        return c;
    }
}
```
首先检查类是否已经被加载过，若没有加载过并且有父类加载器则调用父类加载器的 loadClass() 方法，若父加载器为空则默认使用启动类加载器作为父加载器。如果父类加载失败，抛出 ClassNotFoundException 异常后，再调用自己的 findClass() 方法进行加载。

## 5. 如何破坏双亲委派模型

双亲委派模型并不是一个强制性的约束模型，而是 Java 设计者推荐给开发者的类加载器实现方式。在 Java 的世界中大部分的类加载器都遵循这个模型，但也有例外，到目前为止，双亲委派模型主要出现过 3 较大规模的'被破坏'情况。

### 5.1 JDK 1.2 历史原因

双亲委派模型的第一次'被破坏'其实发生在双亲委派模型出现之前，即 JDK 1.2 发布之前。由于双亲委派模型在 JDK 1.2 之后才被引入，而类加载器和抽象类 java.lang.ClassLoader 则在 JDK 1.0 时代就已经存在，面对已经存在的用户自定义类加载器的实现代码，Java 设计者引入双亲委派模型时不得不做出一些妥协。为了向前兼容，JDK 1.2 之后的 java.lang.ClassLoader 添加了一个新的 protected 方法 findClass()，在此之前，用户去继承 java. lang.ClassLoader 的唯一目的就是为了重写 loadClass() 方法，因为虚拟机在进行类加载的时候会调用加载器的私有方法 loadClassInternal()，而这个方法的唯一逻辑就是去调用自己的 loadClass()。上一节我们已经看过 loadClass() 方法的代码，双亲委派的具体逻辑就实现在这个方法之中，JDK 1.2之 后已不提倡用户再去覆盖 loadClass() 方法，而应当把自己的类加载逻辑写到 findClass() 方法中，在 loadClass() 方法的逻辑里如果父类加载失败，则会调用自己的 findClass() 方法来完成加载，这样就可以保证新写出来的类加载器是符合双亲委派规则的。

### 5.2 SPI

双亲委派模型的第二次'被破坏'是由这个模型自身的缺陷所导致的，双亲委派很好地解决了各个类加载器的基础类的统一问题（越基础的类由越上层的加载器进行加载），基础类之所以称为“基础”，是因为它们总是作为被用户代码调用的 API，但世事往往没有绝对的完美，如果基础类又要调用回用户的代码，那该怎么办？
这并非是不可能的事情，一个典型的例子便是 JNDI 服务，JNDI 现在已经是 Java 的标准服务，它的代码由启动类加载器去加载（在 JDK 1.3 时放进去的 rt.jar 中），但 JNDI 的目的就是对资源进行集中管理和查找，它需要调用由独立厂商实现并部署在应用程序 ClassPath 下的 JNDI 接口提供者（SPI，Service Provider Interface）的代码，但启动类加载器不可能'认识'这些代码。为了解决这个问题，Java 设计团队只好引入了一个不太优雅的设计：线程上下文类加载器（Thread Context ClassLoader）。这个类加载器可以通过 java.lang.Thread 类的 setContextClassLoaser() 方法进行设置，如果创建线程时还未设置，将会从父线程中继承一个，如果在应用程序的全局范围内都没有设置过的话，那这个类加载器默认就是应用程序类加载器。有了线程上下文类加载器，就可以做一些'舞弊'的事情了，JNDI 服务使用这个线程上下文类加载器去加载所需要的 SPI 代码，也就是父类加载器请求子类加载器去完成类加载的动作，这种行为实际上就是打通了双亲委派模型的层次结构来逆向使用类加载器，实际上已经违背了双亲委派模型的一般性原则，但这也是无可奈何的事情。Java 中所有涉及 SPI 的加载动作基本上都采用这种方式，例如 JNDI、JDBC、JCE、JAXB和JBI等。

### 5.3 模块化

双亲委派模型的第三次'被破坏'是由于用户对程序动态性的追求而导致的，这里所说的'动态性'指的是当前一些非常'热门'的名词：代码热替换（HotSwap）、模块热部署（Hot Deployment）等。Sun 公司所提出的JSR-294、JSR-277 规范在与 JCP 组织的模块化规范之争中落败给 JSR-291（即OSGi R4.2），虽然 Sun 不甘失去 Java 模块化的主导权，独立在发展 Jigsaw 项目，但目前 OSGi 已经成为了业界事实上的 Java 模块化标准，而 OSGi 实现模块化热部署的关键则是它自定义的类加载器机制的实现。每一个程序模块（OSGi 中称为 Bundle）都有一个自己的类加载器，当需要更换一个 Bundle 时，就把 Bundle 连同类加载器一起换掉以实现代码的热替换。在 OSGi 环境下，类加载器不再是双亲委派模型中的树状结构，而是进一步发展为更加复杂的网状结构。

参考：
- 深入理解 Java 虚拟机
- [我竟然被“双亲委派”给虐了](https://mp.weixin.qq.com/s/Q0MqcvbeI7gAcJH5ZaQWgA)
