
我们通常提到类的加载，就是指利用类加载器 ClassLoader 通过类的全限定名来获取定义此类的二进制字节码流，从而构造出类的定义。Flink 作为基于 JVM 的框架，在 flink-conf.yaml 中提供了控制类加载策略的参数 classloader.resolve-order，可选项有 child-first（默认）和 parent-first。



https://nightlies.apache.org/flink/flink-docs-release-1.13/docs/deployment/config/#classloader-parent-first-patterns-default

## ParentFirstClassLoader

ParentFirstClassLoader 仅仅是一个继承 FlinkUserCodeClassLoader 的空类。相当于 ParentFirstClassLoader 直接调用了父加载器的 loadClass() 方法。之前已经讲过，JVM 中类加载器的层次关系和默认 loadClass() 方法的逻辑由双亲委派模型来体现。

```java
public static class ParentFirstClassLoader extends FlinkUserCodeClassLoader {
    ParentFirstClassLoader(URL[] urls, ClassLoader parent, Consumer<Throwable> classLoadingExceptionHandler) {
        super(urls, parent, classLoadingExceptionHandler);
    }
    static {
        ClassLoader.registerAsParallelCapable();
    }
}
```
Flink 的 parent-first 类加载策略就是照搬双亲委派模型的。也就是说，用户代码的类加载器是 Custom ClassLoader，Flink 框架本身的类加载器是 Application ClassLoader。用户代码中的类先由 Flink 框架的类加载器加载，再由用户代码的类加载器加载。但是，Flink 默认并不采用 parent-first 策略，而是采用下面的 child-first 策略，继续看。

## ChildFirstClassLoader






















https://blog.csdn.net/CarloPan/article/details/117295628
https://zhuanlan.zhihu.com/p/477362410
https://blog.csdn.net/chenxyz707/article/details/109043868
