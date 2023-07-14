
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


package com.sjf.bean;
/**
* 学生实体类
* @author sjf0115
*
*/
public class Student {

private String name;
private int age;
private School school;

public String getName() {
return name;
}
public void setName(String name) {
this.name = name;
}
public int getAge() {
return age;
}
public void setAge(int age) {
this.age = age;
}
public School getSchool() {
return school;
}
public void setSchool(School school) {
this.school = school;
}
@Override
public String toString() {
StringBuilder sb = new StringBuilder();
sb.append("name：" + name + " age：" + age );
if(school != null){
sb.append(" school：" + school.getName() + "[" + school.getLocation() + "]");
}//if
return sb.toString();
}
}


package com.sjf.bean;
/**
* 学校实体类
* @author sjf0115
*
*/
public class School {
private String name;
private String location;

public String getName() {
return name;
}
public void setName(String name) {
this.name = name;
}
public String getLocation() {
return location;
}
public void setLocation(String location) {
this.location = location;
}
@Override
public String toString() {
return "name：" + name + " location：" + location;
}
}

1. no
这是Spring的默认情况，不自动装配。Bean的引用必须通过XML文件中的</ref>元素或者ref属性手动设定。大多数情况下我们推荐使用这种方式，因为这种方式使文档更加明确简洁。
2. byName 

这种情况，Bean 设置 autowire属性为"byName"，Spring会自动寻找与属性名字相同的bean（即寻找某些Bean，其id必须同该属性名字相同），找到后，通过调用setXXX方法将其注入属性。


<?xml version="1.0" encoding="UTF-8"?>
<beans xmlns="http://www.springframework.org/schema/beans"
xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
xsi:schemaLocation="http://www.springframework.org/schema/beans http://www.springframework.org/schema/beans/spring-beans.xsd">

<bean id = "yoona" class = "com.sjf.bean.Student" autowire="byName">
<property name="name" value="yoona"/>
<property name="age" value="24"/>
</bean>

<bean id = "school" class="com.sjf.bean.School">
<property name="name" value="西安电子科技大学"/>
<property name="location" value="西安"/>
</bean>
</beans>

运行：

name：yoona   age：24   school：西安电子科技大学[西安]

在这个实例中yoona Bean的school属性名字 与 School Bean（西安电子科技大学）的 id 属性是一样的。通过配置autowire属性，Spring就可以利用此信息自动装配yoona的school属性。

约定：

为属性自动装配ID与该属性的名字相同的Bean。通过设置autowire的属性为"byName"，Spring将特殊对待 Bean的所有属性，为这些属性查找与其名字相同的Spring Bean。因为id具有唯一性，所以不可能存在有多个Bean 的id与其属性名字相同而造成冲突的情况。根据byName自动装配结果是要么找到一个Bean，要么一个也找不到。

缺点：

必须假设Bean的名字（ID）与其他Bean的属性的名字一样。


假设我们下面bean名字（id）改成"school1"，这样就与yoona Bean的school属性名字不一样，school属性就得不到装配。

<bean id = "school1" class="com.sjf.bean.School">
<property name="name" value="西安电子科技大学"/>
<property name="location" value="西安"/>
</bean>

3. byType

byType自动装配的工作方式类似于byName自动装配，只不过不再是匹配属性的名字而是检查属性的类型。当我们尝试使用byType自动装配时，Spring会寻找哪一个Bean的类型与属性的类型匹配。找到后，通过调用setXXX方法将其注入。

对于上面那个把Bean的名字（id）改成"school1"的情况，byName已经不能寻找到相应的Bean。在这里我们设置 autowire属性为"byType"。

<?xml version="1.0" encoding="UTF-8"?>
<beans xmlns="http://www.springframework.org/schema/beans"
xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
xsi:schemaLocation="http://www.springframework.org/schema/beans http://www.springframework.org/schema/beans/spring-beans.xsd">

<bean id = "yoona" class = "com.sjf.bean.Student" autowire="byType">
<property name="name" value="yoona"/>
<property name="age" value="24"/>
</bean>

<bean id = "school1" class="com.sjf.bean.School">
<property name="name" value="西安电子科技大学"/>
<property name="location" value="西安"/>
</bean>
</beans>


运行：


name：yoona   age：24   school：西安电子科技大学[西安]

在这个实例中我们设置 autowire属性为"byType"，Spring容器会寻找哪一个Bean的类型与school属性的类型匹配。如果匹配就把Bean 装配到yoona的属性中去。school1 Bean（西安电子科技大学）将自动被装配到yoona的school属性中，因为school属性的类型与school1 Bean的类型都是com.sjf.bean.School类型。

局限性：

如果Spring寻找到多个Bean，它们的类型与需要自动装配的属性的类型都能匹配，它不会智能的挑选一个，则会抛出异常。所以，应用中只允许存在一个Bean与需要自动装配的属性类型相匹配。


<?xml version="1.0" encoding="UTF-8"?>
<beans xmlns="http://www.springframework.org/schema/beans"
xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
xsi:schemaLocation="http://www.springframework.org/schema/beans http://www.springframework.org/schema/beans/spring-beans.xsd">

<bean id = "yoona" class = "com.sjf.bean.Student" autowire="byType">
<property name="name" value="yoona"/>
<property name="age" value="24"/>
</bean>

<bean id = "xidianSchool" class="com.sjf.bean.School">
<property name="name" value="西安电子科技大学"/>
<property name="location" value="西安"/>
</bean>
<bean id = "shandaSchool" class="com.sjf.bean.School">
<property name="name" value="山东大学"/>
<property name="location" value="山东"/>
</bean>
</beans>
假如说，XML中出现了上述情况：有两个Bean与需要自动装配的属性的类型相匹配，则会抛出异常：

No qualifying bean of type [com.sjf.bean.School] is defined: expected single matching bean but found 2: xidianSchool,shandaSchool  

应对措施：

为了避免因为使用byType自动装配而带来的歧义，Spring为我们提供了两种选择：可以为自动装配标示一个首选Bean，或者可以取消某个Bean自动装配的候选资格。
3.1 标示首先Bean

为自动装配标示一个首先Bean，可以使用<bean>元素的primary属性。如果只有一个自动装配的候选Bean的primary属性为true，那么该Bean将比其他候选Bean优先被选择。

<?xml version="1.0" encoding="UTF-8"?>
<beans xmlns="http://www.springframework.org/schema/beans"
xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
xsi:schemaLocation="http://www.springframework.org/schema/beans http://www.springframework.org/schema/beans/spring-beans.xsd">

<bean id = "yoona" class = "com.sjf.bean.Student" autowire="byType">
<property name="name" value="yoona"/>
<property name="age" value="24"/>
</bean>

<bean id = "xidianSchool" class="com.sjf.bean.School" primary="false">
<property name="name" value="西安电子科技大学"/>
<property name="location" value="西安"/>
</bean>
<bean id = "shandaSchool" class="com.sjf.bean.School" primary="true">
<property name="name" value="山东大学"/>
<property name="location" value="山东"/>
</bean>
</beans>

运行结果：

name：yoona   age：24   school：山东大学[山东]

诧异点：

primary属性很怪异的一点是：它的默认设置为true。意思就是说自动装配的所有的候选Bean都是首选Bean。所以，为了使用primary属性，我们不得不把所有的非首选的Bean的primary属性设置为false。
3.2 取消Bean自动装配候选资格

为取消某个Bean的自动装配的候选资格，可以使用<bean>元素的autowire-candidate属性。如果我们希望排除某些Bean，可以设置这些Bean的autowire-candidate属性为false。

<?xml version="1.0" encoding="UTF-8"?>
<beans xmlns="http://www.springframework.org/schema/beans"
xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
xsi:schemaLocation="http://www.springframework.org/schema/beans http://www.springframework.org/schema/beans/spring-beans.xsd">

<bean id = "yoona" class = "com.sjf.bean.Student" autowire="byType">
<property name="name" value="yoona"/>
<property name="age" value="24"/>
</bean>

<bean id = "xidianSchool" class="com.sjf.bean.School" >
<property name="name" value="西安电子科技大学"/>
<property name="location" value="西安"/>
</bean>
<bean id = "shandaSchool" class="com.sjf.bean.School" autowire-candidate="false">
<property name="name" value="山东大学"/>
<property name="location" value="山东"/>
</bean>
</beans>

运行结果：

name：yoona   age：24   school：西安电子科技大学[西安]
4. constructor 自动装配

Course实体类：

package com.sjf.bean;
 
public class Course {
private String name;
private double score;
private Student student;

public Course(Student student) {
this.student = student;
}

public String getName() {
return name;
}
 
public void setName(String name) {
this.name = name;
}
 
public double getScore() {
return score;
}
 
public void setScore(double score) {
this.score = score;
}
 
public Student getStudent() {
return student;
}
 
public void setStudent(Student student) {
this.student = student;
}
 
@Override
public String toString() {
return "courseName：" + name + " score：" + score + " student：" + (student != null ? student.getName() : "null");
}
}

如果通过构造器注入来配置Bean，那么我们可以移除<constructor-arg>元素，由Spring在应用上下文中自动选择Bean注入到构造器入参中。

<bean id = "course" class = "com.sjf.bean.Course" autowire="constructor">
<property name="name" value="英语"/>
<property name="score" value="91"/>
</bean>
 
<bean id = "yoona" class = "com.sjf.bean.Student">
<property name="name" value="yoona"/>
<property name="age" value="24"/>
</bean>

运行结果：

courseName：英语   score：91.0   student：yoona  

在这个实例中，我们对name属性和score属性通过setter方式注入，student属性通过构造器方式注入。在course Bean的声明中，<constructor-arg>元素不见了（对于student属性），而autowire属性设置为"constructor"。这样的话，Spring会去审视Course的构造器，并尝试在Spring配置中寻找匹配Course某一构造器所有参数的Bean。我们定义了一个yoona Bean，它正好与Course 中的一个构造器参数相匹配。因此，当构造 course Bean时，Spring使用这个构造器，并把yoona Bean作为入参传入。

局限性：

和byType自动装配有相同的局限性。当发现多个Bean匹配某个构造器入参时，Spring不会尝试猜测哪一个Bean更适合自动装配。此外，如果一个类有多个构造器，它们都满足自动装配的条件时，Spring也不会尝试哪一个构造器更适合使用。
注意：

当使用constructor自动装配策略时，我们必须让Spring自动装配构造器中的所有入参，我们不能混合使用constructor自动装配策略和<constructor-arg>元素。
5. 最佳自动装配（Spring3 报错 估计弃用了）

如果想自动装配Bean，但是又不能决定使用哪一种类型的自动装配。我们可以设置autowire属性为autodetect，交由Spring决定。
6. 默认自动装配 default-autowire

如果需要为Spring应用上下文中的每一个Bean（或者其中的大多数）都配置相同的autowire属性，那么就可以要求Spring为它所创建的所有Bean应用相同的自动装配策略来简化配置。只需要在<beans>元素上增加一个default-autowire属性：

<?xml version="1.0" encoding="UTF-8"?>
<beans xmlns="http://www.springframework.org/schema/beans"
xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
xsi:schemaLocation="http://www.springframework.org/schema/beans http://www.springframework.org/schema/beans/spring-beans.xsd"
default-autowire="byName">
</beans>

默认情况下default-autowire属性设置为none，表示所有的Bean都不使用自动装配策略，除非Bean自己配置了autowire属性。在这里我们把default-autowire设置为byName，即希望每一个Bean的所有属性都是用byName的自动装配策略进行自动装配。

注意：

不能因为我们配置了一个默认的自动装配策略，就意味着所有的Bean只能使用这个默认的自动装配策略。我们还可以使用<bean>元素的autowire属性来覆盖<beans>元素所配置的默认自动装配策略。



参考：《Spring实战》



package com.sjf.bean;
/**
* 学生实体类
* @author sjf0115
*
*/
public class Student {

private String name;
private int age;
private School school;

public String getName() {
return name;
}
public void setName(String name) {
this.name = name;
}
public int getAge() {
return age;
}
public void setAge(int age) {
this.age = age;
}
public School getSchool() {
return school;
}
public void setSchool(School school) {
this.school = school;
}
@Override
public String toString() {
StringBuilder sb = new StringBuilder();
sb.append("name：" + name + " age：" + age );
if(school != null){
sb.append(" school：" + school.getName() + "[" + school.getLocation() + "]");
}//if
return sb.toString();
}
}


package com.sjf.bean;
/**
* 学校实体类
* @author sjf0115
*
*/
public class School {
private String name;
private String location;

public String getName() {
return name;
}
public void setName(String name) {
this.name = name;
}
public String getLocation() {
return location;
}
public void setLocation(String location) {
this.location = location;
}
@Override
public String toString() {
return "name：" + name + " location：" + location;
}
}
