`<context:annotation-config>`：声明支持一般注释，例如@Required，@Autowired，@PostConstruct等。

`<mvc:annotation-driven/>`：其实是没有意义的。它声明显式支持注释驱动的MVC控制器（即@RequestMapping，@Controller等），尽管它们是默认的行为。

我的建议是始终声明`<context：annotation-config>`，但是除非您需要通过Jackson支持JSON，否则不要使用`<mvc：annotation-driven />`。

当我们需要controller返回一个map的json对象时，可以设定`<mvc:annotation-driven />`，同时设定`<mvc:message-converters>`标签，设定字符集和json处理类，例如：

```
<mvc:annotation-driven>
    <mvc:message-converters>
        <bean class="org.springframework.http.converter.StringHttpMessageConverter">
            <property name="supportedMediaTypes">
                <list>
                    <value>text/plain;charset=UTF-8</value>
                </list>
            </property>
        </bean>
    </mvc:message-converters>
</mvc:annotation-driven>
```

### 1. mvc:annotation-driven

This tag registers the DefaultAnnotationHandlerMapping and AnnotationMethodHandlerAdapter beans that are required for Spring MVC to dispatch requests to @Controllers. The tag configures those two beans with sensible defaults based on what is present in your classpath. The defaults are:

- Support for Spring 3's Type ConversionService in addition to JavaBeans PropertyEditors during Data Binding. A ConversionService instance produced by the org.springframework.format.support.FormattingConversionServiceFactoryBean is used by default. This can be overriden by setting the conversion-service attribute.

- Support for formatting Number fields using the @NumberFormat annotation

- Support for formatting Date, Calendar, Long, and Joda Time fields using the @DateTimeFormat annotation, if Joda Time 1.3 or higher is present on the classpath.

- Support for validating @Controller inputs with @Valid, if a JSR-303 Provider is present on the classpath. The validation system can be explicitly configured by setting the validator attribute.

- Support for reading and writing XML, if JAXB is present on the classpath.

- Support for reading and writing JSON, if Jackson is present on the classpath.

A typical usage is shown below:

```
<?xml version="1.0" encoding="UTF-8"?>
<beans xmlns="http://www.springframework.org/schema/beans"
    xmlns:mvc="http://www.springframework.org/schema/mvc"
    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
    xsi:schemaLocation="
        http://www.springframework.org/schema/beans 
        http://www.springframework.org/schema/beans/spring-beans-3.0.xsd
        http://www.springframework.org/schema/mvc
        http://www.springframework.org/schema/mvc/spring-mvc-3.0.xsd">

    <!-- JSR-303 support will be detected on classpath and enabled automatically -->
    <mvc:annotation-driven/>
    
</beans>
```




资料：http://docs.spring.io/spring/docs/3.0.x/spring-framework-reference/html/mvc.html#mvc-config

https://docs.spring.io/spring/docs/current/spring-framework-reference/html/mvc.html

