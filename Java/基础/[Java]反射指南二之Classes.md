使用Java反射机制可以在运行时期检查Java类的信息，检查Java类的信息往往是你在使用Java反射机制的时候所做的第一件事情，通过获取类的信息你可以获取以下相关的内容：
Class对象，类名，修饰符，包信息，父类，实现的接口，构造器，方法，变量，注解

除了上述这些内容，还有很多的信息你可以通过反射机制获得，如果你想要知道全部的信息你可以查看相应的文档JavaDoc for java.lang.Class里面有详尽的描述。

在本节中我们会简短的涉及上述所提及的信息，上述的一些主题我们会使用单独的章节进行更详细的描述，比如这段内容会描述如何获取一个类的所有方法或者指定方法，但是在单独的章节中则会向你展示如何调用反射获得的方法(Method Object)，如何在多个同名方法中通过给定的参数集合匹配到指定的方法，在一个方法通过反射机制调用的时候会抛出那些异常？如何准确的获取getter/setter方法等等。本节的内容主要是介绍Class类以及你能从Class类中获取哪些信息。

## Class对象

在你想检查一个类的信息之前，你首先需要获取类的Class对象。Java中的所有类型包括基本类型(int, long, float等等)，即使是数组都有与之关联的Class类的对象。如果你在编译期知道一个类的名字的话，那么你可以使用如下的方式获取一个类的Class对象。

```
Class studentClass = Student.class;
```

如果你在编译期不知道类的名字，但是你可以在运行期获得到类名的字符串，那么你则可以这么做来获取Class对象:

```
String className = "com.sjf.open.base.Address";
Class classObject = Class.forName(className);
```
在使用Class.forName()方法时，你必须提供一个类的全名，这个全名包括类所在的包的名字。例如Address类位于com.sjf.open.base包，那么他的全名就是com.sjf.open.base.Address。
如果在调用Class.forName()方法时，没有在编译路径下(classpath)找到对应的类，那么将会抛出ClassNotFoundException。

## 类名


你可以从Class对象中获取两个版本的类名。

### getName()

通过getName() 方法返回类的全限定类名（包含包名）：

```
Class studentClass = Student.class;
System.out.println(studentClass.getName()); // com.sjf.open.base.Student
```

### getSimpleName()
如果你仅仅只是想获取类的名字(不包含包名)，那么你可以使用getSimpleName()方法:

```
Class studentClass = Student.class;
System.out.println(studentClass.getSimpleName()); // Student
```

## 修饰符

可以通过Class对象来访问一个类的修饰符，即public，private，static等关键字，你可以使用如下方法来获取类的修饰符：

```
Class studentClass = Student.class;
System.out.println(studentClass.getModifiers()); // 1
```

修饰符都被包装成一个int类型的数字，这样每个修饰符都是一个位标识(flag bit)，这个位标识可以设置和清除修饰符的类型。

可以使用java.lang.reflect.Modifier类中的方法来检查修饰符对应的数字：

```
int publicNum = Modifier.PUBLIC; // 1
int privateNum = Modifier.PRIVATE; // 2
int protectedNum = Modifier.PROTECTED; // 4
int staticNum = Modifier.STATIC; // 8
int finalNum = Modifier.FINAL; // 16
int synchronizedNum = Modifier.SYNCHRONIZED; // 32
int volatileNum = Modifier.VOLATILE; // 64
int transientNum = Modifier.TRANSIENT; // 128
int nativeNum = Modifier.NATIVE; // 256
int interfaceNum = Modifier.INTERFACE; // 512
int abstractNum = Modifier.ABSTRACT; // 1024
int strictNum = Modifier.STRICT; // 2048
```
## 包信息


可以使用Class对象通过如下的方式获取包信息：
```
Class studentClass = Student.class;
System.out.println(studentClass.getPackage()); // package com.sjf.open.base
```
通过Package对象你可以获取包的相关信息，比如包名，你也可以通过Manifest文件访问位于编译路径下jar包的指定信息，比如你可以在Manifest文件中指定包的版本编号。更多的Package类信息可以阅读java.lang.Package。

## 父类


通过Class对象你可以访问类的父类，如下例：
```
Class studentClass = Student.class;
Class superStudent = studentClass.getSuperclass();
```
可以看到superclass对象其实就是一个Class类的实例，所以你可以继续在这个对象上进行反射操作。
## 实现的接口


可以通过如下方式获取指定类所实现的接口集合：
```
Class studentClass = Student.class;
Class[] interfaceArray = studentClass.getInterfaces();
```
由于一个类可以实现多个接口，因此getInterfaces()方法返回一个Class数组，在Java中接口同样有对应的Class对象。

*注意*：

getInterfaces()方法仅仅只返回当前类所实现的接口。当前类的父类如果实现了接口，这些接口是不会在返回的Class集合中的，尽管实际上当前类其实已经实现了父类接口。

## 构造器


你可以通过如下方式访问一个类的构造方法：
```
Class studentClass = Student.class;
Constructor[] constructorArray = studentClass.getConstructors();
```
更多有关Constructor的信息可以访问Constructors。
## 方法
你可以通过如下方式访问一个类的所有方法：
```
Class studentClass = Student.class;
Method[] methodArray = studentClass.getMethods();
```
更多有关Method的信息可以访问Methods。
## 变量


你可以通过如下方式访问一个类的成员变量：
```
Class studentClass = Student.class;
Field[] fieldArray = studentClass.getFields();
```
更多有关Field的信息可以访问Fields。
## 注解


你可以通过如下方式访问一个类的注解：
```
Class studentClass = Student.class;
Annotation[] annotationArray = studentClass.getAnnotations();
```
更多有关Annotation的信息可以访问Annotations。






















