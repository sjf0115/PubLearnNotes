Java反射机制可以让我们在编译期(Compile Time)之外的**运行期** (Runtime)检查类，接口，变量以及方法的信息。反射还可以让我们在运行期实例化对象，调用方法，通过调用get/set方法获取变量的值。

Java反射机制功能强大而且非常实用。举个例子，你可以用反射机制把Java对象映射到数据库表，就像Butterfly Persistence所做的那样，或者把脚本中的一段语句在运行期映射到相应的对象调用方法上，就像 Butterfly Container在解析它的配置脚本时所做的那样。

目前在互联网上已经有不胜枚举的Java反射指南，然而大多数的指南包括Sun公司所发布的反射指南中都仅仅只是介绍了一些反射的表面内容以及它的潜能。

在这个系列的文章中，我们会比其他指南更深入的去理解Java反射机制，它会阐述Java反射机制的基本原理包括如何去使用数组，注解，泛型以及动态代理还有类的动态加载以及类的重载的实现。同时也会向你展示如何实现一些比较有特性的功能，比如从一个类中读取所有的get/set方法，或者访问一个类的私有变量以及私有方法。在这个系列的指南中同时也会说明一些非反射相关的但是令人困惑的问题，比如哪些泛型信息在运行时是有效的，一些人声称所有的泛型信息在运行期都会消失，其实这是不对的。

该系列文章中所描述介绍的是Java 7版本的反射机制。

Java反射的例子
```
    public static void test1(){
        Method[] methodArray = Student.class.getMethods();
        for(Method method : methodArray){
            System.out.println("method name ->" + method.getName());
        }
    }
```    
输出信息：
```
method name ->getAge
method name ->setAge
method name ->toString
method name ->getName
method name ->setName
method name ->wait
method name ->wait
method name ->wait
method name ->equals
method name ->hashCode
method name ->getClass
method name ->notify
method name ->notifyAll
```
在这个例子中通过调用Student类的class属性获取对应的Class类的对象，通过这个Class类的对象获取Student类中的方法集合。迭代这个方法的集合并且打印每个方法的名字。



原文：http://tutorials.jenkov.com/java-reflection/index.html

