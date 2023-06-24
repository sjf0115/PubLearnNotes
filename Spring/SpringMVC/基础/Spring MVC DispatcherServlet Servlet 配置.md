使用 Servlet 时，我们可以选择以编程方式来配置 Servlet 容器，来代替或与 web.xml 文件结合使用。下面的例子注册了一个 DispatcherServlet:

```java
public class MyWebApplicationInitializer implements WebApplicationInitializer {
	@Override
	public void onStartup(ServletContext container) {
		XmlWebApplicationContext appContext = new XmlWebApplicationContext();
		appContext.setConfigLocation("/WEB-INF/spring/dispatcher-config.xml");

		ServletRegistration.Dynamic registration = container.addServlet("dispatcher", new DispatcherServlet(appContext));
		registration.setLoadOnStartup(1);
		registration.addMapping("/");
	}
}
```
WebApplicationInitializer 是 Spring MVC 提供的一个接口，可以确保我们的实现可以被检测到，并自动初始化 Servlet 3 容器。一个名为 AbstractDispatcherServletInitializer 的 WebApplicationInitializer 的抽象基类实现使得注册 DispatcherServlet 变得更加容易，通过重写方法来指定 servlet 映射和 DispatcherServlet 配置的位置：
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

对于使用基于 Java 的 Spring 配置的应用程序，建议这样做，如下例所示:
```java
public class MyWebAppInitializer extends AbstractAnnotationConfigDispatcherServletInitializer {

	@Override
	protected Class<?>[] getRootConfigClasses() {
		return null;
	}

	@Override
	protected Class<?>[] getServletConfigClasses() {
		return new Class<?>[] { MyWebConfig.class };
	}

	@Override
	protected String[] getServletMappings() {
		return new String[] { "/" };
	}
}
```
如果您使用基于 xml 的 Spring 配置，您应该直接从 AbstractDispatcherServletInitializer 扩展，如下面的示例所示:
```java
public class MyWebAppInitializer extends AbstractDispatcherServletInitializer {

	@Override
	protected WebApplicationContext createRootApplicationContext() {
		return null;
	}

	@Override
	protected WebApplicationContext createServletApplicationContext() {
		XmlWebApplicationContext cxt = new XmlWebApplicationContext();
		cxt.setConfigLocation("/WEB-INF/spring/dispatcher-config.xml");
		return cxt;
	}

	@Override
	protected String[] getServletMappings() {
		return new String[] { "/" };
	}
}
```
AbstractDispatcherServletInitializer 还提供了一种方便的方法来添加 Filter 实例，并将它们自动映射到 DispatcherServlet，如下面的示例所示:
```java
public class MyWebAppInitializer extends AbstractDispatcherServletInitializer {

	// ...

	@Override
	protected Filter[] getServletFilters() {
		return new Filter[] {
			new HiddenHttpMethodFilter(), new CharacterEncodingFilter() };
	}
}
```


> 原文:[Servlet Config](https://docs.spring.io/spring-framework/reference/web/webmvc/mvc-servlet/container-config.html)
