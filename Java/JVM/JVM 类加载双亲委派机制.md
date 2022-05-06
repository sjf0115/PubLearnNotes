
## 1. 类加载器

我们知道，虚拟机在加载类的过程中需要使用类加载器进行加载，而在 Java 中，类加载器有很多，那么当 JVM 想要加载一个 `.class` 文件的时候，到底应该由哪个类加载器加载呢？这时候就需要双亲委派机制来告诉 JVM 使用哪个类加载器加载。在讲解什么是双亲委派机制之前，我们先看一下有哪些加载器。

从 Java 虚拟机的角度来讲，只存在两种不同的类加载器：一种是启动类加载器 Bootstrap ClassLoader，这个类加载器使用 C++ 语言实现，是虚拟机自身的一部分；另一种就是所有其他的类加载器，这些类加载器都由 Java 语言实现，独立于虚拟机外部，并且全都继承自抽象类 java.lang.ClassLoader。从 Java 开发人员的角度来看，类加载器还可以划分得更细致一些，分为用户级别和系统级别类加载器。用户级别的类加载器我们统一称为自定义类加载器，而系统级别的类加载器有：
- 启动类加载器：Bootstrap ClassLoader
- 扩展类加载器：Extention ClassLoader
- 应用程序类加载器：Application ClassLoader

### 1.1 启动类加载器

启动类加载器 Bootstrap ClassLoader 负责将存放在 `<JAVA_HOME>\lib` 目录中的，或者被 `-Xbootclasspath` 参数所指定的路径中的，并且是虚拟机识别的（仅按照文件名识别，如rt.jar，名字不符合的类库即使放在lib目录中也不会被加载）类库加载到虚拟机内存中。启动类加载器无法被 Java 程序直接引用，用户在编写自定义类加载器时，如果需要把加载请求委派给引导类加载器，那直接使用 null 代替即可，如代码清单7-9所示为java.lang.ClassLoader.getClassLoader()方法的代码片段。

### 1.2 扩展类加载器

扩展类加载器 Extension ClassLoader 是由 `sun.misc.Launcher$ExtClassLoader` 实现，负责加载 `<JAVA_HOME>\lib\ext` 目录中的，或者被 `java.ext.dirs` 系统变量所指定的路径中的所有类库，开发者可以直接使用扩展类加载器。

#### 1.3 应用程序类加载器

应用程序类加载器 Application ClassLoader 是由 `sun.misc.Launcher$App-ClassLoader` 实现。由于这个类加载器是 ClassLoader 中的 getSystemClassLoader() 方法的返回值，所以一般也称它为系统类加载器。它负责加载用户类路径 ClassPath 上所指定的类库，开发者可以直接使用这个类加载器，如果应用程序中没有自定义过自己的类加载器，一般情况下这个就是程序中默认的类加载器。

#### 1.4 自定义类加载器

## 2. 什么是双亲委派模型

上述四种类加载器之间存在着一种层次关系，如下图所示：

![](1)

一般认为上一层加载器是下一层加载器的父类加载器，除了启动类加载器 BootstrapClassLoader 之外，所有的加载器都是有父类加载器。我们可以先通过如下代码来看一下类加载器的层级结构：
```java
public class ClassLoaderParent {
    public static void main(String[] args) {
        // 应用程序类加载器 sun.misc.Launcher$AppClassLoader@49476842
        ClassLoader classLoader = ClassLoaderParent.class.getClassLoader();
        System.out.println(classLoader);
        // 扩展类加载器 sun.misc.Launcher$ExtClassLoader@5acf9800
        System.out.println(classLoader.getParent());
        // 启动类加载器 null
        System.out.println(classLoader.getParent().getParent());
    }
}
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

## 3. 双亲委派模型是怎么实现的

双亲委派模型对于保证 Java 程序的稳定运作很重要，但它的实现却非常简单，实现双亲委派的代码都集中在 java.lang.ClassLoade r的 loadClass() 方法之中
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

## 4. 如何破坏双亲委派模型


https://www.jianshu.com/p/bc7309b03407
https://www.jianshu.com/p/67021213872a
https://mp.weixin.qq.com/s?__biz=MzI3NzE0NjcwMg==&mid=2650150958&idx=1&sn=2ae43e8d02e3e1c3a09ab26e629ca4c2&chksm=f368050fc41f8c19015eb516087d0380b750c142934067b1def1faae177a5de1ddc0b8a9ba6f&scene=27#wechat_redirect
https://xie.infoq.cn/article/b21c42dfc1fb22497978865b1
https://xie.infoq.cn/article/1927dfb815f10c5caed3b5c8b
https://time.geekbang.org/dailylesson/detail/100044055?source=app_share
https://time.geekbang.org/column/article/3ad8a469f918be2ee2172336cfcf8215/share?code=1RKFYX0bQBsop1lmfLBvXDK8VPylk2%2F0kkVvdLVVEKM%3D&source=app_share&oss_token=a5702195c81ef9d3
