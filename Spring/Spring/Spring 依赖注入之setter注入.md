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

## 2. 引用其他Bean

在setter注入中引用其他Bean，跟构造器注入引用其他Bean基本一致，都要借助ref属性来实现。

我们来为Student设置一个学校School类：

public class School {

private String name;
 
public void setName(String name) {
this.name = name;
}
}


private String name;
private int age;
private School school;


public void setName(String name) {
this.name = name;
}
 
public void setAge(int age) {
this.age = age;
}
 
public void setSchool(School school) {
this.school = school;
}

使用之前要我们必须在Spring 中将它声明为一个Bean，同时为学校赋值一个名字西电：

<bean id = "xidian" class = "com.sjf.bean.School">
<property name = "name" value = "西电"/>
</bean>

声明了school之后，那么现在就可以将它赋给Student了。使用setter 注入为school 属性设值：

<bean id = "yoona" class = "com.sjf.bean.Student">
<property name="name" value = "yoona"/>
<property name="age" value = "24" />
<property name="school" ref="xidian"></property>
</bean>

<bean id = "xidian" class = "com.sjf.bean.School">
<property name = "name" value = "西电"/>
</bean>

3. 注入内部Bean


我们已经看到yoona该学生有了考进西电大学。不仅yoona可以考上西电大学，其他学生也可以通过自己的努力考上该大学。所以说不同Student（学生）可以共享一个School（学校）。事实上，在应用中与其他Bean 共享Bean是非常普遍的。


<bean id = "yoona" class = "com.sjf.bean.Student">
<property name="name" value = "yoona"/>
<property name="age" value = "24" />
<property name="school" ref="xidian"></property>
</bean>
 
<bean id = "xiaosi" class = "com.sjf.bean.Student">
<property name="name" value = "xiaosi"/>
<property name="age" value = "21" />
<property name="school" ref="xidian"></property>
</bean>

<bean id = "xidian" class = "com.sjf.bean.School">
<property name = "name" value = "西电"/>
</bean>

但是当我们说个人兴趣的时候，就不能与其他人共享了，每一个人都有自己的兴趣喜好，我们将使用一种很好用的Spring 技术：内部Bean（inner bean）。内部Bean 是定义在其他Bean 内部的Bean。


package com.sjf.bean;
 
public class Hobby {

private String desc;
 
public void setDesc(String desc) {
this.desc = desc;
}
 
@Override
public String toString() {
return desc;
}
}


package com.sjf.bean;
 
/**
* 学生实体类
* @author sjf0115
*
*/
public class Student {

private String name;
private int age;
private Hobby hobby;


public void setName(String name) {
this.name = name;
}
 
public void setAge(int age) {
this.age = age;
}

public void setHobby(Hobby hobby) {
this.hobby = hobby;
}
 
@Override
public String toString() {
StringBuilder stringBuilder = new StringBuilder();
stringBuilder.append("个人详细信息如下：" + "\n");
stringBuilder.append("name：" + name + "\n");
stringBuilder.append("age：" + age + "\n");
stringBuilder.append("hobby：" + hobby.toString());
return stringBuilder.toString();
}

}

进行如下配置，我们把Hobby声明为内部Bean：

<bean id = "yoona" class = "com.sjf.bean.Student">
<property name="name" value = "xiaosi"/>
<property name="age" value = "21" />
<property name="hobby">
<bean class = "com.sjf.bean.Hobby">
<property name="desc" value = "喜欢踢足球，打羽毛球"/>
</bean>
</property>
</bean>

正如你所见到的，内部Bean 是通过直接声明一个<bean> 元素作为<property>元素的子节点而定义的。内部Bean 并不仅限于setter 注入，我们还可以把内部Bean 装配到构造方法的入参中。

注意到内部Bean 没有ID 属性。虽然为内部Bean 配置一个ID 属性是完全合法的，但是并没有太大必要，因为我们永远不会通过名字来引用内部Bean。这也突出了使用内部Bean 的最大缺点：它们不能被复用。内部Bean 仅适用于一次注入，而且也不能被其他Bean 所引用。


参考：《Spring实战》
