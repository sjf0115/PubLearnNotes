通常，JavaBean 的属性是私有的，同时拥有一组存取器方法，以 `setXXX()` 和 `getXXX()` 形式存在。Spring 可以借助属性的 set 方法来配置属性的值，以实现 setter 方式的注入。上一篇文章讲解了[如何通过构造器](https://smartsi.blog.csdn.net/article/details/131694035)实现注入，这篇文章主要讲解如何通过 setter 方法实现注入。

## 1. 注入简单值

在 Spring 中我们可以使用 `<property>` 元素配置 Bean 的属性。`<property>` 在许多方面都与 `<constructor-arg>` 类似，只不过一个是通过构造参数来注入值，另一个是通过调用属性的 setter 方法来注入值。

举例说明，让我们使用 setter 注入为 Book 实体类赋予一些基本信息，setter 注入必须借助 `setXXX` 方法来配置属性的值。Book 类一共有三个属性，id、type 以及 name，我们都提供了相应的 set 方法：
```java
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

    @Override
    public String toString() {
        return "Book{" +
                "id=" + id +
                ", type='" + type + '\'' +
                ", name='" + name + '\'' +
                '}';
    }
}
```

下面让我们使用 setter 注入为 Book 注入一些基本信息，下面的 XML 展示了 Bean 的配置：
```xml
<bean id="book-setter" class="com.spring.example.domain.Book">
    <property name="id" value="1"/>
    <property name="type" value="计算机理论"/>
    <property name="name" value="深入理解 Mybatis"/>
</bean>
```
一旦 Book 被实例化，Spring 就会调用 `<property>` 元素所指定属性的 setter 方法为该属性注入值。在这段 XML 代码中，`<property>` 元素会指示 Spring 调用`setId()` 方法将 id 属性的值设置为 '1'、调用 `setType()` 方法将 type 属性的值设为 '计算机理论' 以及调用 `setName()` 方法将 name 属性的值设置为 '深入理解 Mybatis'。注意的是 name="xxx" 中的 xxx 必须跟 `setXXX()` 方法中 XXX 是一样的。`<property>` 元素并没有限制只能注入 String 类型的值，value 属性同样可以指定数值型（int、float、java.lang.Double 等）以及 boolen 型的值。

注意 value 属性的使用，为它设置数字类型的值和设置String 类型的值并没有任何不同。Spring 将根据 Bean 属性的类型自动判断 value 值的正确类型。因为 Bean 的 id 属性为 Integer 类型，Spring 在调用 `setId()` 方法之前会自动将字符串 '1' 转换成 Integer 型。

## 2. 引用其他 Bean

在 setter 注入中引用其他 Bean，跟构造器注入引用其他 Bean 基本一致，都要借助 ref 属性来实现。我们来为 Student 设置一个最喜欢读的书 Book 类：
```java
public class Student {
    private int id;
    private String name;
    private Book book;

    public Student() {
    }

    public Student(int id, String name, Book book) {
        this.id = id;
        this.name = name;
        this.book = book;
    }

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
使用之前要我们先在 Spring 中将它声明为一个 Bean，使用 setter 为 book 注入为属性设值：
```xml
<!-- setter 注入-->
<bean id="book" class="com.spring.example.domain.Book">
    <property name="id" value="1"/>
    <property name="type" value="计算机理论"/>
    <property name="name" value="深入理解 Mybatis"/>
</bean>

<bean id="student" class="com.spring.example.domain.Student">
    <property name="id" value="10001"/>
    <property name="name" value="Lucy"/>
    <property name="book" ref="book"/>
</bean>
```


参考：《Spring实战》
