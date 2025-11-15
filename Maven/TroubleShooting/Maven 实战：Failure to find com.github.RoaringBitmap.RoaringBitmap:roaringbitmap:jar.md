
## 1. 问题

pom 文件中配置如下：
```xml
<roaringbitmap.version>1.5.3</roaringbitmap.version>

<dependency>
<groupId>com.github.RoaringBitmap.RoaringBitmap</groupId>
<artifactId>roaringbitmap</artifactId>
<version>${roaringbitmap.version}</version>
</dependency>
```
但是打包发现如下异常：
```java
Failure to find com.github.RoaringBitmap.RoaringBitmap:roaringbitmap:jar:1.5.3 in https://maven.aliyun.com/nexus/content/groups/public was cached in the local repository, resolution will not be reattempted until the update interval of mirror has elapsed or updates are forced
```

## 2. 分析

根据错误信息，问题在于 Maven 没有从 JitPack 仓库下载依赖，而是尝试从阿里云镜像（配置为 mirror）下载，但阿里云镜像中没有这个依赖。错误信息 `Failure to find ... in https://maven.aliyun.com/... was cached in local repository` 表明：
- Maven 首先尝试从阿里云镜像（https://maven.aliyun.com/nexus/content/groups/public）下载依赖
- 阿里云镜像中没有 com.github.RoaringBitmap.RoaringBitmap:roaringbitmap:jar:1.5.3
- 这个失败结果被缓存到本地仓库，在更新间隔到期或强制更新之前不会重试

---

问题核心原因：
- Maven 配置中可能将阿里云镜像设置为了全局镜像（mirrorOf 设置为 * 或包含 central），覆盖了所有仓库请求，包括对 JitPack 的请求。
- 所有仓库请求（包括 JitPack）都被重定向到阿里云
- 由于阿里云镜像没有 RoaringBitmap 的依赖，因此下载失败。

## 3. 解决方案

根据错误日志，问题核心在于 Maven 镜像配置覆盖了 JitPack 仓库，导致始终从阿里云镜像（不包含 RoaringBitmap）拉取依赖。以下是完整解决方案。

### 3.1 JitPack 仓库配置

确保添加了第三方仓库以访问 RoaringBitmap：
```xml
<repositories>
    <repository>
        <id>jitpack.io</id>
        <url>https://jitpack.io</url>
    </repository>
</repositories>
```

### 3.2 修改镜像配置（settings.xml）

需要调整 Maven 的镜像配置（在 settings.xml 中），使 JitPack 仓库的请求不被镜像到阿里云。定位 `settings.xml` 配置文件调整镜像策略：
```xml
<mirrors>
    <!-- 保留阿里云镜像，但排除 JitPack -->
    <mirror>
        <id>aliyun</id>
        <name>Aliyun Maven Mirror</name>
        <url>https://maven.aliyun.com/nexus/content/groups/public</url>
        <!-- 关键修改：!jitpack.io 表示排除 -->
        <mirrorOf>*,!jitpack.io</mirrorOf>
    </mirror>
</mirrors>
```

> `!jitpack.io` 将 JitPack 仓库从镜像覆盖中排除，使其直连
