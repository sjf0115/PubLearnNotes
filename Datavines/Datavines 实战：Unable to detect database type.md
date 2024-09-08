## 1. 问题

第一次启动 Datavines 时出现如下异常：
```java
Caused by: org.springframework.beans.factory.BeanCreationException: Error creating bean with name 'quartzDataSourceScriptDatabaseInitializer' defined in class path resource [org/springframework/boot/autoconfigure/quartz/QuartzAutoConfiguration$JdbcStoreTypeConfiguration.class]: Bean instantiation via factory method failed; nested exception is org.springframework.beans.BeanInstantiationException: Failed to instantiate [org.springframework.boot.autoconfigure.quartz.QuartzDataSourceScriptDatabaseInitializer]: Factory method 'quartzDataSourceScriptDatabaseInitializer' threw exception; nested exception is java.lang.IllegalStateException: Unable to detect database type
        at org.springframework.beans.factory.support.ConstructorResolver.instantiate(ConstructorResolver.java:658)
        at org.springframework.beans.factory.support.ConstructorResolver.instantiateUsingFactoryMethod(ConstructorResolver.java:638)
        at org.springframework.beans.factory.support.AbstractAutowireCapableBeanFactory.instantiateUsingFactoryMethod(AbstractAutowireCapableBeanFactory.java:1352)
        at org.springframework.beans.factory.support.AbstractAutowireCapableBeanFactory.createBeanInstance(AbstractAutowireCapableBeanFactory.java:1195)
        at org.springframework.beans.factory.support.AbstractAutowireCapableBeanFactory.doCreateBean(AbstractAutowireCapableBeanFactory.java:582)
        at org.springframework.beans.factory.support.AbstractAutowireCapableBeanFactory.createBean(AbstractAutowireCapableBeanFactory.java:542)
        at org.springframework.beans.factory.support.AbstractBeanFactory.lambda$doGetBean$0(AbstractBeanFactory.java:335)
        at org.springframework.beans.factory.support.DefaultSingletonBeanRegistry.getSingleton(DefaultSingletonBeanRegistry.java:234)
        at org.springframework.beans.factory.support.AbstractBeanFactory.doGetBean(AbstractBeanFactory.java:333)
        at org.springframework.beans.factory.support.AbstractBeanFactory.getBean(AbstractBeanFactory.java:208)
        at org.springframework.beans.factory.support.AbstractBeanFactory.doGetBean(AbstractBeanFactory.java:322)
        at org.springframework.beans.factory.support.AbstractBeanFactory.getBean(AbstractBeanFactory.java:208)
        at org.springframework.beans.factory.config.DependencyDescriptor.resolveCandidate(DependencyDescriptor.java:276)
        at org.springframework.beans.factory.support.DefaultListableBeanFactory.doResolveDependency(DefaultListableBeanFactory.java:1380)
        at org.springframework.beans.factory.support.DefaultListableBeanFactory.resolveDependency(DefaultListableBeanFactory.java:1300)
        at org.springframework.beans.factory.annotation.AutowiredAnnotationBeanPostProcessor$AutowiredFieldElement.resolveFieldValue(AutowiredAnnotationBeanPostProcessor.java:656)
        ... 142 more
Caused by: org.springframework.beans.BeanInstantiationException: Failed to instantiate [org.springframework.boot.autoconfigure.quartz.QuartzDataSourceScriptDatabaseInitializer]: Factory method 'quartzDataSourceScriptDatabaseInitializer' threw exception; nested exception is java.lang.IllegalStateException: Unable to detect database type
        at org.springframework.beans.factory.support.SimpleInstantiationStrategy.instantiate(SimpleInstantiationStrategy.java:185)
        at org.springframework.beans.factory.support.ConstructorResolver.instantiate(ConstructorResolver.java:653)
        ... 157 more
Caused by: java.lang.IllegalStateException: Unable to detect database type
        at org.springframework.util.Assert.state(Assert.java:76)
        at org.springframework.boot.jdbc.init.PlatformPlaceholderDatabaseDriverResolver.determinePlatform(PlatformPlaceholderDatabaseDriverResolver.java:114)
        at org.springframework.boot.jdbc.init.PlatformPlaceholderDatabaseDriverResolver.resolveAll(PlatformPlaceholderDatabaseDriverResolver.java:103)
        at org.springframework.boot.autoconfigure.quartz.QuartzDataSourceScriptDatabaseInitializer.getSettings(QuartzDataSourceScriptDatabaseInitializer.java:75)
        at org.springframework.boot.autoconfigure.quartz.QuartzDataSourceScriptDatabaseInitializer.<init>(QuartzDataSourceScriptDatabaseInitializer.java:44)
        at org.springframework.boot.autoconfigure.quartz.QuartzAutoConfiguration$JdbcStoreTypeConfiguration.quartzDataSourceScriptDatabaseInitializer(QuartzAutoConfiguration.java:141)
        at sun.reflect.NativeMethodAccessorImpl.invoke0(Native Method)
        at sun.reflect.NativeMethodAccessorImpl.invoke(NativeMethodAccessorImpl.java:62)
        at sun.reflect.DelegatingMethodAccessorImpl.invoke(DelegatingMethodAccessorImpl.java:43)
        at java.lang.reflect.Method.invoke(Method.java:498)
        at org.springframework.beans.factory.support.SimpleInstantiationStrategy.instantiate(SimpleInstantiationStrategy.java:154)
        ... 158 more
```

## 2. 解决方案

经排查发现 application.yml 中 mysql 的账号密码配置有问题：
```yaml
spring:
  config:
    activate:
      on-profile: mysql
  datasource:
    #driver-class-name: com.mysql.cj.jdbc.Driver
    driver-class-name: com.mysql.jdbc.Driver
    url: jdbc:mysql://127.0.0.1:3306/datavines?useUnicode=true&characterEncoding=UTF-8&useSSL=false&serverTimezone=Asia/Shanghai
    username: root
    password: 123456
  quartz:
    properties:
      org.quartz.jobStore.driverDelegateClass: org.quartz.impl.jdbcjobstore.StdJDBCDelegate
```
