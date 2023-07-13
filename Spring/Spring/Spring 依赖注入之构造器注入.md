基于构造器的注入通过调用带参数的构造器来实现，每个参数代表着一个协作者。

## 1. 通过构造器注入简单类型

### 1.1 默认方式

我们以下面的 Book 实体类为例进行说明：
```java
package com.spring.example.domain;

public class Book {
    private Integer id;
    private String type;
    private String name;

    public Book() {
    }

    public Book(Integer id, String type, String name) {
        this.id = id;
        this.type = type;
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

    public Integer getId() {
        return id;
    }

    public void setId(Integer id) {
        this.id = id;
    }

    public String getType() {
        return type;
    }

    public void setType(String type) {
        this.type = type;
    }

    public String getName() {
        return name;
    }

    public void setName(String name) {
        this.name = name;
    }

}
```
Book 类有三个属性：id、name、type。通过如下配置实现构造器注入：
```xml
<bean id="book" class="com.spring.example.domain.Book">
    <constructor-arg value="1"/>
    <constructor-arg value="计算机理论"/>
    <constructor-arg value="深入理解 Mybatis"/>
</bean>
```
我们通过 ClassPathXmlApplicationContext 加载配置文件得到容器对象，从而获取 Book bean：
```java
// 加载配置文件得到上下文对象 即 容器对象
ApplicationContext ctx = new ClassPathXmlApplicationContext("applicationContext.xml");
// 获取资源
Book book = (Book) ctx.getBean("book");
System.out.println(book);
```
实际执行效果如下所示：
```java
Book{id=1, type='计算机理论', name='深入理解 Mybatis'}
```
从上面我们就可以知道通过构造器注入成功了。


### 1.2 根据 name 属性传值

bean 中的 constructor-arg 元素用于通过构造器注入来设置属性。因为 Book 类中只有一个构造器，所以该代码运行没有任何问题，但是当有相同个数参数的构造器时，将会出现冲突。考虑如下 Book 类提供了两个构造器：
```java
public Book(String name, String type) {
    this.name = name;
    this.type = type;
}

public Book(Integer id, String name) {
    this.id = id;
    this.name = name;
}
```
假设我们进行如下配置：
```xml
<bean id="book" class="com.spring.example.domain.Book">
    <constructor-arg value="1"/>
    <constructor-arg value="深入理解 Mybatis"/>
</bean>
```
那么现在你认为哪个构造器将被调用？按照我们的思维应该是第二个带 Integer 和 String 参数的构造器，真的吗？实际上 Spring 将调用第一个构造器。即使我们知道第一个参数是 Integer，第二个参数是 String，但是 Spring 将其都解析为 String。实际运行结果如下所示：
```java
Book{id=null, type='深入理解 Mybatis', name='1'}
```
针对上面的这种情况，我们可以在构造器参数定义中使用 name 属性与参数进行匹配。现在如下配置，第二个构造器将被调用：
```xml
<bean id="book-name" class="com.spring.example.domain.Book">
    <constructor-arg name="id" value="1"/>
    <constructor-arg name="name" value="深入理解 Mybatis"/>
</bean>
```
这样设置之后只能匹配 `public Book(Integer id, String name)` 构造器。实际运行结果如下所示：
```java
Book{id=1, type='null', name='深入理解 Mybatis'}
```

### 1.3 根据 type 属性传值

通过 name 属性这种方式匹配虽然解决了上述问题，但是如果我们的参数名称发生修改，配置文件也需要对应修改，没办法实现解耦。这时候我们可以在构造器参数定义中使用 type 属性来显式指定参数所对应的简单类型，如下所示：
```xml
<bean id="book-type" class="com.spring.example.domain.Book">
    <constructor-arg type="java.lang.Integer" value="1"/>
    <constructor-arg type="java.lang.String" value="深入理解 Mybatis"/>
</bean>
```
这样设置之后 `value="1"` 则是 Integer 类型，所以只能匹配 `public Book(Integer id, String name)` 构造器。实际运行结果如下所示：
```java
Book{id=1, type='null', name='深入理解 Mybatis'}
```

### 1.4 根据 index 属性传值

现在考虑如下情况，有如下两个数据类型一样的构造器：
```java
public Book(String type, Integer id) {
    this.id = id;
    this.type = type;
}

public Book(Integer id, String name) {
    this.id = id;
    this.name = name;
}
```
我们还是使用上述在构造器参数定义中使用 type 属性来显式指定参数所对应的简单类型：
```xml
<bean id="book-type" class="com.spring.example.domain.Book">
    <constructor-arg type="java.lang.String" value="深入理解 Mybatis"/>
    <constructor-arg type="java.lang.Integer" value="1"/>
</bean>
```
那么现在你认为哪个构造器将被调用？按照我们的思维应该是第二个带 Integer 和 String 参数的构造器，真的吗？实际上 Spring 可能会调用第一个构造器，实际运行结果如下所示：
```java
Book{id=1, type='深入理解 Mybatis', name='null'}
```
针对上面的这种情况，我们可以在构造器参数定义中使用 index 属性显式的指定构造器参数的顺序：
```xml
<bean id="book-index" class="com.spring.example.domain.Book">
    <constructor-arg index="0" value="1"/>
    <constructor-arg index="1" value="深入理解 Mybatis"/>
</bean>
```
这样设置之后只能匹配 `public Book(Integer id, String name)` 构造器。实际运行结果如下所示：
```java
Book{id=1, type='null', name='深入理解 Mybatis'}
```

> 不会调用第一个构造器的原因是不能将index=1的参数转换为 Integer：Could not convert argument value of type [java.lang.String] to required type [java.lang.Integer]


## 2. 通过构造器注入对象引用

我们为 Student 提供一个最喜欢的书 Book 实体类：
```java
public class Student {
    private int id;
    private String name;
    private Book book;

    public int getId() {
        return id;
    }

    public void setId(int id) {
        this.id = id;
    }

    public String getName() {
        return name;
    }

    public void setName(String name) {
        this.name = name;
    }

    public Book getBook() {
        return book;
    }

    public void setBook(Book book) {
        this.book = book;
    }
}
```
我们使用构造器注入的方式 School 类进行配置：
```xml
<bean id="student" class="com.spring.example.domain.Student">
    <constructor-arg value="10001"/>
    <constructor-arg value="Lucy"/>
    <constructor-arg ref="book"/>
</bean>
```
在这我们不能使用 value 属性为第三个构造参数赋值，因为 Book 不是简单类型。取而代之的是，我们使用 ref 属性将 ID 为 book 的 Bean 引用传递给构造器。实际运行效果如下：
```java
Student{id=10001, name='Lucy', book=Book{id=1, type='计算机理论', name='深入理解 Mybatis'}}
```
