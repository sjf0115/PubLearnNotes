## 1. 问题

启动 SeaTunnel Web 运行同步任务时出现如下异常：
```java
2026-05-16 13:00:25.532 seatunnel smarsi INFO [qtp1371045367-23] [AbstractLogger.info():69] - Client statistics is enabled with period 5 seconds.
2026-05-16 13:00:25.548 seatunnel smarsi INFO [qtp1371045367-23] [ConfigBuilder.of():88] - Loading config file from path: /opt/workspace/apache-seatunnel-web-1.0.2-bin/profile/21343715957248.conf
2026-05-16 13:00:25.550 seatunnel smarsi ERROR [qtp1371045367-23] [JobExecutorServiceImpl.executeJobBySeaTunnel():128] - Job execution submission failed.
java.lang.ClassCastException: java.util.LinkedHashMap cannot be cast to java.util.ArrayList
	at org.apache.seatunnel.core.starter.utils.ConfigShadeUtils.processConfig(ConfigShadeUtils.java:143)
	at org.apache.seatunnel.core.starter.utils.ConfigShadeUtils.decryptConfig(ConfigShadeUtils.java:119)
	at org.apache.seatunnel.core.starter.utils.ConfigShadeUtils.decryptConfig(ConfigShadeUtils.java:104)
	at org.apache.seatunnel.core.starter.utils.ConfigBuilder.ofInner(ConfigBuilder.java:70)
	at org.apache.seatunnel.core.starter.utils.ConfigBuilder.lambda$of$1(ConfigBuilder.java:93)
	at java.util.Optional.orElseGet(Optional.java:267)
	at org.apache.seatunnel.core.starter.utils.ConfigBuilder.of(ConfigBuilder.java:93)
	at org.apache.seatunnel.engine.core.parse.MultipleTableJobConfigParser.<init>(MultipleTableJobConfigParser.java:151)
	at org.apache.seatunnel.engine.client.job.ClientJobExecutionEnvironment.getJobConfigParser(ClientJobExecutionEnvironment.java:102)
	at org.apache.seatunnel.engine.client.job.ClientJobExecutionEnvironment.getLogicalDag(ClientJobExecutionEnvironment.java:114)
	at org.apache.seatunnel.engine.client.job.ClientJobExecutionEnvironment.execute(ClientJobExecutionEnvironment.java:182)
	at org.apache.seatunnel.app.service.impl.JobExecutorServiceImpl.executeJobBySeaTunnel(JobExecutorServiceImpl.java:126)
	at org.apache.seatunnel.app.service.impl.JobExecutorServiceImpl.jobExecute(JobExecutorServiceImpl.java:79)
	at org.apache.seatunnel.app.controller.JobExecutorController.jobExecutor(JobExecutorController.java:64)
	at sun.reflect.NativeMethodAccessorImpl.invoke0(Native Method)
	at sun.reflect.NativeMethodAccessorImpl.invoke(NativeMethodAccessorImpl.java:62)
	at sun.reflect.DelegatingMethodAccessorImpl.invoke(DelegatingMethodAccessorImpl.java:43)
	at java.lang.reflect.Method.invoke(Method.java:498)
	at org.springframework.web.method.support.InvocableHandlerMethod.doInvoke(InvocableHandlerMethod.java:205)
	at org.springframework.web.method.support.InvocableHandlerMethod.invokeForRequest(InvocableHandlerMethod.java:150)
	at org.springframework.web.servlet.mvc.method.annotation.ServletInvocableHandlerMethod.invokeAndHandle(ServletInvocableHandlerMethod.java:117)
	at org.springframework.web.servlet.mvc.method.annotation.RequestMappingHandlerAdapter.invokeHandlerMethod(RequestMappingHandlerAdapter.java:895)
	at org.springframework.web.servlet.mvc.method.annotation.RequestMappingHandlerAdapter.handleInternal(RequestMappingHandlerAdapter.java:808)
	at org.springframework.web.servlet.mvc.method.AbstractHandlerMethodAdapter.handle(AbstractHandlerMethodAdapter.java:87)
	at org.springframework.web.servlet.DispatcherServlet.doDispatch(DispatcherServlet.java:1067)
	at org.springframework.web.servlet.DispatcherServlet.doService(DispatcherServlet.java:963)
	at org.springframework.web.servlet.FrameworkServlet.processRequest(FrameworkServlet.java:1006)
	at org.springframework.web.servlet.FrameworkServlet.doPost(FrameworkServlet.java:909)
	at javax.servlet.http.HttpServlet.service(HttpServlet.java:517)
	at org.springframework.web.servlet.FrameworkServlet.service(FrameworkServlet.java:883)
	at javax.servlet.http.HttpServlet.service(HttpServlet.java:584)
	at org.eclipse.jetty.servlet.ServletHolder.handle(ServletHolder.java:799)
	at org.eclipse.jetty.servlet.ServletHandler$ChainEnd.doFilter(ServletHandler.java:1631)
	at org.springframework.web.filter.RequestContextFilter.doFilterInternal(RequestContextFilter.java:100)
	at org.springframework.web.filter.OncePerRequestFilter.doFilter(OncePerRequestFilter.java:117)
	at org.eclipse.jetty.servlet.FilterHolder.doFilter(FilterHolder.java:193)
	at org.eclipse.jetty.servlet.ServletHandler$Chain.doFilter(ServletHandler.java:1601)
	at org.springframework.web.filter.FormContentFilter.doFilterInternal(FormContentFilter.java:93)
	at org.springframework.web.filter.OncePerRequestFilter.doFilter(OncePerRequestFilter.java:117)
	at org.eclipse.jetty.servlet.FilterHolder.doFilter(FilterHolder.java:193)
	at org.eclipse.jetty.servlet.ServletHandler$Chain.doFilter(ServletHandler.java:1601)
	at org.springframework.web.filter.CharacterEncodingFilter.doFilterInternal(CharacterEncodingFilter.java:201)
	at org.springframework.web.filter.OncePerRequestFilter.doFilter(OncePerRequestFilter.java:117)
	at org.eclipse.jetty.servlet.FilterHolder.doFilter(FilterHolder.java:193)
	at org.eclipse.jetty.servlet.ServletHandler$Chain.doFilter(ServletHandler.java:1601)
	at org.eclipse.jetty.servlet.ServletHandler.doHandle(ServletHandler.java:548)
	at org.eclipse.jetty.server.handler.ScopedHandler.handle(ScopedHandler.java:143)
	at org.eclipse.jetty.security.SecurityHandler.handle(SecurityHandler.java:600)
	at org.eclipse.jetty.server.handler.HandlerWrapper.handle(HandlerWrapper.java:127)
	at org.eclipse.jetty.server.handler.ScopedHandler.nextHandle(ScopedHandler.java:235)
	at org.eclipse.jetty.server.session.SessionHandler.doHandle(SessionHandler.java:1624)
	at org.eclipse.jetty.server.handler.ScopedHandler.nextHandle(ScopedHandler.java:233)
	at org.eclipse.jetty.server.handler.ContextHandler.doHandle(ContextHandler.java:1440)
	at org.eclipse.jetty.server.handler.ScopedHandler.nextScope(ScopedHandler.java:188)
	at org.eclipse.jetty.servlet.ServletHandler.doScope(ServletHandler.java:501)
	at org.eclipse.jetty.server.session.SessionHandler.doScope(SessionHandler.java:1594)
	at org.eclipse.jetty.server.handler.ScopedHandler.nextScope(ScopedHandler.java:186)
	at org.eclipse.jetty.server.handler.ContextHandler.doScope(ContextHandler.java:1355)
	at org.eclipse.jetty.server.handler.ScopedHandler.handle(ScopedHandler.java:141)
	at org.eclipse.jetty.server.handler.HandlerWrapper.handle(HandlerWrapper.java:127)
	at org.eclipse.jetty.server.Server.handle(Server.java:516)
	at org.eclipse.jetty.server.HttpChannel.lambda$handle$1(HttpChannel.java:487)
	at org.eclipse.jetty.server.HttpChannel.dispatch(HttpChannel.java:732)
	at org.eclipse.jetty.server.HttpChannel.handle(HttpChannel.java:479)
	at org.eclipse.jetty.server.HttpConnection.onFillable(HttpConnection.java:277)
	at org.eclipse.jetty.io.AbstractConnection$ReadCallback.succeeded(AbstractConnection.java:311)
	at org.eclipse.jetty.io.FillInterest.fillable(FillInterest.java:105)
	at org.eclipse.jetty.io.ChannelEndPoint$1.run(ChannelEndPoint.java:104)
	at org.eclipse.jetty.util.thread.strategy.EatWhatYouKill.runTask(EatWhatYouKill.java:338)
	at org.eclipse.jetty.util.thread.strategy.EatWhatYouKill.doProduce(EatWhatYouKill.java:315)
	at org.eclipse.jetty.util.thread.strategy.EatWhatYouKill.tryProduce(EatWhatYouKill.java:173)
	at org.eclipse.jetty.util.thread.strategy.EatWhatYouKill.run(EatWhatYouKill.java:131)
	at org.eclipse.jetty.util.thread.ReservedThreadExecutor$ReservedThread.run(ReservedThreadExecutor.java:409)
	at org.eclipse.jetty.util.thread.QueuedThreadPool.runJob(QueuedThreadPool.java:883)
	at org.eclipse.jetty.util.thread.QueuedThreadPool$Runner.run(QueuedThreadPool.java:1034)
	at java.lang.Thread.run(Thread.java:750)
```
从上面代码可以看到核心错误：
```
java.lang.ClassCastException: java.util.LinkedHashMap cannot be cast to java.util.ArrayList
    at ConfigShadeUtils.processConfig(ConfigShadeUtils.java:143)
```

**根因**：SeaTunnel Web 1.0.2 的 `ConfigShadeUtils.processConfig` 在处理配置加解密时，期望 `source`/`sink`/`transform` 配置节是 **List（数组）格式**，但生成的配置文件使用的是 **Map（对象）格式**。

## 2. 问题原因

SeaTunnel Web 1.0.2 的 `ConfigShadeUtils` 期望 `source`、`transform`、`sink` 是 **数组格式**，但当前生成的配置使用的是 **对象格式**：

**当前格式（错误 - Map 格式）：**
```hocon
source {
  Jdbc {
    url = "..."
  }
}
```

**正确格式（List 格式）：**
```hocon
source [
  {
    plugin_name = "Jdbc"
    url = "..."
  }
]
```

## 3. 解决方案

需要修改 SeaTunnel Web 生成配置文件的逻辑，将 `source`/`sink`/`transform` 从 Map 格式改为 List 格式。这是 SeaTunnel Web 1.0.2 与 SeaTunnel Engine 2.3.8 的兼容性问题。SeaTunnel Web 1.0.2 的版本较旧，升级到更高版本（如 1.0.3+）已修复此兼容性问题。

---

**根本原因总结**：SeaTunnel Web 在 `ConfigShadeUtils.processConfig` 中遍历 source/sink/transform 节点时，使用强制类型转换 `(ArrayList)` 获取配置列表，但 HOCON 解析器将 `source { Jdbc {...} }` 解析为 `LinkedHashMap`，导致 ClassCastException。需要使用数组语法 `source [...]` 来生成配置。
