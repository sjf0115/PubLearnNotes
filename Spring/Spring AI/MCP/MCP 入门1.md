# 模型上下文协议(MCP)入门指南
==================================================

模型上下文协议(MCP)标准化了AI应用程序与外部工具及资源的交互方式。

Spring作为核心贡献者早期加入了MCP生态，参与开发和维护了作为Java版MCP实现基础的[官方MCP Java SDK](https://github.com/modelcontextprotocol/java-sdk)。基于此贡献，Spring AI通过Boot启动器和注解提供MCP支持，使得构建MCP服务端和客户端变得异常简单。

## 介绍视频
---------------------------------------------------------------------------------------------------------------------
**[模型上下文协议(MCP)简介 - YouTube](https://www.youtube.com/watch?v=FLpS7OfD5-s)**

本视频提供MCP的入门概述，讲解核心概念与架构设计。

## 完整教程与源码
---------------------------------------------------------------------------------------------------------------------------------------------------
**📖 博客教程：**[连接你的AI到万物](https://spring.io/blog/2025/09/16/spring-ai-mcp-intro-blog)  
**💻 完整源码：**[MCP天气示例仓库](https://github.com/tzolov/spring-ai-mcp-blogpost)

本教程涵盖Spring AI开发MCP的核心要点，包括高级功能和部署模式。以下所有代码示例均出自该教程。

## 快速入门
-------------------------------------------------------------------------------------------------------
最快捷的方式是使用Spring AI基于注解的方案。以下示例来自博客教程：

### 简单MCP服务端
```java
@Service
public class WeatherService {

    @McpTool(description = "获取某地当前温度")
    public String getTemperature(
            @McpToolParam(description = "城市名称", required = true) String city) {
        return String.format("%s当前温度：22°C", city);
    }
}
