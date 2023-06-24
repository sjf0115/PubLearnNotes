## 1. 依赖

导入 SpringMVC 和 Servlet 坐标：
```xml
<!--  Spring MVC -->
<dependency>
    <groupId>org.springframework</groupId>
    <artifactId>spring-webmvc</artifactId>
    <version>6.0.3</version>
</dependency>

<!-- Servlet -->
<dependency>
    <groupId>jakarta.servlet</groupId>
    <artifactId>jakarta.servlet-api</artifactId>
    <version>6.0.0</version>
    <scope>provided</scope>
</dependency>
```

## 2. 初始化 SpringMVC 环境

```java
@Configuration
@ComponentScan("com.spring.example.controller")
public class SpringMvcConfig {

}
```

## 3. 创建 SpringMVC 控制器类

```java
@Controller
public class HelloController {
    @RequestMapping("/hello")
    @ResponseBody
    public String hello() {
        return "{\"data\": \"Hello SpringMVC!\"}";
    }
}
```

## 4. 初始化 Servlet 容器的配置

初始化 Servlet 容器，加载 SpringMVC 环境，并设置 SpringMVC 请求拦截的路径：
```java
public class ServletContainerInitConfig extends AbstractDispatcherServletInitializer {
    @Override
    protected WebApplicationContext createServletApplicationContext() {
        AnnotationConfigWebApplicationContext ctx = new AnnotationConfigWebApplicationContext();
        ctx.register(SpringMvcConfig.class);
        return ctx;
    }

    @Override
    protected String[] getServletMappings() {
        return new String[]{"/"};
    }

    @Override
    protected WebApplicationContext createRootApplicationContext() {
        return null;
    }
}
```

## 5. 使用浏览器测试
