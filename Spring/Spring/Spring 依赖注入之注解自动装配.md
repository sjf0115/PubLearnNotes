## 1. 简介
从 Spring 2.5 开始，我们就可以使用注解的自动装配方式装配 Spring Bean 的属性。使用注解自动装配方式与在 XML 中使用 Autowire 属性自动装配没有太大区别。那为啥还要研发出这样一种装配方式？肯定有它独特的地方：使用注解自动装配方式允许更细粒度的自动装配，我们可以选择性的标注某一个属性对其应用自动装配。

2. 启用注解装配
Spring容器默认禁用注解装配。所以，在使用基于注解的自动装配前，我们需要在Spring配置中启用它。最简单的启用方式是使用Spring的context命名空间配置的<context:annotation-config>元素。

转存失败
重新上传
取消

<?xml version="1.0" encoding="UTF-8"?>
<beans xmlns="http://www.springframework.org/schema/beans"
xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
xmlns:context="http://www.springframework.org/schema/context"
xsi:schemaLocation="http://www.springframework.org/schema/beans http://www.springframework.org/schema/beans/spring-beans.xsd
http://www.springframework.org/schema/context http://www.springframework.org/schema/context/spring-context.xsd">
<context:annotation-config/>
 
</beans>
<context:annotation-config/>元素告诉Spring我们打算使用基于注解的自动装配。一旦装配完成，我们就可以对代码添加注解，表示Spring应该为属性，方法和构造器进行自动装配。
3. 使用@Autowired

@Autowired
public void setSchool(School school) {
this.school = school;
}
当我们对setSchool()方法使用@Autowired注解时，我们可以移除用来定义Student的school属性所对应的<property>元素了。如下面配置文件中的yoona Bean。

<?xml version="1.0" encoding="UTF-8"?>
<beans xmlns="http://www.springframework.org/schema/beans"
xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
xmlns:context="http://www.springframework.org/schema/context"
xsi:schemaLocation="http://www.springframework.org/schema/beans http://www.springframework.org/schema/beans/spring-beans.xsd
http://www.springframework.org/schema/context http://www.springframework.org/schema/context/spring-context.xsd">
<context:annotation-config/>
 
<bean id = "yoona" class = "com.sjf.bean.Student">
<property name="name" value="yoona"/>
<property name="age" value="24"/>
</bean>
 
<bean id = "xidianSchool" class = "com.sjf.bean.School">
<property name="name" value="西安电子科技大学"/>
<property name="location" value="西安"/>
</bean>
 
</beans>
运行结果：

name：yoona   age：24   school：西安电子科技大学[西安]
在这个实例中，我们对Student的school属性使用使用@Autowired注解，name属性和age属性使用setter注入方式。当Spring发现我们对setSchool()方法使用@Autowired注解时，Spring就会尝试对该方法执行byType自动装配。查询到只有一个Bean（xidianSchool）满足其条件，自动把xidianSchool Bean注入到Student的school属性中。
注意点：

使用了@Autowired注解时，Spring就会尝试对该方法执行byType自动装配。
特别之处（不同XML方式）：

使用@Autowired注解不只可以使用它标注setter方法，还可以标注需要自动装配Bean引用的任意方法。甚至是构造器，@Autowired注解表示当创建Bean时，即使Spring XML文件中没有使用<constructor-arg>元素配置Bean，该构造器也需要进行自动装配。Spring会从所有满足装配条件的构造器中选择入参最多的那个构造器。还可以标注属性，并可以删除setter方法。
（1）使用@Autowired注解标注setter方法：

@Autowired
public void setSchool(School school) {
this.school = school;
}
（2）使用@Autowired注解标注属性（不受限于private关键字）：

@Autowired
private School school;
（3）使用@Autowired注解标注任意方法：

@Autowired
public void assemblySchool(School school) {
this.school = school;
}
（4）使用@Autowired注解标注构造器：

@Autowired
public Student(School school) {
this.school = school;
}
局限性（同于XML方式）：

应用中必须只能有一个Bean适合装配到@Autowired注解所标注的属性或者参数中。如果没有匹配的Bean，或者存在多个匹配的Bean，@Autowired注解就会遇到一些麻烦。
3.1 没有匹配的Bean
如果没有匹配的Bean，@Autowired注解就会失败，抛出NoSuchBeanDefinitionException异常。
Caused by: org.springframework.beans.factory.NoSuchBeanDefinitionException: 
No qualifying bean of type [com.sjf.bean.School] found for dependency: expected 
at least 1 bean which qualifies as autowire candidate for this dependency. Dependency annotations: {}
    at org.springframework.beans.factory.support.DefaultListableBeanFactory.
raiseNoSuchBeanDefinitionException(DefaultListableBeanFactory.java:1373)
    at org.springframework.beans.factory.support.DefaultListableBeanFactory.
doResolveDependency(DefaultListableBeanFactory.java:1119)
    at org.springframework.beans.factory.support.DefaultListableBeanFactory.
resolveDependency(DefaultListableBeanFactory.java:1014)
    at org.springframework.beans.factory.annotation.
AutowiredAnnotationBeanPostProcessor$AutowiredMethodElement.inject(AutowiredAnnotationBeanPostProcessor.java:618)
    ... 15 more  
属性不一定非要装配，null值也是可以接受的。这种情况下，我们可以设置@Autowired的required属性为false来装配自动装配的是可选的。

@Autowired(required = false)
public void setSchool(School school) {
this.school = school;
}
在这里，Spring将尝试装配school属性，但是如果没有查找到与之匹配的类型为School的Bean，不会抛出任何异常，并且Student Bean的school属性会设置为null。
注意点：

required属性可以用于@Autowired注解所使用的任意地方。但是当使用构造器装配时，只有一个构造器可以将@Autowired的required属性设置true。其他使用@Autowired注解所标注的构造器只能将required属性设置为false。
3.2 多个匹配的Bean
另一个问题是可能会有足够多的（至少2个）都满足装配条件，并且都可以被装配到属性或参数中。假如，我们有两个Bean是School类型的，满足装配条件。这种情况下，@Autowired注解没有办法选择哪一个Bean才是它需要的，会抛出NoUniqueBeanDefinitionException异常。

<?xml version="1.0" encoding="UTF-8"?>
<beans xmlns="http://www.springframework.org/schema/beans"
xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
xmlns:context="http://www.springframework.org/schema/context"
xsi:schemaLocation="http://www.springframework.org/schema/beans http://www.springframework.org/schema/beans/spring-beans.xsd
http://www.springframework.org/schema/context http://www.springframework.org/schema/context/spring-context.xsd">
<context:annotation-config/>
 
<bean id = "yoona" class = "com.sjf.bean.Student">
<property name="name" value="yoona"/>
<property name="age" value="24"/>
</bean>
 
<bean id = "xidianSchool" class = "com.sjf.bean.School">
<property name="name" value="西安电子科技大学"/>
<property name="location" value="西安"/>
</bean>
 
<bean id = "shandaSchool" class = "com.sjf.bean.School">
<property name="name" value="山东大学"/>
<property name="location" value="山东"/>
</bean>
</beans>
抛出异常：
Caused by: org.springframework.beans.factory.NoUniqueBeanDefinitionException: 
No qualifying bean of type [com.sjf.bean.School] is defined: expected single matching bean but found 2: xidianSchool,shandaSchool
  at org.springframework.beans.factory.support.DefaultListableBeanFactory.doResolveDependency(DefaultListableBeanFactory.java:1126)
  at org.springframework.beans.factory.support.DefaultListableBeanFactory.resolveDependency(DefaultListableBeanFactory.java:1014)
  at org.springframework.beans.factory.annotation.AutowiredAnnotationBeanPostProcessor$AutowiredMethodElement.
inject(AutowiredAnnotationBeanPostProcessor.java:618)
  ... 15 more
为了帮助@Autowired鉴别出哪一个Bean才是我们所需要的，我们可以配合使用Spring的@Qualifier注解。

@Autowired
@Qualifier("shandaSchool")
public void setSchool(School school) {
this.school = school;
}
这样，我们就使用@Qualifier注解尝试注入ID为"shandaSchool"的Bean。表面上看，把@Autowired的byType自动装配转换为显示的byName装配。实际只是使用@Qualifier注解缩小了自动装配挑选候选Bean的范围。上例中通过指定Bean 的ID把选择范围缩小到只剩一个Bean。
除了通过Bean的ID缩小选择范围，还可以通过在Bean上直接使用qualifier来缩小范围。

<?xml version="1.0" encoding="UTF-8"?>
<beans xmlns="http://www.springframework.org/schema/beans"
xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
xmlns:context="http://www.springframework.org/schema/context"
xsi:schemaLocation="http://www.springframework.org/schema/beans http://www.springframework.org/schema/beans/spring-beans.xsd
http://www.springframework.org/schema/context http://www.springframework.org/schema/context/spring-context.xsd">
<context:annotation-config/>
 
<bean id = "yoona" class = "com.sjf.bean.Student">
<property name="name" value="yoona"/>
<property name="age" value="24"/>
</bean>
 
<bean id = "xidianSchool" class = "com.sjf.bean.School">
<property name="name" value="西安电子科技大学"/>
<property name="location" value="西安"/>
<qualifier value="ShanXi"/>
</bean>
 
<bean id = "shandaSchool" class = "com.sjf.bean.School">
<property name="name" value="山东大学"/>
<property name="location" value="山东"/>
<qualifier value="ShanDong"/>
</bean>
</beans>
这里，限定shandongSchool Bean是山东地区的大学，xidianSchool Bean是陕西地区的大学。

@Autowired
@Qualifier("ShanXi")
public void setSchool(School school) {
this.school = school;
}
运行结果：

name：yoona   age：24   school：西安电子科技大学[西安]
这里通过指定@Qualifier属性为"ShanXi"，把选择范围缩小到只剩一个Bean（xidianSchool）。
4. 在注解注入中使用表达式
既然可以使用注解为Spring的Bean自动装配其他Bean的引用，我们同样希望能够使用注解装配简单的值。Spring3.0 引入了@Value，它是一个新的装配注解。可以让我们使用注解装配String类型的值和基本类型的值，例如int，boolean。可以通过@Value直接标注某个属性，方法或者方法参数，并传入一个String类型的表达式来装配属性。

@Value("yoona")
private String name;
在这里，我们为String类型的属性装配了一个String类型的值。但是传入@Value的String类型的参数只是一个表达式，它的计算结果可以是任意类型，因此@Value能够标注任意类型的属性。
实际上，装配简单值，不是@Value的主要作用，它可以借助SEL表达式，作用更加突出。我们知道运行期可以通过SpEL动态计算复杂表达式的值并把结果装配到Bean的属性中。这一特性也使得@Value注解成为强大的装配可选方案。

@Value("#{systemProperties.myFavoriteSong}")
private String song;
在这个例子中，我们使用SpEL从系统属性中获取一个值。
参考：《Spring实战》


​
