
## 1. 简介

我们把 Spring 在 Bean 与 Bean 之间建立依赖关系的行为称为'装配'。Spring 的 IOC 容器虽然功能强大，但它本身不过只是一个空壳而已，它自己并不能独自完成装配工作。需要我们主动将 Bean 放进去，并告诉它 Bean 和 Bean 之间的依赖关系，它才能按照我们的要求完成装配工作。在前面的学习中，我们都是在 XML 配置中通过 `<constructor-arg>` 和 `<property>` 中的 ref 属性，手动维护 Bean 与 Bean 之间的依赖关系的，具体可以查阅 [Spring 依赖注入之构造器注入](https://smartsi.blog.csdn.net/article/details/131694035) 和 [Spring 依赖注入之setter注入](https://smartsi.blog.csdn.net/article/details/131715353)。

对于只包含少量 Bean 的应用来说，这种方式已经足够满足我们的需求了。但随着应用的不断发展，容器中包含的 Bean 会越来越多，Bean 和 Bean 之间的依赖关系也越来越复杂，这就使得我们所编写的 XML 配置也越来越复杂，越来越繁琐。我们知道，过于复杂的 XML 配置不但可读性差，而且编写起来极易出错，严重的降低了开发人员的开发效率。为了解决这一问题，Spring 框架还为我们提供了'自动装配'功能。

## 2. Spring 自动装配

Spring 的自动装配功能可以让 Spring 容器依据某种规则，为指定的 Bean 从应用的上下文（AppplicationContext 容器）中查找它所依赖的 Bean，并自动建立 Bean 之间的依赖关系。而这一过程是在完全不依赖 `<constructor-arg>` 和 `<property>` 元素的 ref 属性。Spring 的自动装配功能能够有效地简化 Spring 应用的 XML 配置，因此在配置数量相当多时采用自动装配降低工作量。

如果想要使用 Spring 的自动装配功能，只需要在 Spring XML 配置文件中 `<bean>` 元素中添加 autowire 属性即可。Spring 为我们提供了 4 种各具特色的自动装配策略：

| 类型     | 说明     |
| :------------- | :------------- |
| no          | 不启动自动装配。默认方式，Bean 的引用必须通过 XML 文件中的 `</ref>` 元素或者 ref 属性手动设定 |
| byName	    | 按名称自动装配。把与 Bean 属性具有相同名字（ID）的其他 Bean 自动装配到 Bean 对应属性中。如果没有跟属性的名字相匹配的 Bean，则该属性不进行匹配。|
| byType	    | 按类型自动装配。把与 Bean 属性具有相同类型的其他 Bean 自动装配到 Bean 对应属性中。如果没有跟属性的类型相匹配的 Bean，则该属性不进行匹配。|
| constructor	| 把与 Bean 的构造器入参具有相同类型的其他 Bean 自动装配到 Bean 构造器对应入中。|

为了演示不同类型的自动装配策略，我们需要定义 Book 和 Student 实体类：
```java
public class Book {
  private Integer id;
  private String type;
  private String name;

  public Book() {
  }

  public Book(Integer id, String type, String name) {
      System.out.println("调用 Book#Book(Integer id, String type, String name)");
      this.id = id;
      this.type = type;
      this.name = name;
  }

  public Integer getId() {
      return id;
  }

  public void setId(Integer id) {
      System.out.println("调用 Book#setId(Integer id)");
      this.id = id;
  }

  public String getType() {
      return type;
  }

  public void setType(String type) {
      System.out.println("调用 Book#setType(String type)");
      this.type = type;
  }

  public String getName() {
      return name;
  }

  public void setName(String name) {
      System.out.println("调用 Book#setName(String name)");
      this.name = name;
  }

  @Override
  public String toString() {
      return "Book{" +
              "id=" + id +
              ", type='" + type + '\'' +
              ", name='" + name + '\'' +
              '}';
  }
}

public class Student {
    private int id;
    private String name;
    private Book book;

    public Student() {
    }

    public Student(int id, String name, Book book) {
        System.out.println("调用 Student(int id, String name, Book book)");
        this.id = id;
        this.name = name;
        this.book = book;
    }

    public Student(Book book) {
        System.out.println("调用 Student(Book book)");
        this.book = book;
    }

    public int getId() {
        return id;
    }

    public void setId(int id) {
        System.out.println("调用 Student#setId(int id)");
        this.id = id;
    }

    public String getName() {
        return name;
    }

    public void setName(String name) {
        System.out.println("调用 Student#setName(String name)");
        this.name = name;
    }

    public Book getBook() {
        return book;
    }

    public void setBook(Book book) {
        System.out.println("调用 Student#setBook(Book book)");
        this.book = book;
    }

    @Override
    public String toString() {
        return "Student{" +
                "id=" + id +
                ", name='" + name + '\'' +
                ", book=" + book +
                '}';
    }
}
```

### 2.1 no

`autowire="no"` 是 Spring 的默认配置，表示不自动装配。此时我们必须通过 `<constructor-arg>` 和 `<property>` 元素的 `</ref>` 元素或者 ref 属性维护 Bean 的依赖关系。如下所示我们通过构造器注入的方式配置了两个 Bean：
```xml
<bean id="book" class="com.spring.example.domain.Book">
    <constructor-arg value="1"/>
    <constructor-arg value="计算机理论"/>
    <constructor-arg value="深入理解 Mybatis"/>
</bean>

<bean id="student" class="com.spring.example.domain.Student" autowire="no">
    <constructor-arg value="10001"/>
    <constructor-arg value="Lucy"/>
    <constructor-arg ref="book"/>
</bean>
```
使用如下代码测试一下：
```java
public static void main(String[] args) {
    // 加载配置文件得到上下文对象 即 容器对象
    ApplicationContext ctx = new ClassPathXmlApplicationContext("di/applicationContext-autowire-no.xml");

    // 引用类型
    Student student = (Student) ctx.getBean("student");
    System.out.println(student);
}
```
实际运行输出如下所示：
```
调用 Book(Integer id, String type, String name)
调用 Student(int id, String name, Book book)
Student{id=10001, name='Lucy', book=Book{id=1, type='计算机理论', name='深入理解 Mybatis'}}
```

> 上述就是通过构造器注入的方式实现获取 Student 对象，具体可以查阅[Spring 依赖注入之构造器注入](https://smartsi.blog.csdn.net/article/details/131694035)

### 2.2 byName 

byName 装配方式需要设置 autowire 属性为 "byName"，Spring 会自动寻找与属性名字相同的 bean（即寻找某些 Bean，其 id 必须同该属性名字相同），找到后，通过调用 setXXX 方法将其注入属性：
```xml
<!--  通过 setter 手动装配  -->
<bean id="book" class="com.spring.example.domain.Book">
    <property name="id" value="1"/>
    <property name="type" value="计算机理论"/>
    <property name="name" value="深入理解 Mybatis"/>
</bean>

<!--  简单类型 id、name 通过 setter 手动装配  -->
<!--  引用类型 book 通过 setter 自动装配  -->
<bean id="student" class="com.spring.example.domain.Student" autowire="byName">
    <property name="id" value="10001"/>
    <property name="name" value="Lucy"/>
</bean>
```
在这个实例中 `student` Bean 的 book 属性名字 与 book Bean 的 id 属性是一样的。通过配置 autowire 属性，Spring 就可以利用此信息自动装配。实际运行效果如下所示：
```java
调用 Book#setId(Integer id)
调用 Book#setType(String type)
调用 Book#setName(String name)
调用 Student#setId(int id)
调用 Student#setName(String name)
调用 Student#setBook(Book book)
Student{id=10001, name='Lucy', book=Book{id=1, type='计算机理论', name='深入理解 Mybatis'}}
```

需要注意的是为属性自动装配 ID 与该属性的名字相同的 Bean。通过设置 autowire 的属性为"byName"，Spring 将特殊对待 Bean的所有属性，为这些属性查找与其名字相同的 Spring Bean。因为id具有唯一性，所以不可能存在有多个 Bean 的 id 与其属性名字相同而造成冲突的情况。根据 byName 自动装配结果是要么找到一个Bean，要么一个也找不到。

缺点就是 Bean 的名字（ID）与其他 Bean 的属性的名字必须保持一致。假设我们 Book 类对应的 bean 名字（id）改成"book2"：
```xml
<bean id="book2" class="com.spring.example.domain.Book">
    <property name="id" value="1"/>
    <property name="type" value="计算机理论"/>
    <property name="name" value="深入理解 Mybatis"/>
</bean>
```
这样就与 Student Bean 的 book 属性名字不一样，book 属性就得不到装配：
```java
调用 Book#setId(Integer id)
调用 Book#setType(String type)
调用 Book#setName(String name)
调用 Student#setId(int id)
调用 Student#setName(String name)
Student{id=10001, name='Lucy', book=null}
```

### 2.3 byType

byType 自动装配的工作方式类似于 byName 自动装配，只不过不再是匹配属性的名字而是检查属性的类型。当我们尝试使用 byType 自动装配时，Spring 会寻找哪一个 Bean 的类型与属性的类型匹配。找到后，通过调用 setXXX 方法将其注入。对于上面那个把 Bean 的名字（id）改成 "book2" 的情况，byName 已经不能寻找到相应的 Bean。在这里我们设置 autowire 属性为 "byType"：
```xml
<!--  通过 setter 手动装配  -->
<bean id="book2" class="com.spring.example.domain.Book">
    <property name="id" value="1"/>
    <property name="type" value="计算机理论"/>
    <property name="name" value="深入理解 Mybatis"/>
</bean>

<!--  简单类型通过 setter 手动装配  -->
<!--  引用类型通过 setter 自动装配  -->
<bean id="student" class="com.spring.example.domain.Student" autowire="byType">
    <property name="id" value="10001"/>
    <property name="name" value="Lucy"/>
</bean>
```

实际运行效果如下所示：
```java
调用 Book#setId(Integer id)
调用 Book#setType(String type)
调用 Book#setName(String name)
调用 Student#setId(int id)
调用 Student#setName(String name)
调用 Student#setBook(Book book)
Student{id=10001, name='Lucy', book=Book{id=1, type='计算机理论', name='深入理解 Mybatis'}}
```
在这个实例中我们设置 autowire 属性为 "byType"，Spring 容器会寻找哪一个 Bean 的类型与 book 属性的类型匹配。如果匹配就把 Bean 装配到 student 的属性中去。id 为 `book2` 的 Bean将自动被装配到 `student` 的 book 属性中，因为 book 属性的类型与 `book2` Bean 的类型都是 com.spring.example.domain.Book 类型。

需要注意的是如果 Spring 寻找到多个Bean，它们的类型与需要自动装配的属性的类型都能匹配，它不会智能的挑选一个，则会抛出异常。所以，应用中只允许存在一个 Bean 与需要自动装配的属性类型相匹配：
```xml
<!--  存在两个 Book 对应的 Bean  -->
<bean id="book2" class="com.spring.example.domain.Book">
    <property name="id" value="1"/>
    <property name="type" value="计算机理论"/>
    <property name="name" value="深入理解 Mybatis"/>
</bean>

<bean id="spring-book" class="com.spring.example.domain.Book">
    <property name="id" value="1"/>
    <property name="type" value="计算机理论"/>
    <property name="name" value="深入理解 Spring"/>
</bean>

<!--  简单类型通过 setter 手动装配  -->
<!--  引用类型通过 setter 自动装配  -->
<bean id="student" class="com.spring.example.domain.Student" autowire="byType">
    <property name="id" value="10001"/>
    <property name="name" value="Lucy"/>
</bean>
```
如上面所示有两个 Bean 与需要自动装配的属性的类型相匹配，这种情况下会抛出异常：
```java
Caused by: org.springframework.beans.factory.NoUniqueBeanDefinitionException: No qualifying bean of type 'com.spring.example.domain.Book' available: expected single matching bean but found 2: book2,spring-book
	at org.springframework.beans.factory.config.DependencyDescriptor.resolveNotUnique(DependencyDescriptor.java:220)
	at org.springframework.beans.factory.support.DefaultListableBeanFactory.doResolveDependency(DefaultListableBeanFactory.java:1285)
	at org.springframework.beans.factory.support.DefaultListableBeanFactory.resolveDependency(DefaultListableBeanFactory.java:1227)
	at org.springframework.beans.factory.support.AbstractAutowireCapableBeanFactory.autowireByType(AbstractAutowireCapableBeanFactory.java:1509)
	... 13 more 
```
为了避免因为使用 byType 自动装配而带来的歧义，Spring 为我们提供了两种选择：可以为自动装配标示一个首选 Bean，或者可以取消某个 Bean 自动装配的候选资格。

#### 2.3.1 标示首先Bean

为自动装配标示一个首先 Bean，可以使用 `<bean>` 元素的 primary 属性。如果只有一个自动装配的候选 Bean 的 primary 属性为 true，那么该 Bean 将比其他候选 Bean 优先被选择：
```xml

<bean id="mybatis-book" class="com.spring.example.domain.Book">
    <property name="id" value="1"/>
    <property name="type" value="计算机理论"/>
    <property name="name" value="深入理解 Mybatis"/>
</bean>

<bean id="springboot-book" class="com.spring.example.domain.Book">
    <property name="id" value="1"/>
    <property name="type" value="计算机理论"/>
    <property name="name" value="深入理解 SpringBoot"/>
</bean>

<!--  指定首先 Bean  -->
<bean id="spring-book" class="com.spring.example.domain.Book" primary="true">
    <property name="id" value="1"/>
    <property name="type" value="计算机理论"/>
    <property name="name" value="深入理解 Spring"/>
</bean>

<!--  简单类型通过 setter 手动装配  -->
<!--  引用类型通过 setter 自动装配  -->
<bean id="student" class="com.spring.example.domain.Student" autowire="byType">
    <property name="id" value="10001"/>
    <property name="name" value="Lucy"/>
</bean>
```
实际运行效果如下所示：
```java
调用 Book#setId(Integer id)
调用 Book#setType(String type)
调用 Book#setName(String name)
调用 Book#setId(Integer id)
调用 Book#setType(String type)
调用 Book#setName(String name)
调用 Book#setId(Integer id)
调用 Book#setType(String type)
调用 Book#setName(String name)
调用 Student#setId(int id)
调用 Student#setName(String name)
调用 Student#setBook(Book book)
Student{id=10001, name='Lucy', book=Book{id=1, type='计算机理论', name='深入理解 Spring'}}
```
如果 id="spring-book" Bean 的 primary 属性设置为 'tue'，实际运行效果如下所示：
```java
调用 Book#setId(Integer id)
调用 Book#setType(String type)
调用 Book#setName(String name)
调用 Book#setId(Integer id)
调用 Book#setType(String type)
调用 Book#setName(String name)
调用 Book#setId(Integer id)
调用 Book#setType(String type)
调用 Book#setName(String name)
调用 Student#setId(int id)
调用 Student#setName(String name)
调用 Student#setBook(Book book)
Student{id=10001, name='Lucy', book=Book{id=1, type='计算机理论', name='深入理解 SpringBoot'}}
```

#### 2.3.2 取消 Bean 自动装配候选资格

为取消某个 Bean 的自动装配的候选资格，可以使用 `<bean>` 元素的 `autowire-candidate` 属性。如果我们希望排除某些 Bean，可以设置这些 Bean 的 autowire-candidate 属性为 false：
```xml
<!--  取消 Bean 候选资格  -->
<bean id="mybatis-book" class="com.spring.example.domain.Book" autowire-candidate="false">
    <property name="id" value="1"/>
    <property name="type" value="计算机理论"/>
    <property name="name" value="深入理解 Mybatis"/>
</bean>

<!--  取消 Bean 候选资格  -->
<bean id="springboot-book" class="com.spring.example.domain.Book" autowire-candidate="false">
    <property name="id" value="1"/>
    <property name="type" value="计算机理论"/>
    <property name="name" value="深入理解 SpringBoot"/>
</bean>

<!--  首先 Bean  -->
<bean id="spring-book" class="com.spring.example.domain.Book">
    <property name="id" value="1"/>
    <property name="type" value="计算机理论"/>
    <property name="name" value="深入理解 Spring"/>
</bean>

<!--  简单类型通过 setter 手动装配  -->
<!--  引用类型通过 setter 自动装配  -->
<bean id="student" class="com.spring.example.domain.Student" autowire="byType">
    <property name="id" value="10001"/>
    <property name="name" value="Lucy"/>
</bean>
```
实际运行效果如下所示：
```java
调用 Book#setId(Integer id)
调用 Book#setType(String type)
调用 Book#setName(String name)
调用 Book#setId(Integer id)
调用 Book#setType(String type)
调用 Book#setName(String name)
调用 Book#setId(Integer id)
调用 Book#setType(String type)
调用 Book#setName(String name)
调用 Student#setId(int id)
调用 Student#setName(String name)
调用 Student#setBook(Book book)
Student{id=10001, name='Lucy', book=Book{id=1, type='计算机理论', name='深入理解 Spring'}}
```

### 2.4. constructor 自动装配

如果通过构造器注入来配置 Bean，那么我们可以移除 `<constructor-arg>` 元素，由 Spring 在应用上下文中自动选择 Bean 注入到构造器入参中。在未使用 constructor 自动装配之前，student Bean 的 book 属性通过 `constructor-arg` 元素的 ref 属性注入：
```xml
<bean id="book" class="com.spring.example.domain.Book">
    <constructor-arg value="1"/>
    <constructor-arg value="计算机理论"/>
    <constructor-arg value="深入理解 Mybatis"/>
</bean>

<bean id="student" class="com.spring.example.domain.Student">
    <constructor-arg value="10001"/>
    <constructor-arg value="Lucy"/>
    <constructor-arg ref="book"/>
</bean>
```
下面是重新声明的 student Bean，在这个 Bean 中 book 属性的 `<constructor-arg>` 元素消失不见了，而 autowire 属性设置为 constructor：
```xml
<!--  简单类型通过 setter 手动装配  -->
<!--  引用类型通过构造器自动装配  -->
<bean id="student" class="com.spring.example.domain.Student" autowire="constructor">
    <property name="id" value="10001"/>
    <property name="name" value="Lucy"/>
</bean>
```
> 当使用 constructor 自动装配策略时，我们必须让 Spring 自动装配构造器中的所有入参，我们不能混合使用 constructor 自动装配策略和 `<constructor-arg>` 元素。所以在这简单类型的 id、name 属性通过 setter 方法手动装配注入。

在这个示例中，简单类型的 id、name 属性通过 setter 方法手动装配注入，引用类型的 book 属性可以通过构造器自动装配。这就告诉 Spring 去审视 Student 的构造器，并尝试在 Spring 配置中寻找匹配 book 属性的构造器。为此我们在 Book 实体类中添加如下构造器：
```java
public Student(Book book) {
    this.book = book;
}
```
当构造 student Bean 时，Spring 使用这个构造器，并把 book Bean 作为参数传入。实际运行效果如下所示：
```java
调用 Book#Book(Integer id, String type, String name)
调用 Student(Book book)
调用 Student#setId(int id)
调用 Student#setName(String name)
Student{id=10001, name='Lucy', book=Book{id=1, type='计算机理论', name='深入理解 Mybatis'}}
```

需要注意的是和 byType 自动装配一样，都有相同的局限性。当发现多个 Bean 匹配某个构造器入参时，Spring不会尝试猜测哪一个 Bean 更适合自动装配。此外，如果一个类有多个构造器，它们都满足自动装配的条件时，Spring 也不会尝试哪一个构造器更适合使用。

当使用 constructor 自动装配策略时，我们必须让 Spring 自动装配构造器中的所有入参，我们不能混合使用 constructor 自动装配策略和 `<constructor-arg>` 元素。

参考：《Spring实战》
