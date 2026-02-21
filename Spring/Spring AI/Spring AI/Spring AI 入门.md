https://docs.spring.io/spring-ai/reference/getting-started.html#dependency-management

> Spring AI：1.1.2

本节提供使用 Spring AI 的快速入门指引。

> Spring AI 支持 Spring Boot 3.4.x 和 3.5.x 版本

## 1. Spring Initializr


请访问 [start.spring.io](https://start.spring.io/)，在新应用中选择您需要使用的 AI 模型和向量存储组件。

---

## 2. 构件仓库

### 2.1 正式版 - 使用 Maven Central

Spring AI 1.0.0 及后续版本已在 Maven Central 仓库提供。构建文件只需启用 Maven Central 即可，通常无需额外配置仓库:
```xml
<!-- Maven 构建默认包含 Maven Central -->
<repositories>
    <repository>
        <id>central</id>
        <url>https://repo.maven.apache.org/maven2</url>
    </repository>
</repositories>
```

### 2.2 快照版 - 添加快照仓库

如需使用开发版本（如 `1.1.0-SNAPSHOT`）或 `1.0.0` 之前的里程碑版本，需在构建文件中添加以下快照仓库:
```xml
<repositories>
  <repository>
    <id>spring-snapshots</id>
    <name>Spring Snapshots</name>
    <url>https://repo.spring.io/snapshot</url>
    <releases>
      <enabled>false</enabled>
    </releases>
  </repository>

  <repository>
    <name>Central Portal Snapshots</name>
    <id>central-portal-snapshots</id>
    <url>https://central.sonatype.com/repository/maven-snapshots/</url>
    <releases>
      <enabled>false</enabled>
    </releases>
    <snapshots>
      <enabled>true</enabled>
    </snapshots>
  </repository>

</repositories>
```

需要注意的是使用 Maven 构建 Spring AI 快照时，请检查镜像配置。若在 settings.xml 中配置了如下镜像：
```xml
<mirror>
    <id>my-mirror</id>
    <mirrorOf>*</mirrorOf>
    <url>https://my-company-repository.com/maven</url>
</mirror>
```
通配符 `*` 会将所有仓库请求重定向至镜像，导致无法访问 Spring 快照仓库。请修改 mirrorOf 配置排除 Spring 仓库：
```xml
<mirror>
    <id>my-mirror</id>
    <mirrorOf>*,!spring-snapshots,!central-portal-snapshots</mirrorOf>
    <url>https://my-company-repository.com/maven</url>
</mirror>
```
此配置允许 Maven 直接访问 Spring 快照仓库，同时通过镜像获取其他依赖。

## 3. 依赖管理

Spring AI BOM 声明了 Spring AI 指定版本所有依赖的推荐版本。此 BOM 仅包含依赖管理，不涉及插件声明或 Spring/Spring Boot 直接引用。可使用 Spring Boot 父 POM 或 Spring Boot BOM (spring-boot-dependencies) 管理 Spring Boot 版本。添加 BOM 至项目：
```xml
<dependencyManagement>
    <dependencies>
        <dependency>
            <groupId>org.springframework.ai</groupId>
            <artifactId>spring-ai-bom</artifactId>
            <version>1.0.0</version>
            <type>pom</type>
            <scope>import</scope>
        </dependency>
    </dependencies>
</dependencyManagement>
```

## 4. 添加组件依赖

文档后续各章节会说明需添加的具体依赖：
- [对话模型](https://docs.spring.io/spring-ai/reference/api/chatmodel.html)
- [嵌入模型](https://docs.spring.io/spring-ai/reference/api/embeddings.html)
- [图像生成模型](https://docs.spring.io/spring-ai/reference/api/imageclient.html)
- [语音转录模型](https://docs.spring.io/spring-ai/reference/api/audio/transcriptions.html)
- [文本转语音 (TTS) 模型](https://docs.spring.io/spring-ai/reference/api/audio/speech.html)
- [向量数据库](https://docs.spring.io/spring-ai/reference/api/vectordbs.html)

## 5. Spring AI 示例

请访问 [此页面](https://github.com/spring-ai-community/awesome-spring-ai) 获取更多 Spring AI 相关资源和示例。


> [Getting Started](https://docs.spring.io/spring-ai/reference/getting-started.html#dependency-management)
