## 1. 依赖

导入 SpringMVC 和 Servlet 坐标：
```xml
<!--  Spring MVC -->
<dependency>
    <groupId>org.springframework</groupId>
    <artifactId>spring-webmvc</artifactId>
    <version>5.2.10.RELEASE</version>
</dependency>

<!-- Servlet -->
<dependency>
    <groupId>javax.servlet</groupId>
    <artifactId>javax.servlet-api</artifactId>
    <version>3.1.0</version>
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
## 5. 配置 Tomcat

你可以选择使用 Tomcat 插件(`tomcat7-maven-plugin`)来代替安装本地 Tomcat:
```xml
<build>
    <plugins>
        <!-- Tomcat7 插件-->
        <plugin>
            <groupId>org.apache.tomcat.maven</groupId>
            <artifactId>tomcat7-maven-plugin</artifactId>
            <version>2.2</version>
            <!-- 插件配置 -->
            <configuration>
                <port>8070</port>
                <path>/</path>
                <uriEncoding>UTF-8</uriEncoding>
            </configuration>
        </plugin>
    </plugins>
</build>
```



## 5. 使用浏览器测试

在浏览器中打开 `http://localhost:8070/hello`，出现如下内容：
```json
{"data": "Hello SpringMVC!"}
```
